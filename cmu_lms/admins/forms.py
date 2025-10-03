from django import forms
from accounts.models import User
from .models import SchoolClass, Announcement
from .models import ParentStudent

class TeacherForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password"]

class StudentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password"]

class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "subject", "teacher", "students"]

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message"]
    
class ParentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password"]

class ParentStudentForm(forms.ModelForm):
    class Meta:
        model = ParentStudent
        fields = ["parent", "student"]
