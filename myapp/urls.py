from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from myapp.views import student_delete 

urlpatterns = [
    path('', views.role_select_view, name='role_select'),

    # Logins
    path('login/adviser/', views.adviser_login_view, name='adviser_login'),
    path('login/student/', views.student_login_view, name='student_login'),

    # Signups
    path('signup/student/', views.student_signup, name='student_signup'),

    # Dashboards
    path('adviser-dashboard/', views.adviser_dashboard, name='adviser_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),

    # Enrollment
    path('enroll/', views.enroll_student, name='enroll_student'),

    # Attendance
    path('scan/', views.scan_barcode, name='scan'),
    path('logout/', views.logout_view, name='logout'),
    path('adviser/scan-barcode/', views.adviser_scan_barcode, name='adviser_scan_barcode'),


    # Student Management
    path('adviser/my-students/', views.my_students, name='my_students'),
    path('student/add/', views.student_create, name='student_add'),
    path('student/<int:pk>/edit/', views.student_update, name='student_edit'),
    path('student/<int:student_id>/delete/', student_delete, name='student_delete')

]

# Static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
 