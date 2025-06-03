from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User, Group
from .models import Profile, Student, Attendance
from .forms import StudentForm, ScanForm
from datetime import timedelta
from django.views.decorators.http import require_POST
from .models import Profile

# Role Selection Page
def role_select_view(request):
    return render(request, 'myapp/role_select.html')

# Adviser Signup  # Make sure you import your Profile model

def adviser_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "myapp/adviser_signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "myapp/adviser_signup.html")

        user = User.objects.create_user(username=username, password=password)
        adviser_group = Group.objects.get(name='adviser')
        user.groups.add(adviser_group)
        Profile.objects.create(user=user, role='adviser')

        messages.success(request, "Adviser account created successfully. Please log in.")
        return redirect('adviser_login')

    return render(request, 'myapp/adviser_signup.html')

# Student Signup
def student_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        student_id = request.POST.get("student_id")
        name = request.POST.get("name")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "myapp/student_signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "myapp/student_signup.html")

        if not student_id:
            messages.error(request, "Student ID is required.")
            return render(request, "myapp/student_signup.html")

        user = User.objects.create_user(username=username, password=password)
        student_group = Group.objects.get(name='student')
        user.groups.add(student_group)
        profile = Profile.objects.create(user=user, role='student')
        Student.objects.create(profile=profile, student_id=student_id, name=name)

        messages.success(request, "Student account created successfully. Please log in.")
        return redirect('student_login')

    return render(request, 'myapp/student_signup.html')

# Login View with role validation
def login_view(request, role=None):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                return render(request, f'myapp/{role}_login.html', {
                    'error': 'Your account is missing a profile. Contact admin.'
                })

            if not role or profile.role == role:
                login(request, user)
                if profile.role == 'adviser':
                    return redirect('adviser_dashboard')
                elif profile.role == 'student':
                    return redirect('student_dashboard')
            else:
                return render(request, f'myapp/{role}_login.html', {
                    'error': f'You are not authorized as {role}.'
                })

        return render(request, f'myapp/{role}_login.html', {'error': 'Invalid credentials'})

    return render(request, f'myapp/{role}_login.html')

# Specific login views for roles
def adviser_login_view(request):
    return login_view(request, role='adviser')

def student_login_view(request):
    return login_view(request, role='student')

# Helper checks
def is_adviser(user):
    return hasattr(user, 'profile') and user.profile.role == 'adviser'

def is_student(user):
    return hasattr(user, 'profile') and user.profile.role == 'student'

# Adviser: Dashboard
@login_required
@user_passes_test(is_adviser)
def adviser_dashboard(request):
    students = Student.objects.all().select_related('profile')
    total_students = students.count()
    today = timezone.now().date()
    todays_attendance_count = Attendance.objects.filter(timestamp__date=today).count()
    recent_date = today - timedelta(days=3)
    recent_checkins_count = Attendance.objects.filter(timestamp__date__gte=recent_date).count()

    chart_labels = []
    chart_data = []
    for i in range(4, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        count = Attendance.objects.filter(timestamp__date=day).count()
        chart_data.append(count)

    context = {
        'students': students,
        'total_students': total_students,
        'todays_attendance_count': todays_attendance_count,
        'recent_checkins_count': recent_checkins_count,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }

    return render(request, 'myapp/adviser_dashboard.html', context)

# Adviser: Student List
@login_required
@user_passes_test(is_adviser)
def my_students(request):
    students = Student.objects.all()
    return render(request, 'adviser/my_students.html', {'students': students})

# Student Dashboard (Only shows present students)
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    profile = request.user.profile
    if profile.role != 'student':
        return render(request, 'unauthorized.html')

    student = profile.student
    today = timezone.now().date()

    # Get all attendance records for today
    attendance_records_today = Attendance.objects.filter(timestamp__date=today).select_related('student')

    # Prepare the list of students present today
    student_ids_present = attendance_records_today.values_list('student_id', flat=True).distinct()
    present_students_today = Student.objects.filter(id__in=student_ids_present).prefetch_related('attendance_set')

    # Format the current student's attendance for today (optional)
    attendance_data = [
        {
            'name': record.student.name,
            'student_id': record.student.student_id,
            'time': record.timestamp.strftime('%I:%M %p'),
            'date': record.timestamp.date().strftime('%Y-%m-%d'),
            'present': record.present,
        }
        for record in attendance_records_today if record.student == student
    ]

    context = {
        'student': student,
        'attendance_data': attendance_data,
        'present_students_today': present_students_today,
        'today': today,
    }

    return render(request, 'myapp/student_dashboard.html', context)

# Logout
def logout_view(request):
    logout(request)
    return redirect('role_select')

# Adviser: Barcode Scan
@login_required
@user_passes_test(is_adviser)
def scan_barcode(request):
    message = ""
    if request.method == 'POST':
        form = ScanForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode']
            try:
                student = Student.objects.get(student_id=barcode)
                Attendance.objects.create(student=student, timestamp=timezone.now(), present=True)
                message = f"✅ Attendance recorded for {student.name}"
            except Student.DoesNotExist:
                message = "❌ Student not found!"
    else:
        form = ScanForm()
    return render(request, 'myapp/scan.html', {'form': form, 'message': message})

# Adviser: Barcode scan via POST
@require_POST
def adviser_scan_barcode(request):
    barcode = request.POST.get('barcode', '').strip()
    if not barcode:
        messages.error(request, "No barcode scanned.")
        return redirect('adviser_dashboard')

    try:
        student = Student.objects.get(student_id=barcode)
    except Student.DoesNotExist:
        messages.error(request, "Student with that barcode not found.")
        return redirect('adviser_dashboard')

    today = timezone.now().date()
    attendance, created = Attendance.objects.get_or_create(
        student=student,
        timestamp__date=today,
        defaults={'present': True, 'timestamp': timezone.now()}
    )

    if not created:
        messages.info(request, f"{student.name} has already been marked present today.")
    else:
        messages.success(request, f"Attendance recorded for {student.name}.")

    return redirect('adviser_dashboard')

# Adviser: Create student
@login_required
@user_passes_test(is_adviser)
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect('adviser_dashboard')
    else:
        form = StudentForm()
    return render(request, 'myapp/student_form.html', {'form': form, 'title': 'Add Student'})

# Adviser: Update student
@login_required
@user_passes_test(is_adviser)
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect('adviser_dashboard')
    else:
        form = StudentForm(instance=student)
    return render(request, 'myapp/student_form.html', {'form': form, 'title': 'Edit Student'})


@login_required
def student_delete(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.delete()
        return redirect('adviser_dashboard')  # Change this if your list view uses a different name
    return render(request, 'myapp/student_confirm_delete.html', {'student': student})


# Placeholder enrollment page
def enroll_student(request):
    return render(request, 'myapp/enroll.html')
