from django.contrib import admin
from .models import ContactSubmission, Applicant, Program, ProgramChoice, ScreeningForm, AcademicSubject, ExaminationDetail, ScreeningPayment

# Register Program only
admin.site.register([Program])

@admin.register(ProgramChoice)
class ProgramChoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'program_type', 'is_active', 'created_at')
    list_filter = ('program_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('program_type', 'name')
    fields = ('program_type', 'name', 'description', 'is_active')

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    search_fields = ('name', 'email')
    readonly_fields = ('name', 'email', 'message', 'submitted_at')
    list_filter = ('submitted_at',)

class AcademicSubjectInline(admin.TabularInline):
    model = AcademicSubject
    extra = 0
    fields = ('subject', 'grade', 'sitting')

class ExaminationDetailInline(admin.TabularInline):
    model = ExaminationDetail
    extra = 0
    fields = ('sitting', 'exam_type', 'exam_number', 'exam_year')

@admin.register(ExaminationDetail)
class ExaminationDetailAdmin(admin.ModelAdmin):
    list_display = ('screening_form', 'sitting', 'exam_type', 'exam_number', 'exam_year')
    list_filter = ('sitting', 'exam_type', 'exam_year')
    search_fields = ('screening_form__first_name', 'screening_form__surname', 'exam_number')
    ordering = ('screening_form', 'sitting')

@admin.register(AcademicSubject)
class AcademicSubjectAdmin(admin.ModelAdmin):
    list_display = ('screening_form', 'subject', 'grade', 'sitting')
    list_filter = ('sitting', 'subject', 'grade')
    search_fields = ('screening_form__first_name', 'screening_form__surname', 'subject')
    ordering = ('screening_form', 'sitting', 'subject')

@admin.register(ScreeningForm)
class ScreeningFormAdmin(admin.ModelAdmin):
    list_display = (
        'applicant', 
        'first_name', 
        'surname',
        'jamb_reg_no',
        'jamb_score',
        'state_of_origin',
        'local_government',
        'academic_subjects_summary',
        'examination_summary',
        'created_at'
    )
    list_filter = (
        'state_of_origin',
        'created_at'
    )
    search_fields = (
        'first_name',
        'surname',
        'jamb_reg_no',
        'email',
        'phone_number'
    )
    readonly_fields = ('created_at', 'updated_at', 'academic_subjects_summary', 'examination_summary')
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('academic_subjects', 'examination_details')
    
    def academic_subjects_summary(self, obj):
        """Display a summary of academic subjects"""
        first_sitting = obj.get_first_sitting_subjects()
        second_sitting = obj.get_second_sitting_subjects()
        
        summary = []
        if first_sitting:
            summary.append(f"First Sitting: {', '.join([f'{s.subject}({s.grade})' for s in first_sitting])}")
        if second_sitting:
            summary.append(f"Second Sitting: {', '.join([f'{s.subject}({s.grade})' for s in second_sitting])}")
        
        return ' | '.join(summary) if summary else 'No subjects added'
    
    def examination_summary(self, obj):
        """Display a summary of examination details"""
        first_exam = obj.get_first_sitting_examination()
        second_exam = obj.get_second_sitting_examination()
        
        summary = []
        if first_exam:
            summary.append(f"First: {first_exam.get_exam_type_display()}({first_exam.exam_year})")
        if second_exam:
            summary.append(f"Second: {second_exam.get_exam_type_display()}({second_exam.exam_year})")
        
        return ' | '.join(summary) if summary else 'No exams added'
    
    academic_subjects_summary.short_description = 'Academic Subjects'
    examination_summary.short_description = 'Examinations'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'surname', 'date_of_birth', 'sex', 'state_of_origin', 'local_government', 'email', 'phone_number', 'contact_address')
        }),
        ('JAMB Details', {
            'fields': ('jamb_reg_no', 'jamb_score')
        }),
        ('Academic Information', {
            'fields': ('primary_school', 'primary_school_dates', 'secondary_school', 'secondary_school_dates')
        }),
        ('Program Choices', {
            'fields': ('first_choice', 'second_choice', 'third_choice')
        }),
        ('Documents', {
            'fields': ('waec_result', 'jamb_result_slip', 'birth_certificate', 'passport_photo', 'declaration')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [AcademicSubjectInline, ExaminationDetailInline]


@admin.register(ScreeningPayment)
class ScreeningPaymentAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'amount', 'reference', 'status', 'payment_date', 'verified_at')
    list_filter = ('status', 'payment_date', 'verified_at')
    search_fields = ('applicant__user__first_name', 'applicant__user__last_name', 'reference', 'paystack_reference')
    readonly_fields = ('payment_date', 'verified_at')
    ordering = ('-payment_date',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('applicant', 'amount', 'reference', 'paystack_reference', 'status')
        }),
        ('Timestamps', {
            'fields': ('payment_date', 'verified_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('applicant__user')

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'state')
    search_fields = ('user__username', 'user__email', 'phone_number')