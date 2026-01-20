from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import User, StaffProfile, StudentProfile, AcademicRecord, PaymentTransaction, Faculty, Department, Course, CourseRegistration, Enrollment, Verification

# Customizing the User Admin
@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    model = User
    # Fields to display in the user list view
    list_display = ('username', 'email', 'user_type', 'matriculation_number', 'is_verified')
    list_filter = ('user_type', 'is_verified')
    search_fields = ('username', 'email', 'matriculation_number')

    # Sections for editing a user
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'email', 'user_type', 'is_verified')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2')
        }),
    )

    ordering = ('username',)  # Default ordering

# Customizing StudentProfile Admin
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'faculty', 'cgpa','department', 'current_level']
    search_fields = ['user__username']
    list_filter = ('faculty', 'department', 'current_level', 'state_of_origin')  # Add filters for easy navigation
    ordering = ('user',)  # Default ordering
    list_editable = ('faculty', 'department', 'current_level', 'cgpa')  # Make specific fields editable in the list view

# Customizing StaffProfile Admin
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'faculty', 'department', 'staff_type', 'is_head_of_department')
    list_filter = ('faculty', 'department', 'staff_type', 'is_head_of_department')
    search_fields = ('user__username', 'staff_id', 'user__email')

# Faculty Admin
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'created_at')
    search_fields = ('name', 'short_name')

# Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'faculty', 'created_at')
    list_filter = ('faculty',)
    search_fields = ('name', 'short_name', 'faculty__name')

# Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'credits', 'semester', 'created_at')
    search_fields = ('code', 'title')
    list_filter = ('semester',)

@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'registration_date', 'status')
    search_fields = ('student__username', 'course__title')
    list_filter = ('status',)

# AcademicRecord Admin
@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'year', 'semester_gpa')
    list_filter = ('semester', 'year')
    search_fields = ('student__user__username', 'student__matriculation_number')

# Enrollment Admin
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'year', 'grade')
    list_filter = ('semester', 'year', 'grade')
    search_fields = ('student__user__username', 'course__course_name')

# Verification Admin
@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_type', 'is_verified', 'verification_date', 'verified_by')
    list_filter = ('is_verified', 'verification_type')
    search_fields = ('user__username', 'verified_by__user__username')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['student', 'payment_type', 'amount', 'reference', 'status', 'session']
    search_fields = ('student', 'session', 'semester')
    list_filter = ('status', 'session')
    list_editable = ('session', 'payment_type')