from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from teachers.models import Class  # import the teacher’s Class model
from .forms import JoinClassForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from teachers.models import Event,Assignment,Submission,Message,StreamNotification

@login_required
def dashboard(request):
    user = request.user
    # All classes the student is enrolled in
    enrolled_classes = request.user.enrolled_classes.filter(is_archived=False)  # 👈 Only active classes
    # Optionally, you can show classes in grid (same as sidebar)
    classes = enrolled_classes.order_by('class_name')
    
    return render(request, "students/dashboard.html", {
        "classes": classes,
        "enrolled_classes": enrolled_classes
    })
@login_required
def calendar(request):
    events = Event.objects.all().order_by("date")
    return render(request, "students/calendar.html", {"events": events})

@login_required
@require_POST
def join_class_ajax(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        try:
            class_obj = Class.objects.get(code=code)
            class_obj.students.add(request.user)  # Save to DB
            class_obj.save()
            
            # Return updated info
            enrolled_count = request.user.enrolled_classes.count()
            return JsonResponse({
                "status": "success",
                "message": f"Successfully joined {class_obj.class_name}!",
                "class": {
                    "id": class_obj.id,
                    "name": class_obj.class_name,
                    "section": class_obj.section,
                    "banner": class_obj.get_banner_url(),
                },
                "class_count": enrolled_count
            })
        except Class.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid class code."})
    else:
        return JsonResponse({"status": "error", "message": "Form is invalid."})
    

from django.shortcuts import render, get_object_or_404
from teachers.models import Class

@login_required
def class_detail(request, id):
    class_obj = get_object_or_404(Class, id=id, students=request.user)
    assignments = class_obj.assignments.all().order_by('-created_at')
    user = request.user
     # Get stream notifications (same as teachers)
    notifications = class_obj.notifications.all().order_by('-created_at')
    
      # get quizzes
    quizzes = Quiz.objects.filter(class_obj=class_obj).order_by("-created_at")
    
     # Attach attempt info
    for quiz in quizzes:
        quiz.student_attempt = quiz.attempts.filter(student=request.user).first()

    # Attach student's submission to each assignment
    for assignment in assignments:
        assignment.student_submission = Submission.objects.filter(
            assignment=assignment,
            student=user
        ).first()

    # All classes the student is enrolled in
    enrolled_classes = user.enrolled_classes.all()
    classes = enrolled_classes.order_by('class_name')

    context = {
        "class_obj": class_obj,
        "assignments": assignments,
        "classes": classes,
        "enrolled_classes": enrolled_classes,
        "notifications": notifications,
        "quizzes": quizzes,
    }
    return render(request, "students/class_detail.html", context)

@login_required
def notification_redirect(request, notification_id):
    notif = get_object_or_404(StreamNotification, id=notification_id)

    # If assignment was graded → go to grades page
    if notif.assignment and "graded" in notif.message.lower():
        return redirect('students:grades', class_id=notif.assignment.class_obj.id)

    # Otherwise → assignment detail
    if notif.assignment:
        return redirect('students:assignment_detail', id=notif.assignment.id)

    # Otherwise → class stream
    return redirect('students:class_detail', id=notif.class_obj.id)



@login_required
def archived_classes(request):
    archived_classes = Class.objects.filter(students=request.user, is_archived=True)
    return render(request, "students/archived_classes.html", {
        "archived_classes": archived_classes
    })

@login_required
def restore_class(request):
    if request.method == "POST":
        class_id = request.POST.get("class_id")
        try:
            class_obj = Class.objects.get(id=class_id, students=request.user)
            class_obj.is_archived = False
            class_obj.save()
            return redirect("students:archived_classes")
        except Class.DoesNotExist:
            return redirect("students:archived_classes")
@login_required
def archive_class(request):
    if request.method == "POST":
        class_id = request.POST.get("class_id")
        try:
            class_obj = Class.objects.get(id=class_id, students=request.user)
            class_obj.is_archived = True
            class_obj.save()
            return redirect("students:archived_classes")  # ✅ go to archived classes page
        except Class.DoesNotExist:
            return redirect("students:dashboard")
 
@login_required
def unenroll_class(request):
    if request.method == "POST":
        class_id = request.POST.get("class_id")
        try:
            class_obj = Class.objects.get(id=class_id)
            class_obj.students.remove(request.user)
            return redirect("students:dashboard")  # adjust to your dashboard
        except Class.DoesNotExist:
            return redirect("students:dashboard")

from django.shortcuts import render
from teachers.models import Announcement  # import the model from teachers app
from django.contrib.auth.decorators import login_required

@login_required
def student_announcements(request):
    # show all announcements (or filter later if needed)
    announcements = Announcement.objects.all().order_by('-date_posted')

    return render(request, "students/announcements.html", {
        "announcements": announcements
    })

@login_required
def student_stream(request, class_id):
    class_obj = get_object_or_404(Class, pk=class_id)

    # Make sure the student is enrolled
    if request.user not in class_obj.students.all():
        return HttpResponseForbidden("You are not enrolled in this class.")

    # ✅ Only fetch notifications for the logged-in student
    notifications = StreamNotification.objects.filter(
        user=request.user,   # <-- ito ang filter para hindi sumama iba
        class_obj=class_obj
    ).order_by('-created_at')

    unread_count = notifications.filter(read=False).count()

    return render(request, "students/class_detail.html", {
        "notifications": notifications,
        "unread_count": unread_count,
        "class_obj": class_obj,
    })



from django.utils import timezone

@login_required
def assignment_detail(request, id):
    assignment = get_object_or_404(Assignment, id=id)
    submission = Submission.objects.filter(
        assignment=assignment, student=request.user
    ).first()

    now = timezone.now()
    is_past_due = assignment.due_date and now > assignment.due_date

    if request.method == "POST":
        # Hand-in
        if "hand_in" in request.POST and not is_past_due:
            file = request.FILES.get("file")
            if submission:  # update existing
                submission.file = file
                submission.is_submitted = True
                submission.save()
            else:  # create new
                Submission.objects.create(
                    assignment=assignment,
                    student=request.user,
                    file=file,
                    is_submitted=True,
                )

        # Unsubmit
        elif "unsubmit" in request.POST and submission and not is_past_due:
            submission.is_submitted = False
            submission.file = None  # optional: keep file instead of removing
            submission.save()

        return redirect("students:assignment_detail", id=assignment.id)

    return render(request, "students/assignment_detail.html", {
        "assignment": assignment,
        "submission": submission,
        "is_past_due": is_past_due
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model  # assuming Message model exists

User = get_user_model()

@login_required
def messages_inbox(request):
    user = request.user

    # Determine contacts based on role
    if user.role == 'teacher':
        contacts = User.objects.filter(role__in=['student', 'parent']).exclude(id=user.id)
    elif user.role == 'student':
        contacts = User.objects.filter(role__in=['teacher', 'parent']).exclude(id=user.id)
    elif user.role == 'parent':
        contacts = User.objects.filter(role__in=['teacher', 'student']).exclude(id=user.id)
    else:
        contacts = User.objects.none()  # fallback: no contacts

    context = {
        'contacts': contacts,
        'other_user': None,  # no conversation selected yet
        'messages': [],
        'classes': getattr(user, 'created_classes', Class.objects.none()).all(),
    }
    return render(request, 'students/conversation.html', context)


@login_required
def conversation(request, user_id):
    user = request.user
    other_user = get_object_or_404(User, id=user_id)

    # Fetch all messages between current user and other_user
    messages = Message.objects.filter(
        Q(sender=user, recipient=other_user) |
        Q(sender=other_user, recipient=user)
    ).order_by('timestamp')

    # Determine contacts for sidebar based on role
    if user.role == 'teacher':
        contacts = User.objects.filter(role__in=['student', 'parent']).exclude(id=user.id)
    elif user.role == 'student':
        contacts = User.objects.filter(role__in=['teacher', 'parent']).exclude(id=user.id)
    elif user.role == 'parent':
        contacts = User.objects.filter(role__in=['teacher', 'student']).exclude(id=user.id)
    else:
        contacts = User.objects.none()

    # Handle sending new message
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=user, recipient=other_user, content=content)
            return redirect('students:conversation', user_id=other_user.id)

    context = {
        'contacts': contacts,
        'other_user': other_user,
        'messages': messages,
        'classes': getattr(user, 'created_classes', Class.objects.none()).all(),
    }
    return render(request, 'students/conversation.html', context)

@login_required
def student_grades(request):
    # Get all assignments from classes the student is enrolled in
    assignments = Assignment.objects.filter(class_obj__students=request.user).select_related("class_obj")

    # Build a list of dicts: assignment + submission (if exists)
    work_list = []
    for assignment in assignments:
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
        work_list.append({
            "assignment": assignment,
            "submission": submission,
        })

    return render(request, "students/grades.html", {"work_list": work_list})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from teachers.models import Quiz, Question, Option, StudentAnswer  # adjust import if needed
from .models import StudentQuizAttempt  # import the new model

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # fetch any existing answers by this student for this quiz
    existing_answers_qs = StudentAnswer.objects.filter(
        student=request.user,
        question__quiz=quiz
    ).select_related('selected_option', 'question')

    submitted = existing_answers_qs.exists()

    if request.method == "POST":
        # Prevent double submit
        if submitted:
            messages.info(request, "You already submitted this quiz.")
            return redirect("students:class_detail", id=quiz.class_obj.id)

        # Save answers
        for question in quiz.questions.all():
            field_name = f"question_{question.id}"
            value = request.POST.get(field_name)
            if value is None or value == "":
                continue  # skip unanswered

            if question.question_type == "multiple-choice":
                try:
                    opt = Option.objects.get(id=value, question=question)
                except Option.DoesNotExist:
                    continue
                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={
                        "selected_option": opt,
                        "text_answer": None,
                        "score": 1 if opt.is_correct else 0,
                    }
                )

            elif question.question_type == "identification":
                text = value.strip()
                correct_opt = question.options.filter(is_correct=True).first()
                score = 1 if correct_opt and correct_opt.text.strip().lower() == text.lower() else 0
                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={
                        "text_answer": text,
                        "selected_option": None,
                        "score": score,
                    }
                )

            else:  # essay
                text = value.strip()
                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={
                        "text_answer": text,
                        "selected_option": None,
                        "score": 0,  # teacher will grade later
                    }
                )
        # ✅ Mark quiz as "attempted"
        quiz_attempt, created = StudentQuizAttempt.objects.get_or_create(
            student=request.user,
            quiz=quiz,
            defaults={"status": "completed"}
        )
        if not created:
            quiz_attempt.status = "completed"
            quiz_attempt.save()

        messages.success(request, "Quiz submitted — marked as Turned in.")
        return redirect("students:class_detail", id=quiz.class_obj.id)

    # Prepare pairs (question + possible existing answer) so template can render history
    answers_by_qid = {a.question_id: a for a in existing_answers_qs}
    qa_pairs = [{"question": q, "answer": answers_by_qid.get(q.id)} for q in quiz.questions.all()]

    return render(request, "students/take_quiz.html", {
        "quiz": quiz,
        "submitted": submitted,
        "qa_pairs": qa_pairs,
    })