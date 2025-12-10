from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class PasswordProtectionMiddleware(MiddlewareMixin):
    """
    Simple whole-site password wall.

    If PASSWORD_PROTECT_ENABLED is True, any request from a user who has not yet
    provided the correct password is redirected to the password gate view.

    Once the correct password is entered, we store a flag in the session and
    allow normal access.
    """

    SESSION_KEY = "site_unlocked"

    def process_request(self, request):
        if not getattr(settings, "PASSWORD_PROTECT_ENABLED", False):
            return None

        static_url = getattr(settings, "STATIC_URL", "/static/")
        if static_url and request.path.startswith(static_url):
            return None

        # Use namespaced URL name
        try:
            password_url = reverse("calendarapp:password_gate")
        except Exception:
            password_url = "/access/"

        if request.path == password_url:
            return None

        if request.path.startswith("/admin/"):
            return None

        if request.session.get(self.SESSION_KEY, False):
            return None

        request.session["site_next"] = request.get_full_path()

        # Redirect using the namespaced name
        return redirect("calendarapp:password_gate")
