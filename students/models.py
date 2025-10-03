from django.db import models
from django.conf import settings
from teachers.models import Quiz   # import your Quiz model

class StudentQuizAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name="attempts", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[("completed", "Completed")],
        default="completed"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "quiz")  # prevents duplicate attempts

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.status})"
    
    
