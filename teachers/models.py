from django.db import models
from django.conf import settings
import string, random
from django.contrib.auth.models import User


def generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Class(models.Model):
    class_name = models.CharField(max_length=100)
    subject_name = models.CharField(max_length=100)
    section = models.CharField(max_length=50)
    time = models.TimeField(null=True, blank=True)

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_classes"
    )
    code = models.CharField(max_length=10, unique=True, default=generate_class_code)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="enrolled_classes",
        blank=True
    )
    is_archived = models.BooleanField(default=False)  # ✅ new field
    banner = models.ImageField(upload_to="class_banners/", blank=True, null=True)
    theme = models.CharField(max_length=50, blank=True, null=True)  # NEW field

    def get_banner_url(self):
        if self.banner:  # uploaded image
            return self.banner.url
        elif self.theme:  # preset theme
            return f"/static/images/themes/{self.theme}.jpg"
        return "/static/images/default-banner.jpg"  # fallback
 # 🔹 New field for Google Drive
    gdrive_folder_id = models.CharField(max_length=200, blank=True, null=True)

    def get_drive_link(self):
        if self.gdrive_folder_id:
            return f"https://drive.google.com/drive/folders/{self.gdrive_folder_id}"
        return None
    
    def __str__(self):
        return f"{self.class_name} - {self.section}"

class Assignment(models.Model):
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    points = models.IntegerField(default=100)
    due_date = models.DateTimeField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
     # ✅ who this assignment is for
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="student_assignments", blank=True)

    def __str__(self):
        return f"{self.title} ({self.class_obj.class_name} - {self.class_obj.section})"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to="submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)  # ✅ add this field
    # NEW fields
    grade = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # 0 - 100 etc
    is_published = models.BooleanField(default=False)  # if True students can see grade
    is_returned = models.BooleanField(default=False)   # optional: returned/feedback flag

    status = models.CharField(
        max_length=20,
        choices=[("assigned", "Assigned"), ("turned_in", "Turned In"), ("missing", "Missing")],
        default="assigned"
    )
    def status(self):
        """Convenience method for status chips"""
        if self.grade is not None:
            return "graded"
        if self.file:
            return "turned_in"
        return "missing"
    
    def __str__(self):
        return f"{self.student.username} → {self.assignment.title}"
    
class StreamNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    class_obj = models.ForeignKey(
        "Class",
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    assignment = models.ForeignKey("Assignment", on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)  # ✅ New field
    
    def __str__(self):
        return f"{self.user} - {self.message[:30]}"
    
class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('exam', 'Exams'),
        ('event', 'Events'),
        ('reminder', 'Reminders'),
        ('general', 'General'),
    ]
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.title
    
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    EVENT_TYPE_CHOICES = [
        ("announcement", "Announcement"),
        ("exam", "Exam"),
        ("holiday", "Holiday"),
        ("meeting", "Meeting"),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default="announcement")

    def __str__(self):
        return f"{self.title} ({self.date})"
    
class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_messages",
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_messages",
        on_delete=models.CASCADE
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.content[:20]}"

class Quiz(models.Model):
    QUIZ_TYPES = [
        ("quiz", "Quiz"),
        ("exam", "Exam"),
    ]

    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    quiz_type = models.CharField(max_length=10, choices=QUIZ_TYPES, default="quiz")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_quizzes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_quiz_type_display()})"


class Question(models.Model):
    QUESTION_TYPES = [
        ("multiple-choice", "Multiple Choice"),
        ("identification", "Identification"),
        ("essay", "Essay"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)

    def __str__(self):
        return f"{self.text[:50]}..."


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Wrong'})"


class StudentAnswer(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_option = models.ForeignKey(
        Option, null=True, blank=True, on_delete=models.SET_NULL
    )
    text_answer = models.TextField(blank=True, null=True)  # for essay/identification
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)  # auto-grading result
    
    def __str__(self):
        return f"Answer by {self.student} → {self.question.text[:30]}"
    
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL  # cleaner alias

class ParentInvite(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_invites")
    parent_email = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_parent_invites")
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite: {self.parent_email} -> {self.student}"
    

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")  # Parent account
    children = models.ManyToManyField(User, related_name="linked_parents", blank=True)  # Links to User accounts with role=student

    def __str__(self):
        return f"Parent: {self.user}"
