from django.urls import path
from . import views

app_name = 'calendarapp'

urlpatterns = [
    path('', views.MonthView.as_view(), name='month_view'),
    path('day/<int:year>/<int:month>/<int:day>/', views.DayView.as_view(), name='day_view'),
    path('event/add/', views.SaleEventCreateView.as_view(), name='event_add'),
    path('event/<int:pk>/edit/', views.SaleEventUpdateView.as_view(), name='event_edit'),
    path('event/<int:pk>/delete/', views.SaleEventDeleteView.as_view(), name='event_delete'),

    # NEW:
    # existing API route
    # path("api/create-from-page/", views.create_event_from_page, name="create_from_page"),

    # NEW: analysis editor
    path("event/<int:pk>/analysis/", views.SaleEventAnalysisUpdateView.as_view(),
         name="event_analysis"),

    # NEW: password gate URL
    path('access/', views.password_gate, name='password_gate'),

]
