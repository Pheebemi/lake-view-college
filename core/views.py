from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from accounts.models import Faculty, Department, User, StudentProfile, AcademicRecord
from django.contrib import messages
from .models import ContactSubmission
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import render_to_string
from .forms import ApplicantForm, ApplicantScreeningForm
from .models import ScreeningForm
# from weasyprint import HTML
from accounts.state import NIGERIA_STATES_AND_LGAS
from .models import Program
from django.contrib.auth import get_user_model
from django.db import IntegrityError
User = get_user_model()
from .models import Applicant, Program
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .models import ScreeningPayment
from django.views.decorators.http import require_http_methods
import time
import requests
from django.conf import settings


def landing_page(request):
    return render(request, 'core/landing.html')

def create_applicant(request):
    programs = Program.objects.all()
    if request.method == 'POST':
        try:
            # Create user instance but don't save yet
            user = User(
                username=request.POST.get('username'),
                email=request.POST.get('email', ''),  # Add email field if not already present
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                user_type='applicant'
            )
            
            # Validate password
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if not password1 or not password2:
                messages.error(request, 'Please provide both passwords')
                return redirect('core:apply_page')
                
            if password1 != password2:
                messages.error(request, 'Passwords do not match!')
                return redirect('core:apply_page')
            
            # Set password and save user
            user.set_password(password1)
            
            # Basic validation
            if not all([user.username, user.first_name, user.last_name]):
                messages.error(request, 'Please fill in all required fields')
                return redirect('core:apply_page')
            
            # Save user
            user.save()
            
            # Create applicant profile
            try:
                program = Program.objects.get(id=request.POST.get('programs'))
                applicant = Applicant.objects.create(
                    user=user,
                    state=request.POST.get('state', ''),
                    phone_number=request.POST.get('phone_number', ''),
                    programs=program,
                    mode=request.POST.get('mode', 'Open')
                )
                messages.success(request, 'Your application has been submitted successfully!')
                return redirect('core:applicant_login')
            except Program.DoesNotExist:
                user.delete()  # Rollback user creation if program doesn't exist
                messages.error(request, 'Invalid program selected')
                return redirect('core:apply_page')
            except Exception as e:
                user.delete()  # Rollback user creation if applicant profile creation fails
                messages.error(request, f'Error creating application: {str(e)}')
                return redirect('core:apply_page')
                
        except IntegrityError:
            messages.error(request, 'Username already exists. Please choose a different one.')
            return redirect('core:apply_page')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('core:apply_page')
    
    context = {
        'states': list(NIGERIA_STATES_AND_LGAS.keys()),
        'programs': programs
    }
    return render(request, 'core/apply.html', context)

def applicant_login(request):
    """
    Handles login for applicants.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.user_type == 'applicant':
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name()}!")
                return redirect('core:applicant_dashboard')
            else:
                messages.error(request, "This login is for applicants only.")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'core/applicant_login.html')

@login_required
def applicant_dashboard(request):
    """
    Display the applicant dashboard.
    """
    if request.user.user_type != 'applicant':
        messages.error(request, "Access denied. Applicants only.")
        return redirect('core:landing_page')
    
    try:
        applicant = Applicant.objects.get(user=request.user)
        has_submitted_form = ScreeningForm.objects.filter(applicant=applicant).exists()
        
        # Check if applicant has paid for screening form
        has_paid_screening_fee = ScreeningPayment.objects.filter(
            applicant=applicant, 
            status='success'
        ).exists()
        
        # Get the screening fee based on the applicant's program
        screening_fee = applicant.programs.screening_fee
        
        context = {
            'applicant': applicant,
            'has_submitted_form': has_submitted_form,
            'has_paid_screening_fee': has_paid_screening_fee,
            'screening_fee': screening_fee
        }
        return render(request, 'dashboard/applicant-dashboard.html', context)
    except Applicant.DoesNotExist:
        messages.error(request, "Applicant profile not found.")
        return redirect('core:landing_page')

def landing_page(request):
    faculties = Faculty.objects.all()
    context = {'faculties': faculties}
    return render(request, 'core/landing.html', context)


def contact_page(request):
    return render(request, 'core/contact.html')

def about_page(request):
    return render(request, 'core/about.html')

def library_page(request):
    return render(request, 'core/library.html')

def programs_list(request):
    programs = Faculty.objects.all()
    context = {'programs': programs}
    return render(request, 'core/programs.html', context)

def program_detail(request, pk):
    program = get_object_or_404(Faculty, pk=pk)
    departments = Department.objects.filter(faculty=program)
    context = {
        'program':program,
        'departments':departments
        }
    return render(request, 'core/program_detail.html', context)

def contact_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Save the contact submission
        ContactSubmission.objects.create(name=name, email=email, message=message)
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('core:contact_page')

    return render(request, 'core/contact.html')

@login_required
def screening_payment_wall(request):
    """Payment wall for screening form access"""
    if request.user.user_type != 'applicant':
        messages.error(request, "Access denied. Applicants only.")
        return redirect('core:landing_page')

    applicant = get_object_or_404(Applicant, user=request.user)
    
    # Check if applicant has already paid
    existing_payment = ScreeningPayment.objects.filter(
        applicant=applicant, 
        status='success'
    ).first()
    
    if existing_payment:
        # Already paid, redirect to screening form
        return redirect('core:screening_form')
    
    # Get the screening fee based on the applicant's program
    screening_fee = applicant.programs.screening_fee
    
    context = {
        'applicant': applicant,
        'amount': screening_fee
    }
    return render(request, 'core/screening_payment_wall.html', context)

@login_required
def initiate_screening_payment(request):
    """Initialize screening form payment with Paystack - EXACT COPY FROM SCHOOL FEES"""
    try:
        applicant = get_object_or_404(Applicant, user=request.user)
        data = json.loads(request.body)
        amount = data.get('amount')
        
        if not amount:
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        # Generate unique reference
        reference = f"SCR-{applicant.id}-{int(time.time())}"
        
        # Initialize payment with Paystack
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": request.user.email,
            "amount": float(amount) * 100,  # Convert to kobo
            "reference": reference,
            "callback_url": request.build_absolute_uri(
                reverse('core:verify_screening_payment', args=[reference])
            ),
            "metadata": {
                "applicant_id": applicant.id,
                "payment_type": "screening_form"
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        if response_data['status']:
            # Create payment record - EXACT COPY FROM SCHOOL FEES
            ScreeningPayment.objects.create(
                applicant=applicant,
                reference=reference,
                amount=amount
            )
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Payment initialization failed'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_program_choices(request, program_type):
    """API endpoint to get program choices based on program type"""
    try:
        choices = ProgramChoice.objects.filter(
            program_type=program_type,
            is_active=True
        ).values('id', 'name')
        
        return JsonResponse({
            'success': True,
            'choices': list(choices)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def verify_screening_payment(request, reference):
    """Verify screening form payment with Paystack"""
    if request.user.user_type != 'applicant':
        messages.error(request, "Access denied. Applicants only.")
        return redirect('core:screening_payment_wall')

    try:
        # Verify payment with Paystack
        import requests
        from django.conf import settings
        from django.utils import timezone
        
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        # Get payment transaction
        payment = ScreeningPayment.objects.get(reference=reference, applicant__user=request.user)
        
        if response_data['status'] and response_data['data']['status'] == 'success':
            # Update payment status
            payment.status = 'success'
            payment.paystack_reference = response_data['data']['reference']
            payment.verified_at = timezone.now()
            payment.save()
            
            messages.success(request, "Payment verified successfully! You can now access the screening form.")
            return redirect('core:screening_form')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Payment verification failed!")
            return redirect('core:screening_payment_wall')
        
    except ScreeningPayment.DoesNotExist:
        messages.error(request, "Payment transaction not found!")
        return redirect('core:screening_payment_wall')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('core:screening_payment_wall')


@login_required
def screening_form(request):
    if request.user.user_type != 'applicant':
        messages.error(request, "Access denied. Applicants only.")
        return redirect('core:landing_page')

    applicant = get_object_or_404(Applicant, user=request.user)
    
    # Check if applicant has paid for screening form
    payment = ScreeningPayment.objects.filter(
        applicant=applicant, 
        status='success'
    ).first()
    
    if not payment:
        screening_fee = applicant.programs.screening_fee
        messages.error(request, f"You must pay ₦{screening_fee:,.0f} to access the screening form.")
        return redirect('core:screening_payment_wall')
    
    existing_form = ScreeningForm.objects.filter(applicant=applicant).first()

    if request.method == 'POST':
        form = ApplicantScreeningForm(request.POST, request.FILES, instance=existing_form, applicant=applicant)
        if form.is_valid():
            try:
                screening = form.save(commit=False)
                screening.applicant = applicant
                screening.save()

                # Process academic subjects
                academic_subjects_data = request.POST.get('academic_subjects')
                if academic_subjects_data:
                    # Clear existing academic subjects for this screening form
                    screening.academic_subjects.all().delete()
                    
                    # Parse the academic subjects data
                    import ast
                    try:
                        subjects_dict = ast.literal_eval(academic_subjects_data)
                        
                        # Process first sitting subjects
                        if 'first' in subjects_dict:
                            for subject_id, subject_data in subjects_dict['first'].items():
                                if subject_data.get('subject') and subject_data.get('grade'):
                                    from .models import AcademicSubject
                                    AcademicSubject.objects.create(
                                        screening_form=screening,
                                        subject=subject_data['subject'],
                                        grade=subject_data['grade'],
                                        sitting='first'
                                    )
                        
                        # Process second sitting subjects
                        if 'second' in subjects_dict:
                            for subject_id, subject_data in subjects_dict['second'].items():
                                if subject_data.get('subject') and subject_data.get('grade'):
                                    from .models import AcademicSubject
                                    AcademicSubject.objects.create(
                                        screening_form=screening,
                                        subject=subject_data['subject'],
                                        grade=subject_data['grade'],
                                        sitting='second'
                                    )
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing academic subjects data: {e}")

                # Process examination details
                from .models import ExaminationDetail
                
                # Clear existing examination details
                screening.examination_details.all().delete()
                
                # Process first sitting examination (required)
                first_exam_type = request.POST.get('first_sitting_exam_type')
                first_exam_number = request.POST.get('first_sitting_exam_number')
                first_exam_year = request.POST.get('first_sitting_exam_year')
                
                if first_exam_type and first_exam_number and first_exam_year:
                    ExaminationDetail.objects.create(
                        screening_form=screening,
                        sitting='first',
                        exam_type=first_exam_type,
                        exam_number=first_exam_number,
                        exam_year=first_exam_year
                    )
                
                # Process second sitting examination (optional)
                second_exam_type = request.POST.get('second_sitting_exam_type')
                second_exam_number = request.POST.get('second_sitting_exam_number')
                second_exam_year = request.POST.get('second_sitting_exam_year')
                
                # Only create if all fields are provided
                if second_exam_type and second_exam_number and second_exam_year:
                    ExaminationDetail.objects.create(
                        screening_form=screening,
                        sitting='second',
                        exam_type=second_exam_type,
                        exam_number=second_exam_number,
                        exam_year=second_exam_year
                    )

                # Check if this is an auto-save request
                is_auto_save = request.POST.get('auto_save') == 'true'
                
                if is_auto_save:
                    return JsonResponse({
                        'success': True,
                        'message': f'Step {request.POST.get("step", "unknown")} saved successfully'
                    })

                # Add success message for final submission
                messages.success(request, 'Screening form submitted successfully!')

                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('core:applicant_dashboard'),
                    'message': 'Screening form submitted successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error saving form: {str(e)}'
                })
        
        errors = {
            field: error_list[0] for field, error_list in form.errors.items()
            if field != 'de_result' or (field == 'de_result' and request.POST.get('admission_type') == 'direct-entry')
        }

        return JsonResponse({
            'success': False,
            'message': 'Please correct the following errors: ' + ', '.join([f"{field}: {error}" for field, error in errors.items()])
        })

    # Render the form for GET requests
    form = ApplicantScreeningForm(instance=existing_form, applicant=applicant)
    
    # Get existing academic subjects if form exists
    existing_subjects = {}
    existing_examinations = {}
    last_saved_step = 1  # Default to step 1
    
    if existing_form:
        from .models import AcademicSubject
        first_sitting = existing_form.get_first_sitting_subjects()
        second_sitting = existing_form.get_second_sitting_subjects()
        existing_subjects = {
            'first': [{'subject': s.subject, 'grade': s.grade} for s in first_sitting],
            'second': [{'subject': s.subject, 'grade': s.grade} for s in second_sitting]
        }
        
        # Get existing examination details
        first_exam = existing_form.get_first_sitting_examination()
        second_exam = existing_form.get_second_sitting_examination()
        
        existing_examinations = {
            'first': {
                'exam_type': first_exam.exam_type if first_exam else '',
                'exam_number': first_exam.exam_number if first_exam else '',
                'exam_year': first_exam.exam_year if first_exam else ''
            } if first_exam else {},
            'second': {
                'exam_type': second_exam.exam_type if second_exam else '',
                'exam_number': second_exam.exam_number if second_exam else '',
                'exam_year': second_exam.exam_year if second_exam else ''
            } if second_exam else {}
        }
        
        # Determine the last completed step based on form data
        if existing_form.first_name and existing_form.first_name != 'N/A':
            last_saved_step = 1
        if existing_form.jamb_reg_no and existing_form.jamb_reg_no != 'N/A':
            last_saved_step = 2
        if existing_form.primary_school and existing_form.primary_school != 'N/A':
            last_saved_step = 3
        if existing_form.first_choice:
            last_saved_step = 4
        if existing_form.waec_result and existing_form.waec_result.name != 'test.docx':
            last_saved_step = 5
        if existing_form.declaration:
            last_saved_step = 6
    
    # Add states and LGAs data to context
    context = {
        'form': form,
        'existing_form': existing_form,
        'active_step': last_saved_step, # Use the last saved step as the active step
        'states_lgas': json.dumps(NIGERIA_STATES_AND_LGAS),
        'states': list(NIGERIA_STATES_AND_LGAS.keys()),
        'existing_subjects': json.dumps(existing_subjects),
        'existing_examinations': json.dumps(existing_examinations)
    }
    
    return render(request, 'core/screening_form.html', context)

@login_required
def get_screening_form_data(request):
    """Get screening form data for printing"""
    if request.user.user_type != 'applicant':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        applicant = get_object_or_404(Applicant, user=request.user)
        screening_form = ScreeningForm.objects.filter(applicant=applicant).first()
        
        if not screening_form:
            return JsonResponse({'error': 'No screening form found'}, status=404)
        
        # Get academic subjects
        first_sitting_subjects = screening_form.get_first_sitting_subjects()
        second_sitting_subjects = screening_form.get_second_sitting_subjects()
        
        # Get examination details
        first_exam = screening_form.get_first_sitting_examination()
        second_exam = screening_form.get_second_sitting_examination()
        
        data = {
            'personal_info': {
                'first_name': screening_form.first_name,
                'middle_name': screening_form.middle_name,
                'surname': screening_form.surname,
                'date_of_birth': screening_form.date_of_birth.strftime('%B %d, %Y') if screening_form.date_of_birth else 'N/A',
                'sex': screening_form.get_sex_display(),
                'state_of_origin': screening_form.state_of_origin,
                'local_government': screening_form.local_government,
                'email': screening_form.email,
                'phone_number': screening_form.phone_number,
                'contact_address': screening_form.contact_address,
            },
            'jamb_details': {
                'jamb_reg_no': screening_form.jamb_reg_no,
                'jamb_score': screening_form.jamb_score,
            },
            'academic_info': {
                'primary_school': screening_form.primary_school,
                'primary_school_dates': screening_form.primary_school_dates,
                'secondary_school': screening_form.secondary_school,
                'secondary_school_dates': screening_form.secondary_school_dates,
            },
            'examination_details': {
                'first_sitting': {
                    'exam_type': first_exam.get_exam_type_display() if first_exam else 'N/A',
                    'exam_number': first_exam.exam_number if first_exam else 'N/A',
                    'exam_year': first_exam.exam_year if first_exam else 'N/A',
                },
                'second_sitting': {
                    'exam_type': second_exam.get_exam_type_display() if second_exam else 'N/A',
                    'exam_number': second_exam.exam_number if second_exam else 'N/A',
                    'exam_year': second_exam.exam_year if second_exam else 'N/A',
                }
            },
            'subjects': {
                'first_sitting': [{'subject': s.get_subject_display(), 'grade': s.grade} for s in first_sitting_subjects],
                'second_sitting': [{'subject': s.get_subject_display(), 'grade': s.grade} for s in second_sitting_subjects],
            },
            'program_choices': {
                'first_choice': screening_form.first_choice.name if screening_form.first_choice else 'N/A',
                'second_choice': screening_form.second_choice.name if screening_form.second_choice else 'N/A',
                'third_choice': screening_form.third_choice.name if screening_form.third_choice else 'N/A',
            },
            'applicant_info': {
                'name': applicant.user.get_full_name(),
                'program': applicant.programs.name,
                'mode': applicant.mode,
                'state': applicant.state,
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_student_profile_data(request):
    """Get student profile data for printing"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        
        data = {
            'personal_info': {
                'full_name': request.user.get_full_name(),
                'matriculation_number': request.user.matriculation_number,
                'email': request.user.email,
                'phone_number': request.user.phone_number or 'Not provided',
                'date_of_birth': student_profile.date_of_birth.strftime('%B %d, %Y') if student_profile.date_of_birth else 'Not provided',
                'gender': student_profile.get_gender_display(),
                'state_of_origin': student_profile.state_of_origin,
                'local_government': student_profile.local_government,
                'permanent_address': student_profile.permanent_address or 'Not provided',
            },
            'academic_info': {
                'faculty': student_profile.faculty.name,
                'department': student_profile.department.name,
                'program': student_profile.get_program_display(),
                'admission_year': student_profile.admission_year,
                'current_level': student_profile.current_level.display_name,
                'current_semester': student_profile.get_current_semester_display(),
                'cgpa': float(student_profile.cgpa),
            },
            'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None,
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_student_course_data(request):
    """Get student course data for printing"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        
        # Get registered courses from CourseRegistration (Course has no department/level - those are on CourseOffering)
        from accounts.models import CourseRegistration, AcademicSession
        
        reg_filter = {'student': student_profile, 'status': 'registered'}
        if student_profile.current_session_id:
            reg_filter['course__academic_session'] = student_profile.current_session
        registrations = CourseRegistration.objects.filter(
            **reg_filter
        ).select_related('course').order_by('course__semester', 'course__code')
        
        first_semester_registered = []
        second_semester_registered = []
        
        for reg in registrations:
            course = reg.course
            item = {'code': course.code, 'title': course.title, 'credits': course.credits}
            if course.semester == 'first':
                first_semester_registered.append(item)
            elif course.semester == 'second':
                second_semester_registered.append(item)
        
        # Get current academic session
        current_session = AcademicSession.objects.filter(is_active=True).first()
        session_name = current_session.name if current_session else student_profile.current_session.name if student_profile.current_session else "2023/2024"

        data = {
            'student_info': {
                'name': request.user.get_full_name(),
                'matriculation_number': request.user.matriculation_number,
                'department': student_profile.department.name,
                'level': student_profile.current_level.display_name,
                'semester': student_profile.get_current_semester_display(),
                'faculty': student_profile.faculty.name,
            },
            'academic_session': session_name,
            'courses': {
                'first_semester': first_semester_registered,
                'second_semester': second_semester_registered
            },
            'total_credits': {
                'first_semester': sum(course['credits'] for course in first_semester_registered),
                'second_semester': sum(course['credits'] for course in second_semester_registered),
                'total': sum(course['credits'] for course in first_semester_registered + second_semester_registered)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_pdf(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(StudentProfile, user=user)  # Fetch the StudentProfile associated with the user
    html_string = render_to_string('accounts/student_profile_pdf.html', {'user': user, 'profile': profile})
    html = HTML(string=html_string)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=student_profile_{user.username}.pdf'
    html.write_pdf(response)
    return response