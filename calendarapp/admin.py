from django.contrib import admin
from .models import SaleEvent


@admin.register(SaleEvent)
class SaleEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'status', 'auction_house')
    list_filter = ('status', 'auction_house', 'start_date')
    search_fields = ('title', 'auction_house', 'notes', 'analysis_notes')  # ← add
