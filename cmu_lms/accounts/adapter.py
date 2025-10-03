# accounts/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.role == "student":
            return reverse("students:dashboard")
        elif user.role == "teacher":
            return reverse("teachers:dashboard")
        elif user.role == "parent":
            return reverse("parents:dashboard")
        elif user.role == "school_admin":
            return reverse("admins:dashboard")
        return reverse("accounts:redirect_dashboard")  # fallback
