from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import User, StaffProfile, StudentProfile, AcademicRecord, PaymentTransaction, Faculty, Department, Course, CourseRegistration, Enrollment, Verification, AcademicSession, Level, FeeStructure

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
    list_display = ['user', 'faculty', 'department', 'current_level', 'current_semester', 'current_session', 'cgpa']
    search_fields = ['user__username', 'user__matriculation_number', 'user__email']
    list_filter = ('faculty', 'department', 'current_level', 'current_semester', 'current_session', 'state_of_origin')
    ordering = ('user__username',)
    list_editable = ('current_level', 'current_semester', 'current_session', 'cgpa')

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
    list_display = ('code', 'title', 'level', 'academic_session', 'department', 'semester', 'credits', 'is_active', 'created_at')
    search_fields = ('code', 'title', 'department__name')
    list_filter = ('level', 'academic_session', 'department', 'semester', 'is_active')
    list_editable = ('is_active',)

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
    search_fields = ('student__user__username', 'student__user__matriculation_number', 'session', 'semester')
    list_filter = ('status', 'session', 'semester', 'payment_type')
    list_editable = ('status',)

# Academic Session Admin
@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_year', 'end_year', 'session_type', 'is_active', 'start_date', 'end_date')
    list_filter = ('session_type', 'is_active', 'start_year')
    search_fields = ('name',)
    ordering = ('-start_year', '-end_year')

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-start_year', '-end_year')

# Level Admin
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'display_name')
    ordering = ('order',)

# Fee Structure Admin
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('academic_session', 'department', 'level', 'amount')
    list_filter = ('academic_session', 'department', 'level')
    search_fields = ('academic_session__name', 'department__name', 'level__display_name')
    ordering = ('academic_session', 'department', 'level')
    list_editable = ('amount',)