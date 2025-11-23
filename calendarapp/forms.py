from django import forms
from .models import SaleEvent

class SaleEventForm(forms.ModelForm):
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
