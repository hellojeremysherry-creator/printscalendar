import calendar
from datetime import date
from django.urls import reverse_lazy
from django.views import generic
from django.utils import timezone
from .models import SaleEvent
from .forms import SaleEventForm
import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse

def scrape_auction(request):
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "Missing URL"}, status=400)

    try:
        headers = { "User-Agent": "Mozilla/5.0" }
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")

        # These selectors may need tweaking depending on the page
        title = soup.select_one(".auction-title").get_text(strip=True)
        date = soup.select_one(".auction-date").get_text(strip=True)
        house = soup.select_one(".auction-house").get_text(strip=True)

        return JsonResponse({
            "title": title,
            "auction_house": house,
            "start_date": date,   # you may need to date-parse
        })

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

        # Calendar matrix: list of weeks, each week is list of (day, events)
        cal = calendar.Calendar(firstweekday=0)  # Monday = 0 if you want
        month_days = cal.itermonthdates(year, month)

        weeks = []
        week = []
        for d in month_days:
            day_events = SaleEvent.objects.filter(
                start_date__lte=d,
                end_date__gte=d
            ) | SaleEvent.objects.filter(
                start_date=d,
                end_date__isnull=True
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
