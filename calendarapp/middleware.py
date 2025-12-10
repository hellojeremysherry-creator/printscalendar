from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class PasswordProtectionMiddleware(MiddlewareMixin):
    SESSION_KEY = "site_unlocked"

    def process_request(self, request):
        if not getattr(settings, "PASSWORD_PROTECT_ENABLED", False):
            return None

        static_url = getattr(settings, "STATIC_URL", "/static/")
        if static_url and request.path.startswith(static_url):
            return None

        # 🔹 Allow favicon (and optionally robots.txt) through without gating
        if request.path in ("/favicon.ico", "/robots.txt"):
            return None

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

        # Remember where they were trying to go (but don't let favicon overwrite it)
        if "site_next" not in request.session:
            request.session["site_next"] = request.get_full_path()

        return redirect("calendarapp:password_gate")
