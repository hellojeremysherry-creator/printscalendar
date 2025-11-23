from django import forms
from .models import SaleEvent


class SaleEventForm(forms.ModelForm):
    # Make start_date more flexible
    start_date = forms.DateField(
        label="Start date",
        input_formats=[
            "%Y-%m-%d",  # 2025-10-25
            "%m/%d/%Y",  # 10/25/2025
            "%m/%d/%y",  # 10/25/25
            "%m-%d-%Y",  # 10-25-2025
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. 10/25/2025 or 2025-10-25",
            }
        ),
    )

    # Same flexibility for end_date (optional)
    end_date = forms.DateField(
        label="End date",
        required=False,
        input_formats=[
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%m-%d-%Y",
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. 10/26/2025 (optional)",
            }
        ),
    )

    class Meta:
        model = SaleEvent
        fields = [
            "title",
            "auction_house",
            "location",
            "start_date",
            "end_date",
            "status",
            "notes",
        ]


# NEW: form just for analysis_notes
class SaleEventAnalysisForm(forms.ModelForm):
    class Meta:
        model = SaleEvent
        fields = ["analysis_notes"]
        widgets = {
            "analysis_notes": forms.Textarea(
                attrs={
                    "rows": 28,
                    "class": "form-control font-monospace",
                }
            )
        }
        labels = {
            "analysis_notes": "Research / Arbitrage Dossier",
        }
