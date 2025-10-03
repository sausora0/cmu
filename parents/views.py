from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from teachers.models import Parent

@login_required
def dashboard(request):
    parent, created = Parent.objects.get_or_create(user=request.user)
    children = parent.children.filter(role="student")


    return render(request, "parents/dashboard.html", {
        "parent": parent,
        "children": children,
    })


@login_required
def view_progress(request, student_id):
    parent = Parent.objects.get(user=request.user)
    student = parent.children.get(id=student_id)  # ensures parent only sees their own child
    
    # Example: fetch grades, quizzes, attendance
    quizzes = student.quizsubmission_set.all()
    assignments = student.assignment_set.all()
    
    return render(request, "parents/view_progress.html", {
        "student": student,
        "quizzes": quizzes,
        "assignments": assignments,
    })
