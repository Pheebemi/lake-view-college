from django.urls import path
from . import views, course_views


app_name = 'accounts'

urlpatterns = [
    path('student-login/', views.student_login, name='student_login'),
    path('staff-login/', views.staff_login, name='staff_login'),
    path('logout/', views.logout_user, name='logout'),
    path('student-profile/', views.student_profile, name='student_profile'),
    path('staff-profile/', views.staff_profile, name='staff_profile'),
    path('edit-student-profile/', views.edit_student_profile, name='edit_student_profile'),
    path('edit-staff-profile/', views.edit_staff_profile, name='edit_staff_profile'),
    path('create-course/', course_views.create_course, name='create_course'),
    path('manage-courses/', course_views.manage_courses, name='manage_courses'),
    path('register-courses/', course_views.register_courses, name='register_courses'),
    path('registered-courses/', course_views.view_registered_courses, name='view_registered_courses'),
    path('student/courses/', views.student_courses, name='student_courses'),  # Ensure this line is present
    path('department-students/', views.department_students, name='department_students'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('school-fees/', views.school_fees, name='school_fees'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('verify-payment/<str:reference>/', views.verify_payment, name='verify_payment'),
    path('payment-receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    #path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student-attendance/', views.student_attendance, name='student_attendance'),
    # path('login/', views, name='login'),
]