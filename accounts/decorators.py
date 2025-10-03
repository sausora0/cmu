# accounts/decorators.py
from django.shortcuts import redirect
from functools import wraps

def school_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "school_admin":
            return view_func(request, *args, **kwargs)
        return redirect("no_permission")  # make a template for unauthorized access
    return wrapper

# accounts/decorators.py
from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")  # allauth login
            if request.user.role not in allowed_roles:
                # redirect to their dashboard
                from django.urls import reverse
                if request.user.role == "student":
                    return redirect(reverse("students:dashboard"))
                elif request.user.role == "teacher":
                    return redirect(reverse("teachers:dashboard"))
                elif request.user.role == "parent":
                    return redirect(reverse("parents:dashboard"))
                elif request.user.role == "school_admin":
                    return redirect(reverse("admins:dashboard"))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
