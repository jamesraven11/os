from django import forms
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'student_id']  # adjust fields based on your model

class ScanForm(forms.Form):
    barcode = forms.CharField(label="Scan Barcode", max_length=100)


