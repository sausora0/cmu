from django.shortcuts import render, redirect
from django.shortcuts import render
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Class
from django.shortcuts import render, redirect, get_object_or_404
from .models import Class, Assignment, Event, Submission
from .forms import AssignmentForm, SubmissionForm, EventForm
import csv
import io
from django.http import HttpResponse
from django.contrib.auth import get_user_model

User = get_user_model()
@login_required
def teacherdashboard(request):
    classes = Class.objects.filter(teacher=request.user, is_archived=False)
    return render(request, 'teachers/dashboard.html', {
        'classes': classes,
        'class_count': classes.count()
    })

@login_required
def message(request):
    return render(request, "teachers/messages.html")

@login_required
def calendar(request):
    events = Event.objects.all().order_by("date")  # all events (teachers, students, parents see same list)
    classes = Class.objects.filter(teacher=request.user, is_archived=False)
    
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect("teachers:calendar")
    else:
        form = EventForm()

    return render(request, "teachers/calendar.html", {
        "events": events,
        "form": form,
        'classes': classes,
        'class_count': classes.count()
    })

@login_required
def announcement(request):
    return render(request, 'teachers/announcement.html')


from django.db.models import Avg
from django.db.models import Count, Q, F, ExpressionWrapper, IntegerField

from django.db.models import Count, Q, F, IntegerField, ExpressionWrapper

@login_required
def subject(request, id):
    class_obj = get_object_or_404(Class, pk=id)
    notifications = StreamNotification.objects.filter(
        user=request.user,
        class_obj=class_obj
    ).order_by('-created_at')
    unread_count = class_obj.notifications.filter(read=False).count()

    is_teacher = class_obj.teacher == request.user
    classes = Class.objects.filter(teacher=request.user, is_archived=False)

    # === Quizzes with Turned in / Missing / Assigned ===
    quizzes = (
        Quiz.objects.filter(class_obj=class_obj)
        .annotate(
            turned_in=Count("attempts", filter=Q(attempts__status="completed"), distinct=True),
            assigned=Count("class_obj__students", distinct=True),
        )
        .annotate(
            missing=ExpressionWrapper(
                F("assigned") - F("turned_in"),
                output_field=IntegerField()
            )
        )
        .order_by("-created_at")
    )

    # === Assignments with Turned in / Missing / Assigned ===
    assignments = (
        Assignment.objects.filter(class_obj=class_obj)
        .annotate(
            turned_in=Count("submissions", filter=Q(submissions__file__isnull=False), distinct=True),
            assigned=Count("class_obj__students", distinct=True),
        )
        .annotate(
            missing=ExpressionWrapper(
                F("assigned") - F("turned_in"),
                output_field=IntegerField()
            )
        )
        .order_by("-created_at")
    )

    gradebook = []
    assignment_averages = {}

    if is_teacher:
        students = class_obj.students.all()
        for student in students:
            row = {"student": student, "grades": [], "average": None}
            total = 0
            count = 0

            for assignment in assignments:
                submission = Submission.objects.filter(student=student, assignment=assignment).first()
                grade = submission.grade if submission else None
                published = submission.is_published if submission else False

                row["grades"].append({
                    "assignment": assignment,
                    "grade": grade,
                    "is_published": published,
                    "submission": submission
                })

                if grade is not None:
                    total += grade
                    count += 1
                    assignment_averages.setdefault(assignment.id, []).append(grade)

            row["average"] = round(total / count, 2) if count > 0 else None
            gradebook.append(row)

        # Assignment averages
        for assignment in assignments:
            avg = Submission.objects.filter(assignment=assignment, grade__isnull=False).aggregate(Avg("grade"))["grade__avg"]
            assignment_averages[assignment.id] = round(avg, 2) if avg else None

    if request.method == "POST":
        if request.FILES.get("banner"):
            class_obj.banner = request.FILES["banner"]
            class_obj.theme = None
            class_obj.save()
        elif request.POST.get("theme"):
            class_obj.theme = request.POST["theme"]
            class_obj.banner = None
            class_obj.save()

        return redirect("teachers:subject", id=class_obj.pk)

    return render(request, 'teachers/subject.html', {
        'class_obj': class_obj,
        'assignments': assignments,
        'classes': classes,
        'class_count': classes.count(),
        'gradebook': gradebook if is_teacher else None,
        'assignment_averages': assignment_averages if is_teacher else None,
        'is_teacher': is_teacher,
        "unread_count": unread_count,
        "notifications": notifications,
        "quizzes": quizzes,
    })

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def update_grade(request, class_id, submission_id):
    class_obj = get_object_or_404(Class, pk=class_id, teacher=request.user)
    submission = get_object_or_404(Submission, pk=submission_id, assignment__class_obj=class_obj)

    try:
        grade_val = request.POST.get("grade")
        grade = float(grade_val) if grade_val != "" else None
    except ValueError:
        return JsonResponse({"error": "Invalid grade"}, status=400)

    submission.grade = grade
    submission.save()

    # Recompute averages
    student_avg = Submission.objects.filter(
        student=submission.student, assignment__class_obj=class_obj, grade__isnull=False
    ).aggregate(Avg("grade"))["grade__avg"]

    assignment_avg = Submission.objects.filter(
        assignment=submission.assignment, grade__isnull=False
    ).aggregate(Avg("grade"))["grade__avg"]

    return JsonResponse({
        "success": True,
        "grade": submission.grade,
        "student_id": submission.student.id,
        "assignment_id": submission.assignment.id,
        "student_avg": round(student_avg, 2) if student_avg else None,
        "assignment_avg": round(assignment_avg, 2) if assignment_avg else None,
    })


@login_required
def assignment_form(request, id):
    class_obj = get_object_or_404(Class, id=id)
    classes = Class.objects.filter(teacher=request.user, is_archived=False)

    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.class_obj = class_obj
            assignment.save()
            form.save_m2m()

            # ✅ Notification for teacher
            StreamNotification.objects.create(
            user=request.user,
            class_obj=class_obj,
            assignment=assignment,
            message=f"{request.user.get_full_name()} posted a new assignment: {assignment.title}"
        )

        messages.success(request, "Assignment created and notifications sent!")

        return redirect("teachers:subject", id=class_obj.id)
    else:
        form = AssignmentForm()

    return render(request, "teachers/assignment_form.html", {
        "form": form,
        "class_obj": class_obj,
        "classes": classes,
        "students": class_obj.students.all(),
    })



@login_required
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Optional: check if the logged-in user is the teacher of this class
    if assignment.class_obj.teacher != request.user:
        messages.error(request, "You are not allowed to delete this assignment.")
        return redirect("teachers:subject", id=assignment.class_obj.id)

    assignment.delete()
    messages.success(request, "Assignment deleted successfully.")
    return redirect("teachers:subject", id=assignment.class_obj.id)

@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user  # because students are also AUTH_USER_MODEL
            submission.save()
            return redirect("class_detail", id=assignment.class_obj.id)
    else:
        form = SubmissionForm()
    return render(request, "students/submit_assignment.html", {"form": form, "assignment": assignment})

from django.utils import timezone

@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Check if logged in user is the teacher of the class
    is_teacher = assignment.class_obj.teacher == request.user  

     # check due date
    is_past_due = False
    if assignment.due_date and timezone.now() > assignment.due_date:
        is_past_due = True
        
     # --- Handle POST actions ---
    if request.method == "POST":
        action = request.POST.get("action")
        submission_id = request.POST.get("submission_id")
        student_id = request.POST.get("student_id")  # used for not_turned_in students

        # Return with grade
        if action == "return" and submission_id:
            sub = get_object_or_404(Submission, id=submission_id, assignment=assignment)
            grade = request.POST.get("grade")
            feedback = request.POST.get("feedback", "")
            try:
                sub.grade = int(grade)
                sub.feedback = feedback
                sub.returned = True
                sub.save()
                messages.success(request, f"Returned work to {sub.student.get_full_name()} with grade {grade}.")
            except ValueError:
                messages.error(request, "Invalid grade entered.")
            return redirect("teachers:assignment_detail", assignment_id=assignment.id)


    # Student-side: get their own submission
    student_submission = None
    if not is_teacher:
        student_submission = Submission.objects.filter(
            assignment=assignment, student=request.user
        ).first()

    # Teacher-side: get all enrolled students & submissions
    submissions = []
    not_turned_in = []
    turned_in_count = 0
    assigned_count = 0

    if is_teacher:
        # All enrolled students
        enrolled_students = assignment.class_obj.students.all()

        # All submissions
        submissions = Submission.objects.filter(assignment=assignment).select_related("student")

        # Students who submitted
        submitted_students = submissions.values_list("student_id", flat=True)

        # Students who did NOT submit
        not_turned_in = enrolled_students.exclude(id__in=submitted_students)

        # Stats
        turned_in_count = submissions.count()
        assigned_count = enrolled_students.count() - turned_in_count

    context = {
        "assignment": assignment,
        "is_teacher": is_teacher,
        "student_submission": student_submission,
        "submissions": submissions,
        "not_turned_in": not_turned_in,
        "turned_in_count": turned_in_count,
        "assigned_count": assigned_count,
        "is_past_due": is_past_due,
    }
    return render(request, "teachers/assignment_detail.html", context)


@csrf_exempt
@login_required
def create_class(request):
    if request.method == "POST":
        class_name = request.POST.get("class_name")
        subject_name = request.POST.get("subject_name")
        section = request.POST.get("section")
        time = request.POST.get("time")
        new_class = Class.objects.create(
            class_name=class_name,
            subject_name=subject_name, 
            section=section, 
            time=time, 
            teacher=request.user
        )
         # Step 2: create GDrive folder
        creds_data = request.session.get("google_credentials")
        if creds_data:
            creds = Credentials.from_authorized_user_info(creds_data)
            folder_id = create_drive_folder(new_class.class_name, creds)
            new_class.gdrive_folder_id = folder_id
            new_class.save()

        messages.success(request, f"Class Name '{new_class.class_name}' created! Code: {new_class.code}")
        return redirect("teachers:dashboard")
    
from django.shortcuts import redirect, get_object_or_404
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .models import Class

def create_drive_folder(folder_name, creds):
    service = build("drive", "v3", credentials=creds)
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

@login_required
def open_or_create_drive_folder(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)

    # If already has a folder → redirect directly
    if class_obj.gdrive_folder_id:
        return redirect(f"https://drive.google.com/drive/folders/{class_obj.gdrive_folder_id}")

    # Otherwise → create a new folder
    creds_data = request.session.get("google_credentials")
    if not creds_data:
        messages.error(request, "Google Drive not connected yet.")
        return redirect("teachers:dashboard")

    creds = Credentials.from_authorized_user_info(creds_data)
    folder_id = create_drive_folder(class_obj.class_name, creds)
    class_obj.gdrive_folder_id = folder_id
    class_obj.save()

    return redirect(f"https://drive.google.com/drive/folders/{folder_id}")



@login_required 
def archive_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    if request.method == "POST":
        class_obj.is_archived = True
        class_obj.save()
        return redirect("teachers:archived_classes")
    return redirect("teachers:dashboard")

@login_required
def restore_archived_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    if request.method == "POST":
        class_obj.is_archived = False
        class_obj.save()
    return redirect("teachers:archived_classes")

@login_required
def archived_classes(request):
    archived = Class.objects.filter(teacher=request.user, is_archived=True)
    classes = Class.objects.filter(teacher=request.user)
    return render(request, "teachers/archive_classes.html", {"classes": archived, 'all_classes': classes, 'class_count': classes.count()})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import AnnouncementForm
from .models import Announcement

@login_required
def announcement_list(request):
    announcements = Announcement.objects.all().order_by('-date_posted')
    classes = Class.objects.filter(teacher=request.user, is_archived=False)
    # filters
    search_query = request.GET.get("search")
    category = request.GET.get("category")
    priority = request.GET.get("priority")
    sort = request.GET.get("sort")

    if search_query:
        announcements = announcements.filter(title__icontains=search_query) | announcements.filter(content__icontains=search_query)
    if category:
        announcements = announcements.filter(category=category)
    if priority:
        announcements = announcements.filter(priority=priority)
    if sort == "oldest":
        announcements = announcements.order_by("date_posted")

    # only teachers can add announcements
    form = None
    if hasattr(request.user, "role") and request.user.role in ["teacher", "school_admin"]:
        if request.method == "POST":
            form = AnnouncementForm(request.POST)
            if form.is_valid():
                ann = form.save(commit=False)
                ann.author = request.user
                ann.save()
                return redirect("teachers:announcement_list")
        else:
            form = AnnouncementForm()

    return render(request, "teachers/announcement.html", {
        "announcements": announcements,
        "form": form,
        'classes': classes,
        'class_count': classes.count()
    })


@login_required
def announcement_detail(request, id):
    ann = get_object_or_404(Announcement, id=id)
    return render(request, "teachers/announcement_detail.html", {"announcement": ann})
from django.http import HttpResponseForbidden

@login_required
def announcement_edit(request, id):
    ann = get_object_or_404(Announcement, id=id)

    # only the author (teacher) or an admin can edit
    if not hasattr(request.user, "role") or (request.user != ann.author and request.user.role != "school_admin"):
        return HttpResponseForbidden("You are not allowed to edit this announcement.")

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=ann)
        if form.is_valid():
            form.save()
            return redirect("teachers:announcement_list")
    else:
        form = AnnouncementForm(instance=ann)

    return render(request, "teachers/announcement_form.html", {"form": form, "announcement": ann})


@login_required
def announcement_delete(request, id):
    ann = get_object_or_404(Announcement, id=id)

    # only the author (teacher) or an admin can delete
    if not hasattr(request.user, "role") or (request.user != ann.author and request.user.role != "school_admin"):
        return HttpResponseForbidden("You are not allowed to delete this announcement.")

    if request.method == "POST":
        ann.delete()
        return redirect("teachers:announcement_list")

    return render(request, "teachers/announcement_confirm_delete.html", {"announcement": ann})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Class  # change to your actual model name

def edit_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    if request.method == "POST":
        class_obj.class_name = request.POST.get("class_name")
        class_obj.subject_name = request.POST.get("subject_name")
        class_obj.section = request.POST.get("section")
        class_obj.time = request.POST.get("time")
        class_obj.save()
        messages.success(request, "Class updated successfully!")
        return redirect("teachers:dashboard")  # change to your page


@login_required
def class_grades(request, class_id):
    # Ensure only class teacher may access
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    students = class_obj.students.all().order_by('last_name', 'first_name')
    assignments = class_obj.assignments.all().order_by('created_at')

    # Build gradebook: ensure there's a Submission object for each student/assignment
    gradebook = []
    assignment_averages = {a.id: {"total": 0.0, "count": 0} for a in assignments}

    # Handle form POST (update grades/publish flags / bulk action)
    if request.method == "POST":
        # Bulk action: set all missing to 0
        if "bulk_zero" in request.POST:
            # set grade = 0 for all submissions that are missing (no file and no grade)
            for assignment in assignments:
                missing_subs = Submission.objects.filter(
                    assignment=assignment, file__isnull=True, grade__isnull=True
                )
                for s in missing_subs:
                    s.grade = 0
                    s.is_published = False  # default: keep unpublished until teacher publishes
                    s.save()
            messages.success(request, "All missing submissions set to 0 (draft).")
            return redirect("teachers:class_grades", class_id=class_id)

        # Save edits (grades + publish checkboxes) across the whole table
        # Form fields are: grade_<submission_id>, publish_<submission_id>
        for key, value in request.POST.items():
            if key.startswith("grade_"):
                try:
                    sub_id = int(key.split("_", 1)[1])
                    sub = Submission.objects.filter(id=sub_id).first()
                    if not sub:
                        continue
                    # parse grade (allow blank to clear)
                    grade_val = value.strip()
                    if grade_val == "":
                        sub.grade = None
                    else:
                        try:
                            sub.grade = float(grade_val)
                        except ValueError:
                            # invalid grade - skip or set message
                            continue
                    sub.save()
                except Exception:
                    continue

        # Now handle publish checkboxes
        # For each submission, if publish_<id> in POST --> True, else False
        all_submission_ids = Submission.objects.filter(assignment__class_obj=class_obj).values_list('id', flat=True)
        for sid in all_submission_ids:
            publish_key = f"publish_{sid}"
            sub = Submission.objects.filter(id=sid).first()
            if not sub:
                continue
            sub.is_published = (publish_key in request.POST)
            sub.save()

        messages.success(request, "Grades updated.")
        return redirect("teachers:class_grades", class_id=class_id)

    # GET: Build the gradebook structure for template
    for student in students:
        row = {"student": student, "grades": [], "average": None}
        total = 0.0
        count = 0
        for assignment in assignments:
            sub, created = Submission.objects.get_or_create(assignment=assignment, student=student)
            g = sub.grade
            row["grades"].append({"submission": sub, "grade": g})
            if g is not None:
                total += float(g)
                count += 1
                assignment_averages[assignment.id]["total"] += float(g)
                assignment_averages[assignment.id]["count"] += 1
        row["average"] = round(total / count, 2) if count > 0 else None
        gradebook.append(row)

    # finalize assignment averages
    for a_id, d in assignment_averages.items():
        if d["count"] > 0:
            d["average"] = round(d["total"] / d["count"], 2)
        else:
            d["average"] = None

    context = {
        "class_obj": class_obj,
        "assignments": assignments,
        "gradebook": gradebook,
        "assignment_averages": assignment_averages,
    }
    return render(request, "teachers/class_grades.html", context)


@login_required
def export_grades(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    assignments = class_obj.assignments.all().order_by('created_at')
    students = class_obj.students.all().order_by('last_name', 'first_name')

    # Prepare CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{class_obj.class_name}_grades.csv"'
    writer = csv.writer(response)

    header = ["Student Email", "Student Name"] + [a.title for a in assignments]
    writer.writerow(header)

    for student in students:
        row = [student.email, student.get_full_name()]
        for a in assignments:
            sub = Submission.objects.filter(assignment=a, student=student).first()
            row.append(sub.grade if sub and sub.grade is not None else "")
        writer.writerow(row)

    return response


@login_required
def import_grades(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    assignments = {a.title: a for a in class_obj.assignments.all()}

    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]
        try:
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
        except Exception as e:
            messages.error(request, "Could not read CSV file.")
            return redirect("teachers:class_grades", class_id=class_id)

        updated = 0
        skipped = 0
        for row in reader:
            # Expecting first columns to be "Student Email" and/or "Student Name"
            email = row.get("Student Email") or row.get("student_email") or row.get("Email")
            name = row.get("Student Name") or row.get("student_name") or row.get("Name")

            student = None
            if email:
                student = User.objects.filter(email=email.strip()).first()
            if not student and name:
                # fallback search by full name
                parts = name.strip().split()
                if len(parts) >= 2:
                    # try by first and last
                    student = User.objects.filter(first_name__iexact=parts[0], last_name__iexact=parts[-1]).first()
                else:
                    student = User.objects.filter(first_name__iexact=name.strip()).first()

            if not student:
                skipped += 1
                continue

            # For each assignment column in row, update grade
            for col, val in row.items():
                if col in ("Student Email", "student_email", "Email", "Student Name", "student_name", "Name"):
                    continue
                # match assignment by title exactly
                assignment = assignments.get(col)
                if not assignment:
                    continue
                # parse grade
                if val is None or val == "":
                    continue
                try:
                    grade_val = float(val)
                except ValueError:
                    continue
                sub, _ = Submission.objects.get_or_create(assignment=assignment, student=student)
                sub.grade = grade_val
                # imported grades are saved as drafts (not published) by default
                sub.is_published = False
                sub.save()
                updated += 1

        messages.success(request, f"Imported grades: {updated} values; skipped {skipped} students/rows.")
        return redirect("teachers:class_grades", class_id=class_id)

    messages.error(request, "No file uploaded.")
    return redirect("teachers:class_grades", class_id=class_id)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Message, Class  # assuming Message model exists

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
    return render(request, 'teachers/conversation.html', context)


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
            return redirect('teachers:conversation', user_id=other_user.id)

    context = {
        'contacts': contacts,
        'other_user': other_user,
        'messages': messages,
        'classes': getattr(user, 'created_classes', Class.objects.none()).all(),
    }
    return render(request, 'teachers/conversation.html', context)

from .models import StreamNotification

@login_required
def notification_redirect(request, notification_id):
    notif = get_object_or_404(StreamNotification, id=notification_id)

    # Mark as read
    if not notif.read:
        notif.read = True
        notif.save()

    # Redirect to assignment detail
    if notif.assignment:
        return redirect('teachers:assignment_detail', assignment_id=notif.assignment_id)

    # Fallback
    return redirect('teachers:subject', id=notif.class_obj.id)

from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

@login_required
def clear_notifications(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    class_obj.notifications.all().delete()  # ✅ Delete all linked to this class
    messages.success(request, "All notifications have been cleared.")
    return redirect(reverse('teachers:subject', args=[class_id]))

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
import json

@login_required
@require_POST
def bulk_return_submissions(request):
    import json
    data = json.loads(request.body.decode("utf-8"))
    student_ids = data.get("student_ids", [])
    assignment_id = data.get("assignment_id")

    submissions = Submission.objects.filter(
        assignment_id=assignment_id,
        student_id__in=student_ids
    ).select_related("student", "assignment", "assignment__class_obj")

    updated = []
    notifications = []

    for sub in submissions:
        sub.is_returned = True
        sub.save()

        # Only notify if a grade exists
        if sub.grade is not None:
            # Prepare notification
            message = f"{request.user.get_full_name()} returned your assignment '{sub.assignment.title}' with grade: {sub.grade}/{sub.assignment.points}."
            
            notif = StreamNotification(
                user=sub.student,
                assignment=sub.assignment,
                class_obj=sub.assignment.class_obj,
                message=message
            )
            notifications.append(notif)

        updated.append({
            "id": sub.id,
            "student_id": sub.student.id,
            "student_name": sub.student.get_full_name(),
            "grade": sub.grade,
        })

    # Create all notifications at once (bulk_create is more efficient)
    if notifications:
        StreamNotification.objects.bulk_create(notifications)

    return JsonResponse({"success": True, "updated": updated})

# teachers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Class, Quiz, Question, Option, StudentAnswer

@login_required
def create_quiz(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)

    if request.method == "POST":
        quiz_type = request.POST.get("quiz_type", "quiz")
        quiz_title = request.POST.get("title", "Quiz")  

        # ✅ Create the quiz
        quiz = Quiz.objects.create(
            class_obj=class_obj,
            title=quiz_title,
            quiz_type=quiz_type,
            created_by=request.user
        )

        # ✅ Loop through questions dynamically
        index = 1
        while f"question_text_{index}" in request.POST:
            q_text = request.POST.get(f"question_text_{index}")
            q_type = request.POST.get(f"question_type_{index}")

            if not q_text:
                index += 1
                continue

            # Save Question
            question = Question.objects.create(
                quiz=quiz,
                text=q_text,
                question_type=q_type
            )

            # Multiple choice
            if q_type == "multiple-choice":
                correct_option = request.POST.get(f"correct_option_{index}")
                option_index = 0
                while f"option_{index}_{option_index}" in request.POST:
                    o_text = request.POST.get(f"option_{index}_{option_index}")
                    Option.objects.create(
                        question=question,
                        text=o_text,
                        is_correct=(str(option_index) == correct_option)
                    )
                    option_index += 1

            # Identification
            elif q_type == "identification":
                correct_answer = request.POST.get(f"answer_{index}")
                if correct_answer:
                    Option.objects.create(
                        question=question,
                        text=correct_answer,
                        is_correct=True
                    )

            # Essay → nothing to save as Option
            elif q_type == "essay":
                pass  

            index += 1

        messages.success(request, "Quiz created successfully!")
        return redirect("teachers:subject", id=class_obj.id)

    return render(request, "teachers/quiz.html", {"class_obj": class_obj})

@login_required
def grade_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    answers = StudentAnswer.objects.filter(question__quiz=quiz).select_related("student", "question")

    if request.method == "POST":
        for ans in answers:
            score = request.POST.get(f"score_{ans.id}")
            if score is not None:
                ans.score = float(score)
                ans.save()
        messages.success(request, "Scores updated successfully!")
        return redirect("teachers:subject", class_id=quiz.class_obj.id)

    return render(request, "grade_quiz.html", {"quiz": quiz, "answers": answers})

from students.models import StudentQuizAttempt

@login_required
def quiz_detail(request, class_id, quiz_id):
    class_obj = get_object_or_404(Class, pk=class_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, class_obj=class_obj)

    # All students in this class
    students = class_obj.students.all()

    # Students who submitted (turned in)
    turned_in_attempts = StudentQuizAttempt.objects.filter(
        quiz=quiz, status="completed"
    ).select_related("student")

    turned_in_students = [a.student for a in turned_in_attempts]

    # Students who did not submit (missing)
    missing_students = students.exclude(id__in=[s.id for s in turned_in_students])

    # Preload answers into a dict {(student_id, question_id): answer}
    answers = {}
    student_answers = StudentAnswer.objects.filter(
        student__in=turned_in_students, question__quiz=quiz
    )
    for ans in student_answers:
        answers[(ans.student_id, ans.question_id)] = ans

    # If teacher is grading a student’s answer
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        question_id = request.POST.get("question_id")
        score = request.POST.get("score")

        if student_id and question_id:
            answer = answers.get((int(student_id), int(question_id)))
            if answer:
                answer.score = int(score)
                answer.save()
                messages.success(request, "Score saved successfully.")

        return redirect("teachers:quiz_detail", class_id=class_obj.id, quiz_id=quiz.id)

    return render(request, "teachers/quiz_detail.html", {
        "class_obj": class_obj,
        "quiz": quiz,
        "turned_in_attempts": turned_in_attempts,
        "missing_students": missing_students,
        "answers": answers,  # pass dict to template
    })

# teachers/views.py
from django.shortcuts import render, get_object_or_404

def student_detail(request, user_id):
    student = get_object_or_404(User, id=user_id)
    invites = student.parent_invites.all()  # if you added related_name="parent_invites"
    return render(request, "teachers/student_detail.html", {
        "student": student,
        "invites": invites
    })

from utils.gmail_oauth import send_oauth_email
from .models import ParentInvite,Parent

def invite_parent(request, user_id):
    if request.method == "POST":
        parent_email = request.POST["parent_email"]
        student = get_object_or_404(User, id=user_id)
        teacher = request.user

        invite = ParentInvite.objects.create(
            student=student,
            parent_email=parent_email,
            invited_by=teacher
        )

        accept_url = request.build_absolute_uri(
            reverse("teachers:accept_parent_invite", args=[invite.id])
        )

        subject = f"Parent Access Invitation for {student.get_full_name()}"
        text_content = (
            f"You have been invited by {teacher.get_full_name()} to view "
            f"{student.get_full_name()}'s academic progress.\n\nAccept here: {accept_url}"
        )

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Hello!</h2>
            <p>You have been invited by <strong>{teacher.get_full_name()}</strong> 
               to view <strong>{student.get_full_name()}</strong>'s academic progress.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{accept_url}" 
                   style="background-color: #0d6efd; color: white; padding: 12px 25px;
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                   Accept Invitation
                </a>
            </p>
            <p>If the button doesn’t work, copy and paste this URL into your browser:</p>
            <p><a href="{accept_url}">{accept_url}</a></p>
            <p>Thank you!</p>
        </body>
        </html>
        """

        # ✅ Send using OAuth2 instead of Django backend
        send_oauth_email(
            to_email=parent_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            reply_to=teacher.email,
        )

        return redirect("teachers:student_detail", user_id=student.id)
    
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from teachers.models import ParentInvite, Parent
from utils.gmail_oauth import send_oauth_email

def accept_parent_invite(request, invite_id):
    invite = get_object_or_404(ParentInvite, id=invite_id)

    # Ensure logged-in parent email matches
    if request.user.email.lower() != invite.parent_email.lower():
        return HttpResponse("This Google account does not match the invited email.")

    # 🔹 Force parent role if not already
    if request.user.role != "parent":
        request.user.role = "parent"
        request.user.save()

    # 🔹 Create or get Parent profile
    parent, created = Parent.objects.get_or_create(user=request.user)

    # 🔹 Link the student (prevent duplicates)
    parent.children.add(invite.student)
    parent.save()

    # 🔹 Mark invite as accepted
    invite.accepted = True
    invite.save()

    # Debugging (you’ll see this in your terminal logs)
    print(f"✅ Parent linked: {request.user.email} -> {invite.student.username}")
    print(f"Children now: {[c.username for c in parent.children.all()]}")

    # ✅ Send confirmation email
    subject = "Parent Access Confirmed"
    text_content = (
        f"Hello {request.user.get_full_name()},\n\n"
        f"You have successfully accepted the invitation to monitor {invite.student.get_full_name()}'s "
        f"academic progress in the CMU LMS.\n\n"
        "You can now log in anytime to track updates.\n\nThank you!"
    )

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Access Confirmed 🎉</h2>
        <p>Hello <strong>{request.user.get_full_name()}</strong>,</p>
        <p>You have successfully accepted the invitation to monitor 
           <strong>{invite.student.get_full_name()}</strong>'s academic progress in the <strong>CMU LMS</strong>.</p>
        <p>You can now log in anytime to track updates and progress reports.</p>
        <p style="margin-top:20px;">Thank you!</p>
    </body>
    </html>
    """

    send_oauth_email(
        to_email=invite.parent_email,
        subject=subject,
        text_content=text_content,
        html_content=html_content,
    )

    return redirect("parent_dashboard")

import os
from django.shortcuts import redirect
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# scopes: full drive access
SCOPES = ["https://www.googleapis.com/auth/drive"]

def google_authorize(request):
    flow = Flow.from_client_secrets_file(
        os.path.join(settings.BASE_DIR, "google_credentials.json"),
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri("/oauth2callback/"),
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    request.session["state"] = state
    return redirect(authorization_url)


def google_oauth2_callback(request):
    state = request.session.get("state")
    flow = Flow.from_client_secrets_file(
        os.path.join(settings.BASE_DIR, "google_credentials.json"),
        scopes=SCOPES,
        state=state,
        redirect_uri=request.build_absolute_uri("/oauth2callback/"),
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    creds = flow.credentials
    # save credentials in session
    request.session["google_credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    return redirect("dashboard")

