from django.contrib import admin
from django.urls import path, include
from calendarapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('calendarapp.urls')),
    path("api/scrape-auction/", views.scrape_auction, name="scrape_auction"),

]
