from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import User
from allauth.socialaccount.providers import registry

def login_view(request):
    context = {
        'socialaccount': {
            'providers': {
                'google': registry.by_id('google', request)
            }
        }
    }
    return render(request, 'accounts/login.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('accounts:redirect_dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')

@login_required
def redirect_dashboard(request):
    user = request.user

    # Superuser or admin role
    if user.is_superuser or user.role == "admin":
        return redirect("/admin/")

    # If no role yet, send to role selection
    if not user.role:
        return redirect("accounts:choose_role")

    # Role-based dashboards
    if user.role == "teacher":
        return redirect("teachers:dashboard")
    elif user.role == "student":
        return redirect("students:dashboard")
    elif user.role == "parent":
        return redirect("parents:dashboard")
    elif user.role == "school_admin":
        return redirect("admins:dashboard")  # fixed ✅

    # Default fallback
    return redirect("accounts:choose_role")
    
@login_required
def choose_role(request):
    if request.method == "POST":
        role = request.POST.get("role")
        if role in ["student", "teacher", "parent"]:
            request.user.role = role
            request.user.save()
            return redirect("accounts:redirect_dashboard")  # send back to dashboard redirect
    return render(request, "accounts/choose_role.html")

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserSettings
from .forms import UserSettingsForm

@login_required
def settings_view(request):
    settings_obj, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            return redirect('accounts:settings')
    else:
        form = UserSettingsForm(instance=settings_obj)

    return render(request, 'accounts/settings.html', {'form': form})
