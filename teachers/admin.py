from django.contrib import admin
from .models import Class, Assignment

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("class_name", "subject_name", "section", "teacher", "code", "time")
    list_filter = ("section", "teacher")
    search_fields = ("class_name", "subject_name", "teacher__username", "teacher__first_name", "teacher__last_name")
    
    # Only superuser can see this in admin
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_obj', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'class_obj__class_name', 'class_obj__section')
    list_filter = ('class_obj', 'due_date', 'created_at')

from django.contrib import admin
from .models import Submission, StreamNotification, Announcement, Event, Message


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "is_submitted", "grade", "is_published", "is_returned", "status")
    list_filter = ("is_submitted", "is_published", "is_returned")
    search_fields = ("student__username", "assignment__title")
    date_hierarchy = "submitted_at"

    def status_display(self, obj):
        return obj.status()
    status_display.short_description = "Status"


@admin.register(StreamNotification)
class StreamNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "class_obj", "assignment", "message_preview", "created_at", "read")
    list_filter = ("read", "created_at")
    search_fields = ("user__username", "message")

    def message_preview(self, obj):
        return obj.message[:50]
    message_preview.short_description = "Message"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority", "date_posted", "author")
    list_filter = ("category", "priority", "date_posted")
    search_fields = ("title", "content", "author__username")
    date_hierarchy = "date_posted"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "date", "created_by", "created_at")
    list_filter = ("event_type", "date")
    search_fields = ("title", "description")
    date_hierarchy = "date"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "content_preview", "timestamp", "is_read")
    list_filter = ("is_read", "timestamp")
    search_fields = ("sender__username", "recipient__username", "content")
    date_hierarchy = "timestamp"

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = "Content"

from django.contrib import admin
from .models import Quiz, Question, Option, StudentAnswer


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2  # show 2 empty option fields by default


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True  # lets you click into a full question page


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "class_obj", "quiz_type", "created_by", "created_at")
    list_filter = ("quiz_type", "class_obj")
    search_fields = ("title", "class_obj__class_name")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "question_type")
    list_filter = ("question_type", "quiz")
    search_fields = ("text", "quiz__title")
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("is_correct", "question__quiz")
    search_fields = ("text", "question__text")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "selected_option", "score", "submitted_at")
    list_filter = ("score", "submitted_at", "question__quiz")
    search_fields = ("student__username", "question__text", "selected_option__text")

