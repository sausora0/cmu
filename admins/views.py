from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import school_admin_required
from accounts.models import User
from .models import SchoolClass, Announcement
from .forms import TeacherForm, StudentForm, SchoolClassForm, AnnouncementForm
from teachers.models import Class 
# === DASHBOARD ===
@login_required
@school_admin_required
def dashboard(request):
    teachers = User.objects.filter(role="teacher").count()
    students = User.objects.filter(role="student").count()
    parents = User.objects.filter(role="parent").count()  # ✅ added
    classes = Class.objects.count()
    announcements = Announcement.objects.count()

    return render(request, "admins/dashboard.html", {
        "teachers": teachers,
        "students": students,
        "parents": parents,              # ✅ added
        "classes": classes,
        "announcements": announcements
    })

# === TEACHER CRUD ===
@login_required
@school_admin_required
def teacher_list(request):
    teachers = User.objects.filter(role="teacher")
    return render(request, "admins/teacher_list.html", {"teachers": teachers})

@login_required
@school_admin_required
def teacher_add(request):
    if request.method == "POST":
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.role = "teacher"
            teacher.set_password(form.cleaned_data["password"])
            teacher.save()
            return redirect("admins:teacher_list")
    else:
        form = TeacherForm()
    return render(request, "admins/teacher_form.html", {"form": form})

@login_required
@school_admin_required
def teacher_delete(request, id):
    teacher = get_object_or_404(User, id=id, role="teacher")
    teacher.delete()
    return redirect("admins:teacher_list")

@login_required
@school_admin_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role="teacher")
    classes = teacher.created_classes.all()  # ✅ assumes teachers.Class has ForeignKey(teacher=User)

    return render(request, "admins/teacher_detail.html", {
        "teacher": teacher,
        "classes": classes,
    })
# === STUDENT CRUD ===
@login_required
@school_admin_required
def student_list(request):
    students = User.objects.filter(role="student")
    return render(request, "admins/student_list.html", {"students": students})

@login_required
@school_admin_required
def student_add(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.role = "student"
            student.set_password(form.cleaned_data["password"])
            student.save()
            return redirect("admins:student_list")
    else:
        form = StudentForm()
    return render(request, "admins/student_form.html", {"form": form})

@login_required
@school_admin_required
def student_delete(request, id):
    student = get_object_or_404(User, id=id, role="student")
    student.delete()
    return redirect("admins:student_list")

# === STUDENT DETAIL VIEW ===
@login_required
@school_admin_required
def student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id, role="student")
    classes = student.enrolled_classes.all()  # ✅ M2M relation from your model

    return render(request, "admins/student_detail.html", {
        "student": student,
        "classes": classes,
    })
# === CLASS CRUD ===
@login_required
@school_admin_required
def class_list(request):
    classes = SchoolClass.objects.all()
    return render(request, "admins/class_list.html", {"classes": classes})

@login_required
@school_admin_required
def class_add(request):
    if request.method == "POST":
        form = SchoolClassForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("class_list")
    else:
        form = SchoolClassForm()
    return render(request, "admins/class_form.html", {"form": form})

@login_required
@school_admin_required
def class_delete(request, id):
    c = get_object_or_404(SchoolClass, id=id)
    c.delete()
    return redirect("class_list")

# === ANNOUNCEMENTS ===
@login_required
@school_admin_required
def announcement_list(request):
    announcements = Announcement.objects.all().order_by("-created_at")
    return render(request, "admins/announcement_list.html", {"announcements": announcements})

@login_required
@school_admin_required
def announcement_add(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            return redirect("announcement_list")
    else:
        form = AnnouncementForm()
    return render(request, "admins/announcement_form.html", {"form": form})

# admins/views.py
from .forms import ParentForm, ParentStudentForm
from .models import ParentStudent

# === PARENT CRUD ===
@login_required
@school_admin_required
def parent_list(request):
    parents = User.objects.filter(role="parent")
    return render(request, "admins/parent_list.html", {"parents": parents})

@login_required
@school_admin_required
def parent_add(request):
    if request.method == "POST":
        form = ParentForm(request.POST)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.role = "parent"
            parent.set_password(form.cleaned_data["password"])
            parent.save()
            return redirect("parent_list")
    else:
        form = ParentForm()
    return render(request, "admins/parent_form.html", {"form": form})

@login_required
@school_admin_required
def parent_delete(request, id):
    parent = get_object_or_404(User, id=id, role="parent")
    parent.delete()
    return redirect("parent_list")

# === LINK PARENT TO STUDENT ===
@login_required
@school_admin_required
def parent_student_list(request):
    links = ParentStudent.objects.all()
    return render(request, "admins/parent_student_list.html", {"links": links})

@login_required
@school_admin_required
def parent_student_add(request):
    if request.method == "POST":
        form = ParentStudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("parent_student_list")
    else:
        form = ParentStudentForm()
    return render(request, "admins/parent_student_form.html", {"form": form})

@login_required
@school_admin_required
def parent_student_delete(request, id):
    link = get_object_or_404(ParentStudent, id=id)
    link.delete()
    return redirect("parent_student_list")
