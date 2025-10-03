from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('calendar/', views.calendar, name='calendar'),
    path("join_class_ajax/", views.join_class_ajax, name="join_class_ajax"),
    path("archived/", views.archived_classes, name="archived_classes"),
    path("restore/", views.restore_class, name="restore_class"),
    path("archive/", views.archive_class, name="archive_class"), 
    path("unenroll/", views.unenroll_class, name="unenroll_class"),
    path('class/<int:id>/', views.class_detail, name='class_detail'),
    path("announcements/", views.student_announcements, name="student_announcements"),
    path("assignment/<int:id>/", views.assignment_detail, name="assignment_detail"),

    path('messages/', views.messages_inbox, name='messages_inbox'),
    path('messages/<int:user_id>/', views.conversation, name='conversation'),
    path("notification/<int:notification_id>/", views.notification_redirect, name="notification_redirect"),
    path("grades/", views.student_grades, name="grades"),

    path("quiz/<int:quiz_id>/", views.take_quiz, name="take_quiz"),
]