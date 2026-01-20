from django.contrib.auth.models import AbstractUser
from django.db import models
from .state import NIGERIA_STATES_AND_LGAS
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
        ('applicant', 'Applicant')
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    matriculation_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Only applicable for students and staff."
    )
    

    def clean(self):
        """
        Custom validation to ensure matriculation_number is only set for students or staff.
        """
        if self.user_type not in ['student', 'staff'] and self.matriculation_number:
            raise ValidationError("Matriculation number can only be set for students or staff.")

    def save(self, *args, **kwargs):
        self.clean()  # Call the clean method for validation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.user_type})"
    
    
class Faculty(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30)
    image = models.ImageField(upload_to='faculty/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def faculty_img(self):
        if self.image:
            return self.image.url
        else:
            return 'https://fakeimg.pl/600x400'
    
    class Meta:
        verbose_name_plural = 'Faculties'
class Department(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, related_name='departments', on_delete=models.CASCADE)
    # description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('present', 'Present'), ('absent', 'Absent')])

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.date} - {self.status}"

class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    short_name = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class StudentProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    )
    PROGRAM_CHOICES = (
        ('BSc', 'Bachelor of Science'),
        ('BA', 'Bachelor of Arts'),
        ('BEng', 'Bachelor of Engineering'),
        ('LLB', 'Bachelor of Laws'),
        ('MBBS', 'Bachelor of Medicine, Bachelor of Surgery'),
        ('PharmD', 'Doctor of Pharmacy'),
        ('BBA', 'Bachelor of Business Administration'),
        ('BCom', 'Bachelor of Commerce'),
        ('BEd', 'Bachelor of Education'),
        ('BFA', 'Bachelor of Fine Arts'),
        ('BPharm', 'Bachelor of Pharmacy'),
        ('BTech', 'Bachelor of Technology'),
        ('BVSc', 'Bachelor of Veterinary Science'),
    )
    SEMESTER_CHOICES = (
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
    )
    NIGERIAN_STATES = [(state, state) for state in NIGERIA_STATES_AND_LGAS.keys()]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='user_faculty', default=1)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='user_department', default=1)
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES)
    admission_year = models.CharField(max_length=10, choices=[(str(year), str(year)) for year in range(1900, 2101)])
    current_level = models.CharField(max_length=6, choices=(
        ('100', '100'),
        ('200', '200'),
        ('300', '300'),
        ('400', '400'),
    ))
    current_semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, default='first')
    permanent_address = models.CharField(max_length=100, blank=True, null=True)
    state_of_origin = models.CharField(max_length=100, choices=NIGERIAN_STATES, verbose_name="State of Origin")
    local_government = models.CharField(max_length=100, verbose_name="Local Government")
    cgpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.user.matriculation_number}"

class AcademicRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10, choices=(
        ('first', 'first'),
        ('second', 'second')
    ))
    year = models.CharField(max_length=10, choices=[(str(year), str(year)) for year in range(1900, 2101)])
    courses = models.ManyToManyField("Course", related_name='academic_courses')  
    semester_gpa = models.DecimalField(max_digits=3, decimal_places=2)
    
    def __str__(self):
        return f"{self.student.user.username} - Semester {self.semester} {self.year}"
    
    
    
class StaffProfile(models.Model):
    STAFF_TYPE_CHOICES = (
        ('academic', 'Academic Staff'),
        ('non_academic', 'Non-Academic Staff')
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPE_CHOICES)
    
    # For Academic Staff
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='staff_faculty')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='staff_department')
    qualification = models.CharField(max_length=100)
    
    # Additional Staff Details
    date_employed = models.DateField(blank=True, null=True)
    is_head_of_department = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.staff_id}"



# Course Model
class Course(models.Model):
    SEMESTER_CHOICES = (
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
    )
    LEVEL_CHOICES = (
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
    )
    
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        unique_together = ['code', 'department']

    def __str__(self):
        return f"{self.code} - {self.title}"

# Course Registration Model
class CourseRegistration(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('registered', 'Registered'),
            ('dropped', 'Dropped'),
            ('completed', 'Completed')
        ],
        default='registered'
    )

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.course.title}"

    class Meta:
        unique_together = ('student', 'course')  # Prevent duplicate registrations

class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10, choices=(
        ('first', 'first'),
        ('second', 'second')
    ))
    year = models.CharField(max_length=10, choices=[(str(year), str(year)) for year in range(1900, 2101)])
    grade = models.CharField(max_length=2, blank=True, null=True)
    
    class Meta:
        unique_together = ('student', 'course', 'semester', 'year')

class Verification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_type = models.CharField(max_length=20)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_document = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - Verification Status"

class PaymentTransaction(models.Model):
    PAYMENT_TYPES = (
        ('school_fees', 'School Fees'),
        ('acceptance_fees', 'Acceptance Fees'),
        ('other', 'Other Fees'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    session = models.CharField(max_length=10)  # e.g., "2023/2024"
    semester = models.CharField(max_length=10, choices=StudentProfile.SEMESTER_CHOICES)
    payment_date = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.payment_type} - {self.session}"
    
    class Meta:
        ordering = ['-payment_date']

