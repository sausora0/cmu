from django.db import models
from accounts.models import User

class SchoolClass(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admin_teaching_classes"  # ✅ changed
    )
    students = models.ManyToManyField(
        User,
        related_name="admin_enrolled_classes",  # ✅ changed
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="announcements")

    def __str__(self):
        return self.title
    
class ParentStudent(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children_relations")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_relations")

    def __str__(self):
        return f"{self.parent.get_full_name()} → {self.student.get_full_name()}"