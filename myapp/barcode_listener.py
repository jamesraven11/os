import os
import sys
import django
from datetime import timedelta
from django.utils import timezone
from evdev import InputDevice, categorize, ecodes



# Add Django project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Now you can import Django models
from myapp.models import Student, Attendance  # Adjust if needed
def mark_attendance(student_id):
    try:
        student = Student.objects.get(student_id=student_id)
        now = timezone.now()

        already_marked = Attendance.objects.filter(
            student=student,
            timestamp__date=now.date()
        ).exists()

        if not already_marked:
            Attendance.objects.create(student=student, timestamp=now)
            print(f"✅ Attendance marked for {student.full_name} ({student.student_id})")
        else:
            print(f"ℹ️ Attendance already marked today for {student.full_name}")
    except Student.DoesNotExist:
        print(f"❌ No student found with ID: {student_id}")


# Setup barcode scanner
device = InputDevice('/dev/input/event2')  # Adjust based on your Orange Pi's event number
barcode = ''
print("Waiting for barcode scan...")

for event in device.read_loop():
    if event.type == ecodes.EV_KEY:
        key_event = categorize(event)
        if key_event.keystate == key_event.key_down:
            key = key_event.keycode
            if key == 'KEY_ENTER':
                print("Scanned barcode:", barcode)
                try:
                    student = Student.objects.get(barcode=barcode)
                    Attendance.objects.create(student=student)
                    print(f"Attendance recorded for {student}")
                except Student.DoesNotExist:
                    print("No student found with that barcode.")
                barcode = ''
            elif key.startswith('KEY_'):
                char = '-' if key == 'KEY_MINUS' else key[4:].lower()
                barcode += char
    