from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Course, CourseRegistration, Department, StudentProfile, PaymentTransaction, AcademicSession, Level

def is_staff(user):
    return user.user_type == 'staff'

@login_required
@user_passes_test(is_staff)
def create_course(request):
    if request.method == 'POST':
        department = request.user.staffprofile.department

        # Get the Level instance
        level_name = request.POST.get('level')
        try:
            level = Level.objects.get(name=level_name)
        except Level.DoesNotExist:
            messages.error(request, f'Invalid level: {level_name}')
            return redirect('accounts:create_course')

        course = Course.objects.create(
            code=request.POST.get('code'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            credits=request.POST.get('credits'),
            department=department,
            semester=request.POST.get('semester'),
            level=level,  # Use Level instance instead of string
            academic_session_id=request.POST.get('academic_session'),
            created_by=request.user
        )
        messages.success(request, f'Course {course.code} created successfully!')
        return redirect('accounts:manage_courses')
    
    context = {
        'departments': Department.objects.all(),
        'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
        'levels': Level.objects.all().order_by('order')
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

    # Check if student has paid school fees for current session
    has_paid = PaymentTransaction.objects.filter(
        student=student,
        session=student.current_session.name if student.current_session else "2023/2024",
        semester=student.current_semester,
        status='success'
    ).exists()

    if not has_paid:
        messages.error(request, "You need to pay your school fees before registering courses.")
        return redirect('accounts:school_fees')

    if request.method == 'POST':
        selected_course_ids = request.POST.getlist('courses')
        student = request.user.studentprofile

        # Get the selected courses to determine which semesters to clear
        selected_courses = Course.objects.filter(id__in=selected_course_ids)
        affected_semesters = set(selected_courses.values_list('semester', flat=True))

        # Clear existing registrations for affected semesters only
        for semester in affected_semesters:
            CourseRegistration.objects.filter(
                student=student,
                course__semester=semester,
                course__academic_session=student.current_session
            ).delete()

        # Create new registrations for all selected courses
        registered_count = 0
        for course_id in selected_course_ids:
            try:
                course = Course.objects.get(
                    id=course_id,
                    department=student.department,
                    level=student.current_level,
                    academic_session=student.current_session,
                    is_active=True
                )
                CourseRegistration.objects.create(
                    student=student,
                    course=course,
                    status='registered'
                )
                registered_count += 1
            except Course.DoesNotExist:
                # Skip invalid course selections (shouldn't happen with proper form validation)
                continue

        messages.success(request, f'Successfully registered for {registered_count} course(s)!')
        return redirect('accounts:view_registered_courses')

    student = request.user.studentprofile

    # Get courses for both semesters of the current academic session
    available_courses = Course.objects.filter(
        department=student.department,
        level=student.current_level,
        academic_session=student.current_session,
        is_active=True
    ).order_by('semester', 'code')

    # Get all registered courses for this academic session
    registered_courses = CourseRegistration.objects.filter(
        student=student,
        course__academic_session=student.current_session
    ).select_related('course')

    # Separate courses by semester for template display
    first_semester_courses = available_courses.filter(semester='first')
    second_semester_courses = available_courses.filter(semester='second')

    # Get registered course IDs for easy checking in template
    registered_course_ids = set(reg.course.id for reg in registered_courses)

    context = {
        'first_semester_courses': first_semester_courses,
        'second_semester_courses': second_semester_courses,
        'registered_course_ids': registered_course_ids,
        'registered_courses': registered_courses,
        'total_registered': registered_courses.count(),
        'total_credits': sum(reg.course.credits for reg in registered_courses)
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