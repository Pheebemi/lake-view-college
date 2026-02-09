from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Course, CourseOffering, CourseRegistration, Department, StudentProfile, PaymentTransaction, AcademicSession, Level

def is_staff(user):
    return user.user_type == 'staff'

@login_required
@user_passes_test(is_staff)
def create_course(request):
    if request.method == 'POST':
        course = Course.objects.create(
            code=request.POST.get('code'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            credits=request.POST.get('credits'),
            semester=request.POST.get('semester'),
            academic_session_id=request.POST.get('academic_session'),
            created_by=request.user
        )

        selected_departments = request.POST.getlist('departments')
        selected_levels = request.POST.getlist('levels')

        offerings_created = 0
        for dept_id in selected_departments:
            for level_id in selected_levels:
                try:
                    department = Department.objects.get(id=dept_id)
                    level = Level.objects.get(id=level_id)
                    CourseOffering.objects.create(
                        course=course,
                        department=department,
                        level=level,
                        is_active=True
                    )
                    offerings_created += 1
                except (Department.DoesNotExist, Level.DoesNotExist):
                    continue

        if offerings_created > 0:
            messages.success(request, f'Course {course.code} created with {offerings_created} department-level offering(s)!')
        else:
            messages.warning(request, f'Course {course.code} created but no offerings specified.')

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
    course_offerings = CourseOffering.objects.filter(
        department=department
    ).select_related('course', 'level').order_by('course__code', 'level__order')

    # Build flat list: each row is a (course, level) for template compatibility
    courses = []
    seen = set()
    for offering in course_offerings:
        c = offering.course
        key = (c.id, offering.level.id)
        if key not in seen:
            seen.add(key)
            courses.append({'course': c, 'level': offering.level, 'offering': offering})

    total_credits = sum(row['course'].credits for row in courses)
    context = {
        'courses': courses,
        'department': department,
        'total_courses': len(courses),
        'active_courses': sum(1 for r in courses if r['course'].is_active),
        'total_credits': total_credits,
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

        registered_count = 0
        for course_id in selected_course_ids:
            try:
                course = Course.objects.get(id=course_id)
                if CourseOffering.objects.filter(
                    course=course,
                    department=student.department,
                    level=student.current_level,
                    is_active=True
                ).exists():
                    CourseRegistration.objects.create(
                        student=student,
                        course=course,
                        status='registered'
                    )
                    registered_count += 1
            except Course.DoesNotExist:
                continue

        messages.success(request, f'Successfully registered for {registered_count} course(s)!')
        return redirect('accounts:view_registered_courses')

    student = request.user.studentprofile

    course_offerings = CourseOffering.objects.filter(
        department=student.department,
        level=student.current_level,
        course__academic_session=student.current_session,
        course__is_active=True,
        is_active=True
    ).select_related('course').order_by('course__semester', 'course__code')

    first_semester_courses = [o.course for o in course_offerings if o.course.semester == 'first']
    second_semester_courses = [o.course for o in course_offerings if o.course.semester == 'second']

    registered_courses = CourseRegistration.objects.filter(
        student=student,
        course__academic_session=student.current_session
    ).select_related('course')

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
        
        course_offerings = CourseOffering.objects.filter(
            department=student.department,
            level=student.current_level,
            course__academic_session=student.current_session,
            course__is_active=True,
            is_active=True
        ).select_related('course').order_by('course__semester', 'course__code')

        first_semester_courses = [o.course for o in course_offerings if o.course.semester == 'first']
        second_semester_courses = [o.course for o in course_offerings if o.course.semester == 'second']
        
        # Get registered courses with course details
        registered_courses_queryset = CourseRegistration.objects.filter(
            student=student,
            course__academic_session=student.current_session
        ).select_related('course')

        # Calculate total credits
        total_credits = sum(reg.course.credits for reg in registered_courses_queryset)

        # Get registered course IDs for template
        registered_course_ids = list(registered_courses_queryset.values_list('course_id', flat=True))

        context = {
            'first_semester_courses': first_semester_courses,
            'second_semester_courses': second_semester_courses,
            'registered_course_ids': registered_course_ids,
            'registered_courses_queryset': registered_courses_queryset,
            'total_registered': len(registered_course_ids),
            'total_credits': total_credits,
            'first_semester_count': first_semester_courses.count(),
            'second_semester_count': second_semester_courses.count(),
            'total_available': first_semester_courses.count() + second_semester_courses.count(),
            'current_semester': student.current_semester,
            'student': student
        }
        return render(request, 'accounts/courses/student_courses.html', context)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact the administrator.")
        return redirect('dashboard:student_dashboard') 