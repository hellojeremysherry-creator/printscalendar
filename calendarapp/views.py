import calendar
import json
from datetime import date
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import SaleEventForm, SaleEventAnalysisForm
from .models import SaleEvent

DEFAULT_ANALYSIS_TEMPLATE = """## Acquisition Criteria

- [ ] Edition size ≤150 (or justified by strong market history)
- [ ] Clear arbitrage (geographic, cataloging error, weak photography, variant mispricing, etc.)

---

## 1️⃣ Lot Extraction

- Auction: {{ event.title }} ({{ event.auction_house }} — {{ event.location }})
- Catalogue URL(s):
- Buyer’s premium schedule:

Lots of interest:
- Lot ___ – Artist, *Title*, year, medium, edition, size, signature, condition.
- Lot ___ – ...

---

## 2️⃣ Value Calibration (Comps & Fair Market Range)

For each lot:

- Recent comps:
  - [Auction House, Date] — Price, details
  - ...
- FX assumptions:
- Fair value range:
  - LOW  : $
  - MID  : $
  - HIGH : $
- Notes vs. house estimate:

---

## 3️⃣ Cost Modeling

Formula: All-in = Hammer × (1 + BP) + Tax + Shipping/Insurance/Handling

- Tax assumption:
- Shipping estimate:
- Storage / framing (if any):
- Unknowns / VERIFY:

---

## 4️⃣ Arbitrage Analysis (Resale Optimization)

For each viable lot:

- Optimal venue:
- Alternates:
- Price band:
- Expected liquidity window:
- Rationale:

Score:
- Arbitrage Score (0–100):
- Value Realization (±% vs estimate):
- Liquidity Tier: A / B / C

---

## 5️⃣ Watchlist

Lots to watch contingent on:
- Condition checks:
- Bidding patterns:
- Catalogue discrepancies:
- Timing:

---

## 6️⃣ Execution Playbook

- Bidding strategy:
- Documentation prep:
- Post-acquisition routing:
- Conservation / framing:
- Consignment target(s) + fee assumptions:

---

## Integrity Notes

- Data sources:
- Unknowns flagged:
- Risks / red flags:
"""


class SaleEventAnalysisUpdateView(generic.UpdateView):
    """
    Dedicated page to write long-form research notes for a single event.
    If analysis_notes is empty, we seed it with DEFAULT_ANALYSIS_TEMPLATE.
    """
    model = SaleEvent
    form_class = SaleEventAnalysisForm
    template_name = "calendarapp/event_analysis_form.html"

    def get_initial(self):
        initial = super().get_initial()
        if not self.object.analysis_notes:
            initial["analysis_notes"] = DEFAULT_ANALYSIS_TEMPLATE
        return initial

    def get_success_url(self):
        # After saving, drop back to the day view for that event’s start date
        event = self.object
        return reverse(
            "calendarapp:day_view",
            kwargs={
                "year": event.start_date.year,
                "month": event.start_date.month,
                "day": event.start_date.day,
            },
        )


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


def password_gate(request):
    """
    Very simple one-field form asking for the site password.

    If PASSWORD_PROTECT_ENABLED is False, we just bounce them to /
    so dev environments are not stuck here.
    """
    if not getattr(settings, "PASSWORD_PROTECT_ENABLED", False):
        return redirect("/")

    error = None

    if request.method == "POST":
        submitted = (request.POST.get("password") or "").strip()
        expected = getattr(settings, "PASSWORD_PROTECT_PASSWORD", "")

        if expected and submitted == expected:
            # Correct password – unlock this session
            request.session["site_unlocked"] = True

            # Redirect to the originally requested URL if we stored it
            next_url = request.session.pop("site_next", None)
            if not next_url:
                next_url = reverse("calendarapp:month_view")
            return redirect(next_url)
        else:
            error = "Incorrect password. Please try again."

    return render(request, "calendarapp/password_gate.html", {"error": error})
