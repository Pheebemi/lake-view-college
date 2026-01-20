from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import StudentProfile, AcademicRecord, Course
from .decorators import student_required, staff_required
from datetime import datetime
from django.contrib import messages
from .models import SupportRequest, Notification
from .forms import SupportForm
from django.contrib.auth.decorators import login_required

# Create your views here.
@student_required
def student_dashboard(request):
    profile = StudentProfile.objects.get(user=request.user)
    record = AcademicRecord.objects.filter(student=profile)
    current_year = datetime.now().year
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    context = {
        'profile': profile,
        'record': record,
        'current_year': current_year,
        'notifications': notifications,
    }
    return render(request, 'dashboard/student-dashboard.html', context)

@student_required
def courses(request):
    profile = StudentProfile.objects.get(user=request.user)
    record = AcademicRecord.objects.filter(student=profile)
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    courses = [record.course for record in record if record.course]
    count = len(courses)
    context = {
        'record': record,
        'profile': profile,
        'current_year' : current_year,
        'count': count,
        'notifications': notifications,
    }
    return render(request, 'dashboard/courses.html', context)

@student_required
def timetable(request):
    profile = StudentProfile.objects.get(user=request.user)
    record = AcademicRecord.objects.filter(student=profile)
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    context = {
        'record': record,
        'notifications': notifications,
    }
    return render(request, 'dashboard/timetable.html', context)

@staff_required
def staff_dashboard(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    department = request.user.staffprofile.department  # Assuming staff has a profile with a department field
    total_students = StudentProfile.objects.filter(department=department).count()
    total_courses = Course.objects.filter(department=department).count()
    context = {
        'notifications': notifications,
        'total_students': total_students,
        'total_courses': total_courses,
    }
    return render(request, 'dashboard/staff-dashboard.html', context)

@login_required
def support(request):
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            support_request = form.save(commit=False)
            support_request.user = request.user
            support_request.save()
            messages.success(request, 'Your support request has been submitted successfully.')
            
            # Redirect based on user role
            if request.user.user_type == 'staff':
                return redirect('dashboard:staff_dashboard')
            else:
                return redirect('dashboard:student_dashboard')
        else:
            messages.error(request, 'There was an error submitting your support request. Please try again.')
    else:
        form = SupportForm()
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    return render(request, 'dashboard/support.html', {'form': form, 'notifications': notifications})

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    count = notifications.count()
    context = {
        'notifications': notifications,
        'count': count, 

    }
    return render(request, 'dashboard/notifications.html', context)

@login_required
def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    return redirect('dashboard:notifications')

@login_required
def support_request_detail(request, support_request_id):
    support_request = get_object_or_404(SupportRequest, id=support_request_id, user=request.user)
    return render(request, 'dashboard/support_request_detail.html', {'support_request': support_request})