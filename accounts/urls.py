from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('redirect-dashboard/', views.redirect_dashboard, name='redirect_dashboard'),
    path('choose-role/', views.choose_role, name="choose_role"),
    # allauth urls (Google login, etc.)
    path("", include("allauth.urls")),
    path('settings/', views.settings_view, name='settings'),
]