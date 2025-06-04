from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# User Profile with Role
class Profile(models.Model):
    ROLE_CHOICES = (
        ('adviser', 'Adviser'),
        ('student', 'Student'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Student Model
class Student(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, unique=True)


    def __str__(self):
        return f"{self.name} ({self.student_id})"

# Attendance Model
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    present = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
