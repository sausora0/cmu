from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')

from django import forms
from .models import UserSettings

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        exclude = ['user']
        widgets = {
            'profile_visibility': forms.Select(attrs={'class':'form-select'}),
            'notification_frequency': forms.Select(attrs={'class':'form-select'}),
            'theme': forms.Select(attrs={'class':'form-select'}),
            'language': forms.Select(attrs={'class':'form-select'}),
            'timezone': forms.Select(attrs={'class':'form-select'}),
            'font_size': forms.Select(attrs={'class':'form-select'}),
        }
