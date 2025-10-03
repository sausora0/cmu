# teachers/urls.py
from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('dashboard/', views.teacherdashboard, name='dashboard'),
    path('calendar/', views.calendar, name='calendar'),
    path("announcement/", views.announcement_list, name="announcement_list"),
    path("announcement/<int:id>/", views.announcement_detail, name="announcement_detail"),
    path("announcement/<int:id>/edit/", views.announcement_edit, name="announcement_edit"),
    path("announcement/<int:id>/delete/", views.announcement_delete, name="announcement_delete"),
    path('subject/', views.subject, name='subject'),
    
    #Assignment Path
    path("assignment/form/<int:id>/", views.assignment_form, name="assignment_form"),
    path("assignment/<int:assignment_id>/", views.assignment_detail, name="assignment_detail"),
    path("assignment/<int:assignment_id>/submit/", views.submit_assignment, name="submit_assignment"),
    path("assignment/<int:assignment_id>/delete/", views.delete_assignment, name="delete_assignment"),
    #Notofication
    path("subject/<int:class_id>/clear-notifications/", views.clear_notifications, name="clear_notifications"),
    path('notification/redirect/<int:notification_id>/', views.notification_redirect, name='notification_redirect'),
    #Class Path
    path("create-class/", views.create_class, name="create_class"),
    path('subject/<int:id>/', views.subject, name='subject'),
    #Gradebook
    path("class/<int:class_id>/grades/", views.class_grades, name="class_grades"),
    path("class/<int:class_id>/grades/export/", views.export_grades, name="export_grades"),
    path("class/<int:class_id>/grades/import/", views.import_grades, name="import_grades"),
    path("class/<int:class_id>/grade/<int:submission_id>/", views.update_grade, name="update_grade"),
    # Archive/restore
    path("subject/<int:class_id>/archive/", views.archive_class, name="archive_class"),
    path("subject/<int:class_id>/restore/", views.restore_archived_class, name="restore_archived_class"),
    path("archived-classes/", views.archived_classes, name="archived_classes"),

    path("subject/<int:class_id>/edit/", views.edit_class, name="edit_class"),
    path("messages/", views.messages_inbox, name="messages_inbox"),       # just contacts, no chat open
    path("messages/<int:user_id>/", views.conversation, name="conversation"),  # open specific chat
    path("submissions/bulk-return/", views.bulk_return_submissions, name="bulk_return_submissions"),

    # Quiz-related routes
    path("class/<int:class_id>/quiz/create/", views.create_quiz, name="create_quiz"),
    path("quiz/<int:quiz_id>/grade/", views.grade_quiz, name="grade_quiz"), # NEW quiz path
    path("class/<int:class_id>/quiz/<int:quiz_id>/", views.quiz_detail, name="quiz_detail"),

    path("student/<int:user_id>/", views.student_detail, name="student_detail"),
    path("student/<int:user_id>/invite-parent/", views.invite_parent, name="invite_parent"),
    path("accept-parent-invite/<int:invite_id>/", views.accept_parent_invite, name="accept_parent_invite"),  # ✅ added

    path("authorize/", views.google_authorize, name="google_authorize"),
    path("oauth2callback/", views.google_oauth2_callback, name="google_oauth2_callback"),
    path("class/<int:class_id>/drive/", views.open_or_create_drive_folder, name="open_drive"),
]
