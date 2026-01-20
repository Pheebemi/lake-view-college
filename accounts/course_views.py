from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Course, CourseRegistration, Department, StudentProfile, PaymentTransaction

def is_staff(user):
    return user.user_type == 'staff'

@login_required
@user_passes_test(is_staff)
def create_course(request):
    if request.method == 'POST':
        department = request.user.staffprofile.department
        course = Course.objects.create(
            code=request.POST.get('code'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            credits=request.POST.get('credits'),
            department=department,
            semester=request.POST.get('semester'),
            level=request.POST.get('level'),
            created_by=request.user
        )
        messages.success(request, f'Course {course.code} created successfully!')
        return redirect('accounts:manage_courses')
    
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'accounts/courses/create_course.html', context)

@login_required
@user_passes_test(is_staff)
def manage_courses(request):
    department = request.user.staffprofile.department
    courses = Course.objects.filter(department=department)
    context = {
        'courses': courses
    }
    return render(request, 'accounts/courses/manage_courses.html', context)

@login_required
def register_courses(request):
    student = request.user.studentprofile
    
    # Check if student has paid school fees
    current_session = "2023/2024"  # Make this dynamic
    has_paid = PaymentTransaction.objects.filter(
        student=student,
        session=current_session,
        semester=student.current_semester,
        status='success'
    ).exists()
    
    if not has_paid:
        messages.error(request, "You need to pay your school fees before registering courses.")
        return redirect('accounts:school_fees')
    
    if request.method == 'POST':
        selected_courses = request.POST.getlist('courses')
        student = request.user.studentprofile
        
        # Clear existing registrations for the current semester
        CourseRegistration.objects.filter(
            student=student,
            course__semester=student.current_semester
        ).delete()
        
        # Create new registrations
        for course_id in selected_courses:
            course = Course.objects.get(id=course_id)
            CourseRegistration.objects.create(
                student=student,
                course=course,
                status='registered'
            )
        
        messages.success(request, 'Courses registered successfully!')
        return redirect('accounts:view_registered_courses')
    
    student = request.user.studentprofile
    available_courses = Course.objects.filter(
        department=student.department,
        level=student.current_level,
        semester=student.current_semester,
        is_active=True
    )
    
    context = {
        'courses': available_courses,
        'registered_courses': CourseRegistration.objects.filter(
            student=student,
            course__semester=student.current_semester
        ).values_list('course_id', flat=True)
    }
    return render(request, 'accounts/courses/register_courses.html', context)

@login_required
def view_registered_courses(request):
    student = request.user.studentprofile
    registrations = CourseRegistration.objects.filter(
        student=student
    ).select_related('course')
    
    context = {
        'registrations': registrations
    }
    return render(request, 'accounts/courses/registered_courses.html', context)

@login_required
def student_courses(request):
    """
    Display courses for student based on their department, level and semester
    """
    # First check if user is a student
    if request.user.user_type != 'student':
        messages.error(request, "Access denied. Only students can view courses.")
        return redirect('dashboard:staff_dashboard')
        
    try:
        student = request.user.studentprofile
        
        # Get all courses for student's department
        department_courses = Course.objects.filter(
            department=student.department,
            level=student.current_level,
            is_active=True
        ).order_by('semester')
        
        # Separate courses by semester
        first_semester_courses = department_courses.filter(semester='first')
        second_semester_courses = department_courses.filter(semester='second')
        
        # Get registered courses
        registered_courses = CourseRegistration.objects.filter(
            student=student
        ).values_list('course_id', flat=True)
        
        context = {
            'first_semester_courses': first_semester_courses,
            'second_semester_courses': second_semester_courses,
            'registered_courses': registered_courses,
            'current_semester': student.current_semester,
            'student': student
        }
        return render(request, 'accounts/courses/student_courses.html', context)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact the administrator.")
        return redirect('dashboard:student_dashboard') 