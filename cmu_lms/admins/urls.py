from django.urls import path
from . import views

app_name = "admins"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),

    # Teacher
    path("teachers/", views.teacher_list, name="teacher_list"),
    path("teachers/<int:teacher_id>/", views.teacher_detail, name="teacher_detail"),
    path("teachers/add/", views.teacher_add, name="teacher_add"),
    path("teachers/<int:teacher_id>/delete/", views.teacher_delete, name="teacher_delete"),

    # Student
    path("students/", views.student_list, name="student_list"),
     path("students/<int:student_id>/", views.student_detail, name="student_detail"),
    path("students/add/", views.student_add, name="student_add"),
    path("students/delete/<int:id>/", views.student_delete, name="student_delete"),

    # Classes
    path("classes/", views.class_list, name="class_list"),
    path("classes/add/", views.class_add, name="class_add"),
    path("classes/delete/<int:id>/", views.class_delete, name="class_delete"),

    # Announcements
    path("announcements/", views.announcement_list, name="announcement_list"),
    path("announcements/add/", views.announcement_add, name="announcement_add"),

    # Parents
    path("parents/", views.parent_list, name="parent_list"),
    path("parents/add/", views.parent_add, name="parent_add"),
    path("parents/delete/<int:id>/", views.parent_delete, name="parent_delete"),

    # Parent-Student links
    path("parent-students/", views.parent_student_list, name="parent_student_list"),
    path("parent-students/add/", views.parent_student_add, name="parent_student_add"),
    path("parent-students/delete/<int:id>/", views.parent_student_delete, name="parent_student_delete"),
]
