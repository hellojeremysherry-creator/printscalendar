from django.urls import path
from . import views

app_name = 'calendarapp'

urlpatterns = [
    path('', views.MonthView.as_view(), name='month_view'),
    path('day/<int:year>/<int:month>/<int:day>/', views.DayView.as_view(), name='day_view'),
    path('event/add/', views.SaleEventCreateView.as_view(), name='event_add'),
    path('event/<int:pk>/edit/', views.SaleEventUpdateView.as_view(), name='event_edit'),
    path('event/<int:pk>/delete/', views.SaleEventDeleteView.as_view(), name='event_delete'),
    path("api/scrape-auction/", views.scrape_auction, name="scrape_auction"),

    # NEW:
    path("api/create-from-page/", views.create_event_from_page, name="create_from_page"),
]
