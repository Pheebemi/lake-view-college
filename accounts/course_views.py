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

        # Restrict to staff's programme type only
        staff_dept = request.user.staffprofile.department
        staff_programme_type = getattr(staff_dept.faculty, 'programme_type', 'degree') or 'degree'
        allowed_dept_ids = set(Department.objects.filter(faculty__programme_type=staff_programme_type).values_list('id', flat=True))
        allowed_level_ids = set(Level.objects.filter(programme_type=staff_programme_type).values_list('id', flat=True))

        offerings_created = 0
        for dept_id in selected_departments:
            for level_id in selected_levels:
                try:
                    did, lid = int(dept_id), int(level_id)
                    if did not in allowed_dept_ids or lid not in allowed_level_ids:
                        continue
                    department = Department.objects.get(id=did)
                    level = Level.objects.get(id=lid)
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
    
    # Staff can create courses for any department in their programme type (multiple depts can offer one course)
    staff_dept = request.user.staffprofile.department
    staff_programme_type = getattr(staff_dept.faculty, 'programme_type', 'degree') or 'degree'
    departments = Department.objects.filter(faculty__programme_type=staff_programme_type).select_related('faculty').order_by('name')
    levels = Level.objects.filter(programme_type=staff_programme_type).order_by('order')
    
    context = {
        'departments': departments,
        'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
        'levels': levels
    }
    return render(request, 'accounts/courses/create_course.html', context)

@login_required
@user_passes_test(is_staff)
def manage_courses(request):
    department = request.user.staffprofile.department
    course_offerings = CourseOffering.objects.filter(
        department=department
    ).select_related('course', 'course__academic_session', 'level').order_by('course__code', 'level__order')

    # Read filter query params
    filter_semester = request.GET.get('semester', '')
    filter_level = request.GET.get('level', '')
    filter_session = request.GET.get('session', '')
    filter_status = request.GET.get('status', '')

    # Apply filters to queryset
    if filter_semester:
        course_offerings = course_offerings.filter(course__semester=filter_semester)
    if filter_level:
        course_offerings = course_offerings.filter(level__id=filter_level)
    if filter_session:
        course_offerings = course_offerings.filter(course__academic_session__id=filter_session)
    if filter_status == 'active':
        course_offerings = course_offerings.filter(course__is_active=True)
    elif filter_status == 'inactive':
        course_offerings = course_offerings.filter(course__is_active=False)

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

    # Get filter options for dropdowns
    available_levels = Level.objects.filter(
        course_offerings__department=department
    ).distinct().order_by('order')
    available_sessions = AcademicSession.objects.filter(
        courses__offerings__department=department
    ).distinct().order_by('-start_year')

    context = {
        'courses': courses,
        'department': department,
        'total_courses': len(courses),
        'active_courses': sum(1 for r in courses if r['course'].is_active),
        'total_credits': total_credits,
        # Filter options
        'available_levels': available_levels,
        'available_sessions': available_sessions,
        # Current filter selections (to preserve state)
        'filter_semester': filter_semester,
        'filter_level': filter_level,
        'filter_session': filter_session,
        'filter_status': filter_status,
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

        # Allow current level + carry-over (any level up to current), same programme type only
        student_programme_type = getattr(student, 'programme_type', 'degree') or 'degree'
        current_level_order = student.current_level.order
        available_levels = Level.objects.filter(
            programme_type=student_programme_type,
            order__lte=current_level_order
        )

        registered_count = 0
        for course_id in selected_course_ids:
            try:
                course = Course.objects.get(id=course_id)
                if CourseOffering.objects.filter(
                    course=course,
                    department=student.department,
                    level__in=available_levels,
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

    # Restrict to same programme type (degree/ND/NCE) so ND students only see ND1/ND2, etc.
    student_programme_type = getattr(student, 'programme_type', 'degree') or 'degree'
    current_level_order = student.current_level.order
    available_levels = Level.objects.filter(
        programme_type=student_programme_type,
        order__lte=current_level_order
    ).order_by('order')

    course_offerings = CourseOffering.objects.filter(
        department=student.department,
        level__in=available_levels,
        course__academic_session=student.current_session,
        course__is_active=True,
        is_active=True
    ).select_related('course', 'level').order_by('level__order', 'course__semester', 'course__code')

    current_level_courses = {'first': [], 'second': []}
    carry_over_courses = {'first': [], 'second': []}

    for offering in course_offerings:
        course_data = {
            'course': offering.course,
            'level': offering.level,
            'level_display': offering.level.display_name
        }
        if offering.level.order == student.current_level.order:
            if offering.course.semester == 'first':
                current_level_courses['first'].append(course_data)
            elif offering.course.semester == 'second':
                current_level_courses['second'].append(course_data)
        else:
            if offering.course.semester == 'first':
                carry_over_courses['first'].append(course_data)
            elif offering.course.semester == 'second':
                carry_over_courses['second'].append(course_data)

    registered_courses = CourseRegistration.objects.filter(
        student=student,
        course__academic_session=student.current_session
    ).select_related('course')

    registered_course_ids = set(reg.course.id for reg in registered_courses)
    has_carry_over_courses = len(carry_over_courses['first']) > 0 or len(carry_over_courses['second']) > 0

    context = {
        'current_level_courses': current_level_courses,
        'carry_over_courses': carry_over_courses,
        'registered_course_ids': registered_course_ids,
        'registered_courses': registered_courses,
        'total_registered': registered_courses.count(),
        'total_credits': sum(reg.course.credits for reg in registered_courses),
        'has_carry_over_courses': has_carry_over_courses
    }
    return render(request, 'accounts/courses/register_courses.html', context)

@login_required
def view_registered_courses(request):
    student = request.user.studentprofile
    base_filter = {'student': student}
    if student.current_session_id:
        base_filter['course__academic_session'] = student.current_session
    registrations = CourseRegistration.objects.filter(
        **base_filter
    ).select_related('course').order_by('course__semester', 'course__code')

    first_semester_regs = [r for r in registrations if r.course.semester == 'first']
    second_semester_regs = [r for r in registrations if r.course.semester == 'second']
    first_semester_credits = sum(r.course.credits for r in first_semester_regs)
    second_semester_credits = sum(r.course.credits for r in second_semester_regs)
    total_credits = first_semester_credits + second_semester_credits

    context = {
        'registrations': registrations,
        'first_semester_regs': first_semester_regs,
        'second_semester_regs': second_semester_regs,
        'total_credits': total_credits,
        'first_semester_credits': first_semester_credits,
        'second_semester_credits': second_semester_credits,
        'academic_session': student.current_session,
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