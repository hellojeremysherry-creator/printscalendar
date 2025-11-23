import calendar
from datetime import date
from django.urls import reverse_lazy
from django.views import generic
from django.utils import timezone
from .models import SaleEvent
from .forms import SaleEventForm
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

def scrape_auction(request):
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "Missing URL"}, status=400)

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0.0.0 Safari/537.36"
            ),
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        try:
            resp.raise_for_status()
        except HTTPError:
            if resp.status_code == 403:
                return JsonResponse({
                    "error": "The auction site returned 403 Forbidden. They may be blocking automated requests."
                }, status=502)
            return JsonResponse({
                "error": f"HTTP error from auction site: {resp.status_code}"
            }, status=502)

        soup = BeautifulSoup(resp.text, "html.parser")

        # Default values
        title = ""
        auction_house = ""
        location = ""
        start_date_iso = ""

        if "invaluable.com" in url:
            # ====== SPECIAL CASE: Invaluable ======
            # These selectors are examples – tweak them after inspecting the actual HTML.
            h1 = soup.select_one("h1")  # or more specific selector
            if h1:
                title = h1.get_text(strip=True)

            house_el = soup.find("a", class_="auction-house-name") or soup.find("a", attrs={"data-auction-house": True})
            if house_el:
                auction_house = house_el.get_text(strip=True)

            # Maybe date/time in a specific span/div:
            datetime_el = soup.find("time") or soup.find("span", class_="auction-date")
            if datetime_el:
                text = datetime_el.get_text(strip=True)
                # Try to parse with dateutil for flexibility
                from dateutil import parser
                try:
                    dt = parser.parse(text, fuzzy=True)
                    start_date_iso = dt.date().isoformat()
                except Exception:
                    pass

            location_el = soup.find("span", class_="auction-location")
            if location_el:
                location = location_el.get_text(strip=True)
        else:
            # ====== your existing generic logic here ======
            full_text = soup.get_text(" ", strip=True)
            # ... your regex stuff ...
            # set title, auction_house, location, start_date_iso as before
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""

        data = {
            "title": title or "",
            "auction_house": auction_house or "",
            "location": location or "",
            "start_date": start_date_iso or "",
        }
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




class MonthView(generic.TemplateView):
    template_name = 'calendarapp/month_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get month/year from query params, default to current month
        today = timezone.localdate()
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')

        if year and month:
            year = int(year)
            month = int(month)
        else:
            year = today.year
            month = today.month

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.itermonthdates(year, month)

        weeks = []
        week = []
        for d in month_days:
            day_events = (
                SaleEvent.objects.filter(
                    start_date__lte=d,
                    end_date__gte=d
                ) |
                SaleEvent.objects.filter(
                    start_date=d,
                    end_date__isnull=True
                )
            )

            week.append((d, day_events.distinct()))
            if len(week) == 7:
                weeks.append(week)
                week = []

        context['weeks'] = weeks
        context['year'] = year
        context['month'] = month
        context['month_name'] = calendar.month_name[month]

        # Prev/next month helpers
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year

        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        context['prev_year'] = prev_year
        context['prev_month'] = prev_month
        context['next_year'] = next_year
        context['next_month'] = next_month

        # NEW: extra context for UI niceties
        context['today'] = today
        context['upcoming_events'] = (
            SaleEvent.objects.filter(start_date__gte=today)
            .order_by('start_date')[:10]
        )

        return context



class DayView(generic.TemplateView):
    template_name = 'calendarapp/day_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(kwargs['year'])
        month = int(kwargs['month'])
        day = int(kwargs['day'])

        selected_date = date(year=year, month=month, day=day)
        events = (SaleEvent.objects.filter(
            start_date__lte=selected_date,
            end_date__gte=selected_date
        ) | SaleEvent.objects.filter(
            start_date=selected_date,
            end_date__isnull=True
        ))

        context['date'] = selected_date
        context['events'] = events.distinct()
        return context



class SaleEventCreateView(generic.CreateView):
    model = SaleEvent
    form_class = SaleEventForm
    template_name = "calendarapp/event_form.html"
    success_url = reverse_lazy("calendarapp:month_view")

class SaleEventUpdateView(generic.UpdateView):
    model = SaleEvent
    form_class = SaleEventForm
    template_name = "calendarapp/event_form.html"
    success_url = reverse_lazy("calendarapp:month_view")


class SaleEventDeleteView(generic.DeleteView):
    model = SaleEvent
    template_name = 'calendarapp/event_confirm_delete.html'
    success_url = reverse_lazy('calendarapp:month_view')


@csrf_exempt
@require_POST
def create_event_from_page(request):
    """
    Create a SaleEvent from JSON posted by a bookmarklet running in the browser
    on the auction site page.
    Expected JSON:
      {
        "url": "...",
        "title": "...",
        "auction_house": "...",
        "location": "...",
        "start_date": "YYYY-MM-DD",
        "notes": "optional extra notes"
      }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = (data.get("title") or "").strip()
    start_date_str = (data.get("start_date") or "").strip()

    if not title:
        return JsonResponse({"error": "Missing title"}, status=400)

    start_date = parse_date(start_date_str) or timezone.localdate()

    notes_parts = []
    if data.get("notes"):
        notes_parts.append(data["notes"])
    if data.get("url"):
        notes_parts.append(f"Source: {data['url']}")
    notes = "\n\n".join(notes_parts)

    event = SaleEvent.objects.create(
        title=title,
        auction_house=data.get("auction_house", "")[:200],
        location=data.get("location", "")[:200],
        start_date=start_date,
        end_date=None,
        status="researching",
        notes=notes,
    )

    return JsonResponse(
        {
            "ok": True,
            "id": event.id,
            "title": event.title,
            "start_date": str(event.start_date),
        }
    )
