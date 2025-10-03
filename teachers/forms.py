from django import forms
from .models import Class
from .models import Assignment, Submission, Announcement, Event
from django.contrib.auth import get_user_model
User = get_user_model()


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "instructions", "points", "due_date", "due_time", "assigned_to"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "gclass-title-input",
                "placeholder": "Title*",
                "required": True
            }),
            "instructions": forms.Textarea(attrs={
                "class": "gclass-instructions",
                "placeholder": "Add instructions (optional)...",
                "rows": 6
            }),
            "points": forms.NumberInput(attrs={
                "class": "form-control mb-3", "min": 0, "value": 100
            }),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control mb-3"}),
            "due_time": forms.TimeInput(attrs={"type": "time", "class": "form-control mb-3"}),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["file"]
        
THEME_CHOICES = [
    ("math", "Mathematics"),
    ("science", "Science"),
    ("history", "History"),
    ("literature", "Literature"),
    ("technology", "Technology"),
]

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['time']
        widgets = {
            'time': forms.TimeInput(format='%H:%M'),
        }

    theme = forms.ChoiceField(choices=[("", "None")] + THEME_CHOICES, required=False)

    class Meta:
        model = Class
        fields = ['class_name', 'subject_name', 'section', 'banner', 'theme']

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your announcement...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "event_type"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control",'placeholder': 'Enter title'}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, 'placeholder': 'Write Description...'}),
            "event_type": forms.Select(attrs={"class": "form-select"}),
        }

