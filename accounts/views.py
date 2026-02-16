from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import User, StaffProfile, StudentProfile, Course, CourseOffering, CourseRegistration, Department, PaymentTransaction, AcademicSession, Level
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .state import NIGERIA_STATES_AND_LGAS
import json
import requests
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Attendance, CourseRegistration, StudentProfile

# Create your views here.

#Login student or if staff to dashboard


@csrf_exempt
def student_login(request):
    """
    Handles login for students only.
    """
    if request.method == 'POST':
        # Check if this is a JSON request from API
        if request.content_type == 'application/x-www-form-urlencoded':
            # Get credentials from form data (API request)
            matriculation_number = request.POST.get('username')
            password = request.POST.get('password')
        else:
            # Regular form request
            matriculation_number = request.POST.get('username')
            password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=matriculation_number, password=password)

        if user is not None:
            if user.is_verified:  # Ensure the student is verified
                if user.user_type == 'student':  # Check if the user is a student
                    login(request, user)
                    # Check if this is an API request
                    if request.content_type == 'application/x-www-form-urlencoded':
                        # API request - redirect to dashboard
                        return redirect(reverse('dashboard:student_dashboard'))
                    else:
                        # Regular form request
                        messages.success(request, f"Student Login as '{request.user.username}' 🙌")
                        return redirect(reverse('dashboard:student_dashboard'))
                else:
                    if request.content_type == 'application/x-www-form-urlencoded':
                        # Return JSON error for API
                        return JsonResponse({'error': 'Only students are allowed to log in here.'}, status=400)
                    else:
                        messages.error(request, "Only students are allowed to log in here.")
            else:
                if request.content_type == 'application/x-www-form-urlencoded':
                    return JsonResponse({'error': 'Your account is not verified. Contact the admin.'}, status=400)
                else:
                    messages.error(request, "Your account is not verified. Contact the admin.")
        else:
            if request.content_type == 'application/x-www-form-urlencoded':
                return JsonResponse({'error': 'Invalid matriculation number or password.'}, status=400)
            else:
                messages.error(request, "Invalid matriculation number or password.")

    return render(request, 'accounts/student_login.html')


@csrf_exempt
def staff_login(request):
    if request.method == 'POST':
        # Check if this is a JSON request from API
        if request.content_type == 'application/x-www-form-urlencoded':
            # Get credentials from form data (API request)
            username = request.POST.get('username')
            password = request.POST.get('password')
        else:
            # Regular form request
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_verified:
                if user.user_type == 'staff':
                    login(request, user)
                    # Check if this is an API request
                    if request.content_type == 'application/x-www-form-urlencoded':
                        # API request - redirect to dashboard
                        return redirect(reverse('dashboard:staff_dashboard'))
                    else:
                        # Regular form request
                        messages.info(request, f'Staff Login as {request.user.username}')
                        return redirect(reverse('dashboard:staff_dashboard'))
                else:
                    if request.content_type == 'application/x-www-form-urlencoded':
                        # Return JSON error for API
                        return JsonResponse({'error': 'Only staff members are allowed to log in here.'}, status=400)
                    else:
                        messages.error(request, "Only staffs are allowed to log in here.")
                        return redirect('accounts:staff_login')
            else:
                if request.content_type == 'application/x-www-form-urlencoded':
                    return JsonResponse({'error': 'Your account is not verified. Contact the admin.'}, status=400)
                else:
                    messages.warning(request, 'Your account is not verified. Contact the admin.')
                    return redirect('accounts:staff_login')
        else:
            if request.content_type == 'application/x-www-form-urlencoded':
                return JsonResponse({'error': 'Invalid username or password.'}, status=400)
            else:
                messages.warning(request, 'Something went wrong')
                return redirect('accounts:staff_login')
    else:
        return render(request, 'accounts/staff_login.html')



def logout_user(request):
    logout(request)
    messages.info(request, 'Your session has expired Login to continue 😔')
    return redirect('accounts:student_login')

@login_required
def student_profile(request):
    """
    Display and handle updates to student profile
    """
    try:
        profile = StudentProfile.objects.get(user=request.user)
        context = {
            'profile': profile,
            'user': request.user,
            'states': NIGERIA_STATES_AND_LGAS.keys()
        }
        return render(request, 'accounts/student_profile.html', context)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Profile not found")
        return redirect('dashboard:student_dashboard')

@login_required
def edit_student_profile(request):
    """
    Handle student profile updates
    """
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    if request.method == 'POST':
        # Get form data
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        
        # Handle profile picture upload
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Update profile fields
        profile.date_of_birth = request.POST.get('date_of_birth')
        profile.gender = request.POST.get('gender')
        profile.state_of_origin = request.POST.get('state_of_origin')
        profile.local_government = request.POST.get('local_government')
        profile.permanent_address = request.POST.get('permanent_address')
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:student_profile')
    
    context = {
        'profile': profile,
        'user': request.user,
        'states': list(NIGERIA_STATES_AND_LGAS.keys()),
        'states_lgas': json.dumps(NIGERIA_STATES_AND_LGAS)
    }
    return render(request, 'accounts/edit_student_profile.html', context)

@login_required
def staff_profile(request):
    """
    Display staff profile
    """
    try:
        profile = StaffProfile.objects.get(user=request.user)
        context = {
            'profile': profile,
            'user': request.user,
            'states': NIGERIA_STATES_AND_LGAS.keys()
        }
        return render(request, 'accounts/staff_profile.html', context)
    except StaffProfile.DoesNotExist:
        messages.error(request, "Profile not found")
        return redirect('dashboard:staff_dashboard')

@login_required
def edit_staff_profile(request):
    """
    Handle staff profile updates
    """
    profile = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'POST':
        # Get form data
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        
        # Handle profile picture upload
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Update profile fields
        profile.date_of_birth = request.POST.get('date_of_birth')
        profile.gender = request.POST.get('gender')
        profile.state_of_origin = request.POST.get('state_of_origin')
        profile.local_government = request.POST.get('local_government')
        profile.permanent_address = request.POST.get('permanent_address')
        profile.qualification = request.POST.get('qualification')
        profile.specialization = request.POST.get('specialization')
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:staff_profile')
    
    context = {
        'profile': profile,
        'user': request.user,
        'states': NIGERIA_STATES_AND_LGAS.keys()
    }
    return render(request, 'accounts/edit_staff_profile.html', context)

def is_staff(user):
    return user.user_type == 'staff'

@login_required
@user_passes_test(is_staff)
def create_course(request):
    if request.method == 'POST':
        # Get the active academic session
        active_session = AcademicSession.objects.filter(is_active=True).first()
        if not active_session:
            messages.error(request, 'No active academic session found. Please contact the administrator.')
            return redirect('accounts:create_course')

        # Create the course first (without department/level)
        course = Course.objects.create(
            code=request.POST.get('code'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            credits=request.POST.get('credits'),
            semester=request.POST.get('semester'),
            academic_session=active_session,
            created_by=request.user
        )

        # Get selected departments and levels
        selected_departments = request.POST.getlist('departments')
        selected_levels = request.POST.getlist('levels')

        # Create CourseOffering records for each department-level combination
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
            messages.success(request, f'Course {course.code} created successfully with {offerings_created} department-level offerings!')
        else:
            messages.warning(request, f'Course {course.code} created but no offerings were specified.')

        return redirect('accounts:manage_courses')

    # Get academic sessions for display
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'departments': Department.objects.all(),
        'academic_sessions': academic_sessions,
        'levels': Level.objects.all().order_by('order')
    }
    return render(request, 'accounts/courses/create_course.html', context)

@login_required
@user_passes_test(is_staff)
def manage_courses(request):
    department = request.user.staffprofile.department
    # Get course offerings for this staff member's department
    course_offerings = CourseOffering.objects.filter(
        department=department
    ).select_related('course', 'level').order_by('course__code')

    # Group by course for easier display
    courses_data = {}
    for offering in course_offerings:
        course_id = offering.course.id
        if course_id not in courses_data:
            courses_data[course_id] = {
                'course': offering.course,
                'offerings': []
            }
        courses_data[course_id]['offerings'].append(offering)

    context = {
        'courses_data': courses_data,
        'department': department
    }
    return render(request, 'accounts/manage_courses.html', context)

@login_required
def register_courses(request):
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
        # Now we need to validate that the course is offered to this student's department and any level up to current
        registered_count = 0
        current_level_order = student.current_level.order
        available_levels = Level.objects.filter(order__lte=current_level_order)

        for course_id in selected_course_ids:
            try:
                course = Course.objects.get(id=course_id)
                # Check if this course is offered to this student's department and any level up to current
                offering_exists = CourseOffering.objects.filter(
                    course=course,
                    department=student.department,
                    level__in=available_levels,
                    is_active=True
                ).exists()

                if offering_exists:
                    CourseRegistration.objects.create(
                        student=student,
                        course=course,
                        status='registered'
                    )
                    registered_count += 1
            except Course.DoesNotExist:
                # Skip invalid course selections
                continue

        messages.success(request, f'Successfully registered for {registered_count} course(s)!')
        return redirect('accounts:view_registered_courses')

    student = request.user.studentprofile

    # Get current level order to determine which levels to show
    current_level_order = student.current_level.order

    # Get all levels up to and including current level
    available_levels = Level.objects.filter(order__lte=current_level_order).order_by('order')

    # Get course offerings for this student's department and all levels up to current
    course_offerings = CourseOffering.objects.filter(
        department=student.department,
        level__in=available_levels,
        course__academic_session=student.current_session,
        course__is_active=True,
        is_active=True
    ).select_related('course', 'level').order_by('level__order', 'course__semester', 'course__code')


    # Separate courses by level and semester for template display
    current_level_courses = {'first': [], 'second': []}
    carry_over_courses = {'first': [], 'second': []}

    for offering in course_offerings:
        course_data = {
            'course': offering.course,
            'level': offering.level,
            'level_display': offering.level.display_name
        }

        # Use level order comparison instead of object comparison
        if offering.level.order == student.current_level.order:
            # Current level courses
            if offering.course.semester == 'first':
                current_level_courses['first'].append(course_data)
            elif offering.course.semester == 'second':
                current_level_courses['second'].append(course_data)
        else:
            # Carry-over courses from previous levels
            if offering.course.semester == 'first':
                carry_over_courses['first'].append(course_data)
            elif offering.course.semester == 'second':
                carry_over_courses['second'].append(course_data)

    # Get all registered courses for this academic session
    registered_courses = CourseRegistration.objects.filter(
        student=student,
        course__academic_session=student.current_session
    ).select_related('course')

    # Get registered course IDs for easy checking in template
    registered_course_ids = set(reg.course.id for reg in registered_courses)

    # Debug information
    debug_info = {
        'student_level': student.current_level.display_name,
        'student_level_order': student.current_level.order,
        'available_levels_count': available_levels.count(),
        'available_levels': [l.display_name for l in available_levels],
        'course_offerings_count': course_offerings.count(),
        'current_level_courses_count': len(current_level_courses['first']) + len(current_level_courses['second']),
        'carry_over_courses_count': len(carry_over_courses['first']) + len(carry_over_courses['second']),
        'has_carry_over': len(carry_over_courses['first']) > 0 or len(carry_over_courses['second']) > 0,
        'carry_over_first_count': len(carry_over_courses['first']),
        'carry_over_second_count': len(carry_over_courses['second']),
        'current_first_sample': current_level_courses['first'][:1] if current_level_courses['first'] else [],
        'carry_over_first_sample': carry_over_courses['first'][:1] if carry_over_courses['first'] else [],
    }

    context = {
        'current_level_courses': current_level_courses,
        'carry_over_courses': carry_over_courses,
        'registered_course_ids': registered_course_ids,
        'registered_courses': registered_courses,
        'total_registered': registered_courses.count(),
        'total_credits': sum(reg.course.credits for reg in registered_courses),
        'has_carry_over_courses': len(carry_over_courses['first']) > 0 or len(carry_over_courses['second']) > 0,
        'debug_info': debug_info
    }
    return render(request, 'accounts/register_courses.html', context)

@login_required
def view_registered_courses(request):
    student = request.user.studentprofile

    # Get all registrations for the current academic session
    registrations = CourseRegistration.objects.filter(
        student=student,
        course__academic_session=student.current_session
    ).select_related('course').order_by('course__semester', 'course__code')

    # Separate by semester for better organization
    first_semester_regs = registrations.filter(course__semester='first')
    second_semester_regs = registrations.filter(course__semester='second')

    # Calculate totals
    total_credits = sum(reg.course.credits for reg in registrations)
    first_semester_credits = sum(reg.course.credits for reg in first_semester_regs)
    second_semester_credits = sum(reg.course.credits for reg in second_semester_regs)

    context = {
        'registrations': registrations,
        'first_semester_regs': first_semester_regs,
        'second_semester_regs': second_semester_regs,
        'total_credits': total_credits,
        'first_semester_credits': first_semester_credits,
        'second_semester_credits': second_semester_credits,
        'academic_session': student.current_session
    }
    return render(request, 'accounts/courses/registered_courses.html', context)

@login_required
def department_students(request):
    """View for staff to see students in their department"""

    if request.user.user_type != 'staff':
        messages.error(request, "Access denied. Staff only.")
        return redirect('dashboard:student_dashboard')
    
    try:
        staff_profile = request.user.staffprofile
        department = staff_profile.department
        
        # Get all students in the department
        students = StudentProfile.objects.filter(
            department=department
        ).select_related('user').order_by('current_level', 'user__first_name')
        
        # Group students by level
        students_by_level = {}
        for student in students:
            level = student.current_level
            if level not in students_by_level:
                students_by_level[level] = []
            students_by_level[level].append(student)


        context = {
            'department': department,
            'students_by_level': students_by_level,
            'total_students': students.count(),
              }
        return render(request, 'accounts/department_students.html', context)
        
    except StaffProfile.DoesNotExist:
        messages.error(request, "Staff profile not found. Please contact the administrator.")
        return redirect('dashboard:staff_dashboard')

@login_required
def student_detail(request, student_id):
    """Detailed view of a student for staff members"""
    if request.user.user_type != 'staff':
        messages.error(request, "Access denied. Staff only.")
        return redirect('dashboard:student_dashboard')
    
    try:
        staff_profile = request.user.staffprofile
        student = StudentProfile.objects.select_related(
            'user', 'department', 'faculty'
        ).get(id=student_id)
        
        # Ensure staff can only view students from their department
        if student.department != staff_profile.department:
            messages.error(request, "Access denied. You can only view students from your department.")
            return redirect('accounts:department_students')
        
        # Get student's course registrations
        course_registrations = CourseRegistration.objects.filter(
            student=student
        ).select_related('course').order_by('-registration_date')
        
        # Group courses by semester
        courses_by_semester = {}
        for reg in course_registrations:
            semester_key = f"{reg.course.get_semester_display()} - Level {reg.course.level}"
            if semester_key not in courses_by_semester:
                courses_by_semester[semester_key] = []
            courses_by_semester[semester_key].append(reg)
        
        context = {
            'student': student,
            'courses_by_semester': courses_by_semester,
            'total_courses': course_registrations.count(),
            'total_credits': sum(reg.course.credits for reg in course_registrations),
        }
        return render(request, 'accounts/student_detail.html', context)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('accounts:department_students')
    except StaffProfile.DoesNotExist:
        messages.error(request, "Staff profile not found. Please contact the administrator.")
        return redirect('dashboard:staff_dashboard')

@login_required
def school_fees(request):
    """View for school fees payment page"""
    if request.user.user_type != 'student':
        messages.error(request, "Access denied. Students only.")
        return redirect('dashboard:staff_dashboard')
    
    try:
        from .models import FeeStructure
        student = request.user.studentprofile
        current_session = AcademicSession.objects.filter(is_active=True).first()
        if not current_session:
            # Fallback to a default session if none is active
            current_session = AcademicSession.objects.filter(name="2023/2024").first()
            if not current_session:
                messages.error(request, "No active academic session found. Please contact the administrator.")
                return redirect('dashboard:student_dashboard')

        # Get payment history
        payments = PaymentTransaction.objects.filter(
            student=student
        ).order_by('-payment_date')

        # Check if student has paid for current session and semester
        current_payment = PaymentTransaction.objects.filter(
            student=student,
            session=current_session.name,
            semester=student.current_semester,
            status='success'
        ).first()

        # Get fee amount from FeeStructure
        try:
            fee_structure = FeeStructure.objects.get(
                academic_session=current_session,
                department=student.department,
                level=student.current_level
            )
            current_fees = fee_structure.amount
        except FeeStructure.DoesNotExist:
            # If no fee is defined for this combination, show 0 or a message
            current_fees = 0
            messages.warning(request, f"No fee structure found for {student.current_level.display_name} in {current_session.name}. Please contact the administrator.")
        
        context = {
            'student': student,
            'current_session': current_session.name,
            'current_session_obj': current_session,
            'current_fees': current_fees,
            'has_paid': bool(current_payment),
            'payments': payments,
        }
        return render(request, 'accounts/school_fees.html', context)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard:student_dashboard')

@login_required
@require_http_methods(["POST"])
def initiate_payment(request):
    """Initialize payment with Paystack"""
    try:
        student = request.user.studentprofile
        data = json.loads(request.body)
        amount = data.get('amount')
        
        if not amount:
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        # Get current active session
        current_session = AcademicSession.objects.filter(is_active=True).first()
        if not current_session:
            current_session = AcademicSession.objects.filter(name="2023/2024").first()
        session_name = current_session.name if current_session else "2023/2024"

        # Generate unique reference (use student.id instead of matriculation_number to avoid special characters like /)
        reference = f"SF-{student.id}-{int(timezone.now().timestamp())}"

        # Initialize payment with Paystack
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": student.user.email,
            "amount": float(amount) * 100,  # Convert to kobo
            "reference": reference,
            "callback_url": request.build_absolute_uri(
                reverse('accounts:verify_payment', args=[reference])
            ),
                "metadata": {
                    "student_id": student.id,
                    "payment_type": "school_fees",
                    "session": session_name,
                    "semester": student.current_semester
                }
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response_data['status']:
            # Create payment transaction record
            PaymentTransaction.objects.create(
                student=student,
                payment_type='school_fees',
                amount=amount,
                reference=reference,
                session=session_name,
                semester=student.current_semester
            )
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Payment initialization failed'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def verify_payment(request, reference):
    """Verify payment with Paystack"""
    try:
        # Verify payment with Paystack
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        # Get payment transaction
        transaction = PaymentTransaction.objects.get(reference=reference)
        
        if response_data['status'] and response_data['data']['status'] == 'success':
            # Update transaction
            transaction.status = 'success'
            transaction.paystack_reference = response_data['data']['reference']
            transaction.verified_at = timezone.now()
            transaction.save()
            
            messages.success(request, "Payment verified successfully!")
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, "Payment verification failed!")
        
        return redirect('accounts:school_fees')
        
    except PaymentTransaction.DoesNotExist:
        messages.error(request, "Payment transaction not found!")
        return redirect('accounts:school_fees')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('accounts:school_fees')
@login_required
def student_attendance(request):
    student = request.user
    attendance_records = Attendance.objects.filter(student=student).order_by('-date')
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'accounts/student_attendance.html', context)
@login_required
def payment_receipt(request, payment_id):
    """Generate payment receipt"""
    try:
        payment = PaymentTransaction.objects.select_related('student__user').get(
            id=payment_id,
            student__user=request.user,
            status='success'
        )
        
        context = {
            'payment': payment,
            'school_name': 'LakeView University',
            'school_address': 'Opposite Specialist Hospital, Off Jolly Nyame Way Jalingo, Taraba State',
        }
        return render(request, 'accounts/payment_receipt.html', context)
        
    except PaymentTransaction.DoesNotExist:
        messages.error(request, "Payment record not found!")
        return redirect('accounts:school_fees')

@login_required
def student_courses(request):
    """
    Display courses for student based on their department, level, and semester
    """
    # First check if user is a student
    if request.user.user_type != 'student':
        messages.error(request, "Access denied. Only students can view courses.")
        return redirect('dashboard:staff_dashboard')
        
    try:
        student = request.user.studentprofile

        # Get course offerings for student's department and level
        course_offerings = CourseOffering.objects.filter(
            department=student.department,
            level=student.current_level,
            course__academic_session=student.current_session,
            course__is_active=True,
            is_active=True
        ).select_related('course').order_by('course__semester', 'course__code')

        # Separate courses by semester
        first_semester_courses = [offering.course for offering in course_offerings if offering.course.semester == 'first']
        second_semester_courses = [offering.course for offering in course_offerings if offering.course.semester == 'second']
        
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