from django import forms
from .models import SaleEvent

class SaleEventForm(forms.ModelForm):
    auction_url = forms.URLField(required=False, label="Auction URL")

    class Meta:
        model = SaleEvent
        fields = [
            "auction_url",       # new!
            "title",
            "auction_house",
            "location",
            "start_date",
            "end_date",
            "status",
            "notes",
        ]
