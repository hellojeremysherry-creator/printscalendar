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
        # If not enabled, do nothing
        if not getattr(settings, "PASSWORD_PROTECT_ENABLED", False):
            return None

        # Allow static files
        static_url = getattr(settings, "STATIC_URL", "/static/")
        if static_url and request.path.startswith(static_url):
            return None

        # Allow the password page itself
        try:
            password_url = reverse("password_gate")
        except Exception:
            password_url = "/access/"  # fallback; must match your URL pattern
        if request.path == password_url:
            return None

        # Optionally allow /admin/ to bypass the wall:
        # (if you *want* to lock admin too, remove this block)
        if request.path.startswith("/admin/"):
            return None

        # If session is already unlocked, let them through
        if request.session.get(self.SESSION_KEY, False):
            return None

        # Remember where they were trying to go
        request.session["site_next"] = request.get_full_path()

        # Redirect to password gate
        return redirect("password_gate")
