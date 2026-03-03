from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import (
    User, ExamOfficerProfile, Result, SemesterGPA,
    Course, CourseOffering, CourseRegistration, StudentProfile,
    AcademicSession, Level, Department, Faculty
)


def is_exam_officer(user):
    return user.is_authenticated and user.user_type == 'exam_officer'


@csrf_exempt
def exam_officer_login(request):
    """Login page for exam officers"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_verified:
                if user.user_type == 'exam_officer':
                    login(request, user)
                    messages.success(request, f"Welcome, {user.get_full_name()}!")
                    return redirect('accounts:exam_officer_dashboard')
                else:
                    messages.error(request, "Only Exam Officers are allowed to log in here.")
            else:
                messages.warning(request, 'Your account is not verified. Contact the admin.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/exam_officer/login.html')


@login_required
@user_passes_test(is_exam_officer)
def exam_officer_dashboard(request):
    """Dashboard for exam officers"""
    officer = request.user.examofficerprofile

    # Get assigned programme types
    assigned_types = officer.assigned_programme_types

    # Get current academic session
    current_session = AcademicSession.objects.filter(is_active=True).first()
    session_name = f"{current_session.start_year}/{current_session.end_year}" if current_session else "N/A"

    # Stats for assigned programme types
    total_courses = Course.objects.filter(
        offerings__department__faculty__programme_type__in=assigned_types,
        academic_session=current_session
    ).distinct().count() if current_session and assigned_types else 0

    total_results_uploaded = Result.objects.filter(
        uploaded_by=request.user,
        academic_session=current_session
    ).count() if current_session else 0

    # Get courses that need results (have registered students but no results yet)
    pending_courses = 0
    if current_session and assigned_types:
        courses_with_registrations = Course.objects.filter(
            offerings__department__faculty__programme_type__in=assigned_types,
            academic_session=current_session,
            is_active=True,
            registrations__status='registered'
        ).distinct()
        for course in courses_with_registrations:
            registered_count = CourseRegistration.objects.filter(
                course=course, status='registered'
            ).count()
            results_count = Result.objects.filter(
                course=course, academic_session=current_session
            ).count()
            if results_count < registered_count:
                pending_courses += 1

    # Recent uploads
    recent_results = Result.objects.filter(
        uploaded_by=request.user
    ).select_related('student__user', 'course').order_by('-uploaded_at')[:10]

    context = {
        'officer': officer,
        'session_name': session_name,
        'current_session': current_session,
        'assigned_types': assigned_types,
        'total_courses': total_courses,
        'total_results_uploaded': total_results_uploaded,
        'pending_courses': pending_courses,
        'recent_results': recent_results,
    }
    return render(request, 'accounts/exam_officer/dashboard.html', context)


@login_required
@user_passes_test(is_exam_officer)
def select_course(request):
    """Step 1: Select a course to upload results for"""
    officer = request.user.examofficerprofile
    assigned_types = officer.assigned_programme_types

    current_session = AcademicSession.objects.filter(is_active=True).first()

    # Get filter params
    filter_session = request.GET.get('session', '')
    filter_semester = request.GET.get('semester', '')
    filter_programme = request.GET.get('programme', '')
    filter_level = request.GET.get('level', '')

    # Use selected session or current
    if filter_session:
        selected_session = get_object_or_404(AcademicSession, id=filter_session)
    else:
        selected_session = current_session

    # Get courses for assigned programme types
    courses = Course.objects.filter(
        offerings__department__faculty__programme_type__in=assigned_types,
        academic_session=selected_session,
        is_active=True
    ).distinct().order_by('code')

    if filter_semester:
        courses = courses.filter(semester=filter_semester)

    if filter_programme and filter_programme in assigned_types:
        courses = courses.filter(
            offerings__department__faculty__programme_type=filter_programme
        ).distinct()

    if filter_level:
        courses = courses.filter(
            offerings__level__id=filter_level
        ).distinct()

    # Build course data with registration counts and result status
    from django.db.models import Q
    course_data = []
    for course in courses:
        # Get offerings to find eligible students
        course_offerings = CourseOffering.objects.filter(course=course)
        
        # Build query for eligible students
        student_q = Q()
        for offering in course_offerings:
            student_q |= Q(department=offering.department, current_level=offering.level)
        
        total_eligible = StudentProfile.objects.filter(student_q).count() if course_offerings.exists() else 0
        
        registered = CourseRegistration.objects.filter(
            course=course, status='registered'
        ).count()
        
        results_done = Result.objects.filter(
            course=course, academic_session=selected_session
        ).count()
        
        # Use total_eligible as the baseline for completion if it's greater than registered
        # This handles cases where results are uploaded for non-registered students
        denominator = max(registered, total_eligible)
        
        course_data.append({
            'course': course,
            'registered': registered,
            'total_eligible': total_eligible,
            'results_done': results_done,
            'is_complete': results_done >= denominator and denominator > 0,
        })

    # Get available filters
    available_sessions = AcademicSession.objects.all().order_by('-start_year')
    available_levels = Level.objects.filter(
        programme_type__in=assigned_types
    ).order_by('order')

    context = {
        'course_data': course_data,
        'available_sessions': available_sessions,
        'available_levels': available_levels,
        'assigned_types': assigned_types,
        'current_session': current_session,
        'selected_session': selected_session,
        'filter_session': filter_session,
        'filter_semester': filter_semester,
        'filter_programme': filter_programme,
        'filter_level': filter_level,
    }
    return render(request, 'accounts/exam_officer/select_course.html', context)


@login_required
@user_passes_test(is_exam_officer)
def upload_results(request, course_id):
    """Step 2: View all department students and enter/edit scores"""
    officer = request.user.examofficerprofile
    assigned_types = officer.assigned_programme_types

    course = get_object_or_404(Course, id=course_id)
    current_session = AcademicSession.objects.filter(is_active=True).first()

    # Verify this course belongs to officer's assigned programme types
    valid_offerings = CourseOffering.objects.filter(
        course=course,
        department__faculty__programme_type__in=assigned_types
    )
    if not valid_offerings.exists():
        messages.error(request, "You are not authorized to upload results for this course.")
        return redirect('accounts:exam_officer_select_course')

    # Get all departments and levels that offer this course
    offering_dept_levels = valid_offerings.values_list('department_id', 'level_id')

    # Build query to get ALL students in those departments at those levels
    from django.db.models import Q
    student_q = Q()
    for dept_id, level_id in offering_dept_levels:
        student_q |= Q(department_id=dept_id, current_level_id=level_id)

    all_students = StudentProfile.objects.filter(
        student_q
    ).select_related('user', 'current_level', 'department').order_by('user__first_name', 'user__last_name')

    # Get set of registered student IDs for this course
    registered_student_ids = set(
        CourseRegistration.objects.filter(
            course=course,
            status='registered'
        ).values_list('student_id', flat=True)
    )

    if request.method == 'POST':
        saved_count = 0
        errors = []
        for student in all_students:
            test_key = f"test_{student.id}"
            exam_key = f"exam_{student.id}"

            test_score = request.POST.get(test_key, '').strip()
            exam_score = request.POST.get(exam_key, '').strip()

            if not test_score and not exam_score:
                continue  # Skip students with no scores entered

            try:
                test_val = float(test_score) if test_score else 0
                exam_val = float(exam_score) if exam_score else 0

                if test_val < 0 or test_val > 40:
                    errors.append(f"{student.user.get_full_name()}: Test score must be 0-40")
                    continue
                if exam_val < 0 or exam_val > 60:
                    errors.append(f"{student.user.get_full_name()}: Exam score must be 0-60")
                    continue

                # Get the level from the course offering for this student
                offering = CourseOffering.objects.filter(
                    course=course,
                    department=student.department
                ).first()
                level = offering.level if offering else student.current_level

                result, created = Result.objects.update_or_create(
                    student=student,
                    course=course,
                    academic_session=current_session,
                    defaults={
                        'semester': course.semester,
                        'level': level,
                        'test_score': test_val,
                        'exam_score': exam_val,
                        'uploaded_by': request.user,
                    }
                )
                saved_count += 1
            except (ValueError, TypeError) as e:
                errors.append(f"{student.user.get_full_name()}: Invalid score value")

        if errors:
            for err in errors:
                messages.warning(request, err)
        if saved_count > 0:
            messages.success(request, f"Successfully saved {saved_count} result(s) for {course.code}!")

        return redirect('accounts:exam_officer_upload_results', course_id=course.id)

    # Get existing results for pre-filling the form
    student_results = {}
    existing_results = Result.objects.filter(
        course=course,
        academic_session=current_session
    )
    for r in existing_results:
        student_results[r.student_id] = r

    # Build student list with existing results and registration status
    students_data = []
    for student in all_students:
        existing = student_results.get(student.id)
        students_data.append({
            'student': student,
            'is_registered': student.id in registered_student_ids,
            'test_score': existing.test_score if existing else '',
            'exam_score': existing.exam_score if existing else '',
            'total_score': existing.total_score if existing else '',
            'grade': existing.grade if existing else '',
            'has_result': existing is not None,
        })

    context = {
        'course': course,
        'students_data': students_data,
        'total_students': len(students_data),
        'registered_count': len(registered_student_ids),
        'results_completed': sum(1 for s in students_data if s['has_result']),
        'current_session': current_session,
    }
    return render(request, 'accounts/exam_officer/upload_results.html', context)
