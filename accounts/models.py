from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
        ("school_admin", "School Admin"),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,   # ✅ allow empty
        null=True     # ✅ allow NULL in DB
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.URLField(blank=True, null=True)  # Google profile picture

    def __str__(self):
        return self.user.username
    
from django.db import models
from django.conf import settings

class UserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Profile settings
    show_email = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=False)
    profile_visibility = models.CharField(
        max_length=20,
        choices=[('everyone', 'Everyone'), ('teachers', 'Teachers Only'), ('parents', 'Parents Only')],
        default='everyone'
    )

    # Notifications
    notify_assignments = models.BooleanField(default=True)
    notify_messages = models.BooleanField(default=True)
    notify_grades = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[('immediate', 'Immediate'), ('daily', 'Daily Digest'), ('weekly', 'Weekly Summary')],
        default='immediate'
    )

    # Preferences
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    language = models.CharField(max_length=20, default='en')
    timezone = models.CharField(max_length=50, default='Asia/Manila')
    font_size = models.CharField(max_length=10, choices=[('small','Small'),('medium','Medium'),('large','Large')], default='medium')
    high_contrast = models.BooleanField(default=False)

    # Communication
    allow_messages_from_students = models.BooleanField(default=True)
    allow_messages_from_parents = models.BooleanField(default=True)
    allow_group_chat = models.BooleanField(default=True)

    # Teacher-only
    default_grading_scheme = models.CharField(max_length=50, default='Percentage')
    allow_late_submission = models.BooleanField(default=True)
    max_file_size_mb = models.IntegerField(default=10)

    def __str__(self):
        return f"Settings for {self.user.username}"
