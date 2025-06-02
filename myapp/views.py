from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User, Group
from .models import Profile, Student, Attendance
from .forms import StudentForm, ScanForm
from datetime import timedelta


# Role Selection Page
def role_select_view(request):
    return render(request, 'myapp/role_select.html')


# Adviser Signup
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


# Check if user is adviser helper function
def is_adviser(user):
    return hasattr(user, 'profile') and user.profile.role == 'adviser'


# Check if user is student helper function
def is_student(user):
    return hasattr(user, 'profile') and user.profile.role == 'student'


# Adviser: List all students
@login_required
@user_passes_test(is_adviser)
def my_students(request):
    students = Student.objects.all()
    return render(request, 'adviser/my_students.html', {'students': students})



def is_adviser(user):
    return hasattr(user, 'profile') and user.profile.role == 'adviser'

@login_required
@user_passes_test(is_adviser)
def adviser_dashboard(request):
    # Get all students with their profiles (to minimize DB queries)
    students = Student.objects.all().select_related('profile')
    
    total_students = students.count()

    # Today's date
    today = timezone.now().date()

    # Count how many attendance records were logged today
    todays_attendance_count = Attendance.objects.filter(timestamp__date=today).count()

    # Define 'recent' as the last 3 days (can be adjusted)
    recent_days = 3
    recent_date = today - timedelta(days=recent_days)
    recent_checkins_count = Attendance.objects.filter(timestamp__date__gte=recent_date).count()

    # Prepare chart data for the last 5 days (labels and counts)
    chart_labels = []
    chart_data = []
    for i in range(4, -1, -1):  # From 4 days ago to today
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))  # e.g., 'Mon', 'Tue'
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

# Student Dashboard
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    try:
        student = Student.objects.get(profile__user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('role_select')

    all_attendance = Attendance.objects.filter(student=student)

    attendance_records = all_attendance.order_by('-timestamp')[:10]

    total_days = 30  # Define as needed
    attended_days = all_attendance.filter(present=True).count()
    attendance_percentage = (attended_days / total_days) * 100 if total_days else 0

    today = timezone.now().date()
    todays_attendance = all_attendance.filter(timestamp__date=today).first()
    is_present_today = todays_attendance.present if todays_attendance else False

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'attendance_percentage': attendance_percentage,
        'is_present_today': is_present_today,
        'todays_attendance': todays_attendance,
    }
    return render(request, 'myapp/student_dashboard.html', context)


# Logout
def logout_view(request):
    logout(request)
    return redirect('role_select')


# Barcode scan page, adviser only
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


# Create Student (adviser only)
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


# Update Student (adviser only)
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


# Delete Student (adviser only) with confirmation
@login_required
@user_passes_test(is_adviser)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect('adviser_dashboard')
    return render(request, 'myapp/student_confirm_delete.html', {'student': student})


# Enrollment page placeholder
def enroll_student(request):
    return render(request, 'myapp/enroll.html')
