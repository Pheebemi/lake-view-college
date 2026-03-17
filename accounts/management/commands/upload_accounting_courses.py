import os
from django.core.management.base import BaseCommand
from accounts.models import (
    Faculty, Department, Level, AcademicSession, Course, CourseOffering, User
)

class Command(BaseCommand):
    help = "Upload 200 Level Accounting courses for First and Second Semesters"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the script without saving changes to the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved."))

        # 1. Ensure Faculty and Department exist
        faculty, f_created = Faculty.objects.get_or_create(
            short_name="FOMS",
            programme_type="degree",
            defaults={"name": "Faculty of Management Sciences"}
        )
        if f_created:
            self.stdout.write(f"Created Faculty: {faculty.name}")

        dept, d_created = Department.objects.get_or_create(
            faculty=faculty,
            short_name="ACC",
            defaults={"name": "Accounting"}
        )
        if d_created:
            self.stdout.write(f"Created Department: {dept.name}")

        # 2. Get Level and Session
        level = Level.objects.filter(name="200").first()
        if not level:
            self.stdout.write(self.style.ERROR("Level '200' not found! Please ensure levels are seeded."))
            return

        session = AcademicSession.objects.filter(is_active=True).first()
        if not session:
            self.stdout.write(self.style.ERROR("No active Academic Session found!"))
            return

        admin_user = User.objects.filter(is_superuser=True).first()

        # 3. Define Course Data
        courses_data = [
            # First Semester
            {"code": "ENT 211", "title": "Entrepreneurship and Innovation", "units": 2, "semester": "first"},
            {"code": "ACS 201", "title": "Differential Calculus for Actuarial Science", "units": 3, "semester": "first"},
            {"code": "ACS 203", "title": "Mathematical Statistics for Actuarial Science", "units": 3, "semester": "first"},
            {"code": "ACS 205", "title": "Introductory Actuarial Finance", "units": 2, "semester": "first"},
            {"code": "ACS 207", "title": "Economics of Insurance", "units": 3, "semester": "first"},
            {"code": "LCE--ACC207", "title": "Statistics for Accounting I", "units": 3, "semester": "first"},
            {"code": "LCE--ACC209", "title": "Accounting Information System", "units": 2, "semester": "first"},
            {"code": "LCE--ACC211", "title": "Financial Technology (FIN TECH)", "units": 2, "semester": "first"},
            # Second Semester
            {"code": "GST 212", "title": "Philosophy, Logic, and human existence", "units": 2, "semester": "second"},
            {"code": "ACS 202", "title": "Integral Calculus for Actuarial Science", "units": 3, "semester": "second"},
            {"code": "ACS 204", "title": "Probability Theory for Actuarial Science", "units": 3, "semester": "second"},
            {"code": "ACS 206", "title": "Mathematics of Demography", "units": 2, "semester": "second"},
            {"code": "ACS 208", "title": "Risk Management", "units": 3, "semester": "second"},
            {"code": "LCE--ACC208", "title": "Statistics for Accounting II", "units": 3, "semester": "second"},
            {"code": "LCE--ACC210", "title": "Agricultural Accounting", "units": 2, "semester": "second"},
        ]

        # 4. Process Courses
        for c in courses_data:
            course_code = c["code"]
            course_title = c["title"]
            units = c["units"]
            semester = c["semester"]

            if dry_run:
                self.stdout.write(f"[DRY-RUN] Processing {course_code}: {course_title} ({units} Units, {semester})")
                continue

            # Create or Update Course
            course, created = Course.objects.update_or_create(
                code=course_code,
                defaults={
                    "title": course_title,
                    "credits": units,
                    "semester": semester,
                    "academic_session": session,
                    "created_by": admin_user
                }
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} Course: {course.code}")

            # Create Course Offering
            offering, o_created = CourseOffering.objects.get_or_create(
                course=course,
                department=dept,
                level=level,
                defaults={"is_active": True}
            )
            if o_created:
                self.stdout.write(f"   Linked {course.code} to {dept.name} @ {level.display_name}")
            else:
                self.stdout.write(f"   Offering already exists for {course.code} in {dept.name}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("\nSuccessfully processed all Accounting courses."))
