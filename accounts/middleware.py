# accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path

            # Students
            if path.startswith("/students/") and request.user.role != "student":
                return redirect(self._get_dashboard(request.user))

            # Teachers
            if path.startswith("/teachers/") and request.user.role != "teacher":
                return redirect(self._get_dashboard(request.user))

            # Parents
            if path.startswith("/parents/") and request.user.role != "parent":
                return redirect(self._get_dashboard(request.user))

            # Admins
            if path.startswith("/school_admin/") and request.user.role != "admin":
                return redirect(self._get_dashboard(request.user))

        return self.get_response(request)

    def _get_dashboard(self, user):
        """Redirect to the correct dashboard based on role"""
        if user.role == "student":
            return reverse("students:dashboard")
        elif user.role == "teacher":
            return reverse("teachers:dashboard")
        elif user.role == "parent":
            return reverse("parents:dashboard")
        elif user.role == "school_admin":
            return reverse("admins:dashboard")
        return reverse("accounts:redirect_dashboard")
