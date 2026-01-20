from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import StudentProfile, StaffProfile, Faculty, Department
import random
import string

User = get_user_model()

def generate_unique_id(prefix, length=10):
    """
    Generate a unique identifier for matriculation or staff ID.
    """
    while True:
        # Generate random alphanumeric string
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        full_id = f"{prefix}{random_part}"
        
        # Check uniqueness based on user type
        if prefix.startswith('ST'):  # Student
            if not User.objects.filter(matriculation_number=full_id).exists():
                return full_id
        elif prefix.startswith('SF'):  # Staff
            if not StaffProfile.objects.filter(staff_id=full_id).exists():
                return full_id

import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.user_type == 'student':
                # Generate matriculation number and assign it to the user
                instance.matriculation_number = generate_unique_id('ST')
                instance.save()

                # Assign default faculty and department
                default_faculty = Faculty.objects.first()
                if not default_faculty:
                    default_faculty = Faculty.objects.create(name="Default Faculty", short_name="DF")

                default_department = Department.objects.filter(faculty=default_faculty).first()
                if not default_department:
                    default_department = Department.objects.create(
                        faculty=default_faculty, name="Default Department", short_name="DD"
                    )

                # Create student profile
                StudentProfile.objects.create(
                    user=instance,
                    date_of_birth=None,
                    gender='',
                    faculty=default_faculty,
                    department=default_department,
                    program='BSc',
                    admission_year='2024',
                    current_level='100',
                    permanent_address='',
                    local_government='',
                    state_of_origin='',
                    cgpa=0.00
                )

            elif instance.user_type == 'staff':
                # Generate staff ID and assign it to the profile
                staff_id = generate_unique_id('SF')

                # Assign default faculty and department
                default_faculty = Faculty.objects.first()
                if not default_faculty:
                    default_faculty = Faculty.objects.create(name="Default Faculty", short_name="DF")

                default_department = Department.objects.filter(faculty=default_faculty).first()
                if not default_department:
                    default_department = Department.objects.create(
                        faculty=default_faculty, name="Default Department", short_name="DD"
                    )

                # Create staff profile
                StaffProfile.objects.create(
                    user=instance,
                    staff_id=staff_id,
                    staff_type='academic',
                    faculty=default_faculty,
                    department=default_department,
                    qualification='',
                    date_employed=None,
                    is_head_of_department=False
                )

        except Exception as e:
            # Log the error
            logger.error(f"Error creating profile for {instance.username}: {e}")
            # Reraise the exception to avoid leaving the transaction in a broken state
            raise
