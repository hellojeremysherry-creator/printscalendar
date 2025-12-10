from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('calendarapp.urls')),
    # Your existing app
    path('', include('calendarapp.urls')),
]
