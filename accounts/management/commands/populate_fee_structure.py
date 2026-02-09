from django.core.management.base import BaseCommand
from accounts.models import AcademicSession, Department, Level, FeeStructure


class Command(BaseCommand):
    help = 'Populate initial fee structures for departments and levels'

    def handle(self, *args, **options):
        # Get active academic session
        try:
            current_session = AcademicSession.objects.filter(is_active=True).first()
            if not current_session:
                current_session = AcademicSession.objects.filter(name="2023/2024").first()
            if not current_session:
                self.stdout.write(self.style.ERROR('No academic session found. Please create one first.'))
                return
        except AcademicSession.DoesNotExist:
            self.stdout.write(self.style.ERROR('No academic session found. Please create one first.'))
            return

        # Default fee amounts by level
        default_fees = {
            '100': 150000,  # ₦150,000 for 100 level
            '200': 120000,  # ₦120,000 for 200 level
            '300': 120000,  # ₦120,000 for 300 level
            '400': 120000,  # ₦120,000 for 400 level
        }

        # Get all departments and levels
        departments = Department.objects.all()
        levels = Level.objects.filter(is_active=True)

        if not departments:
            self.stdout.write(self.style.ERROR('No departments found. Please create departments first.'))
            return

        if not levels:
            self.stdout.write(self.style.ERROR('No levels found. Please create levels first.'))
            return

        created_count = 0
        updated_count = 0

        for department in departments:
            for level in levels:
                level_name = level.name
                if level_name in default_fees:
                    fee_amount = default_fees[level_name]

                    # Check if fee structure already exists
                    fee_structure, created = FeeStructure.objects.get_or_create(
                        academic_session=current_session,
                        department=department,
                        level=level,
                        defaults={'amount': fee_amount}
                    )

                    if created:
                        self.stdout.write(
                            f'Created: {fee_structure} - ₦{fee_amount}'
                        )
                        created_count += 1
                    else:
                        # Update existing fee if different
                        if fee_structure.amount != fee_amount:
                            old_amount = fee_structure.amount
                            fee_structure.amount = fee_amount
                            fee_structure.save()
                            self.stdout.write(
                                f'Updated: {fee_structure} - ₦{old_amount} → ₦{fee_amount}'
                            )
                            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Fee structure population completed. Created: {created_count}, Updated: {updated_count}'
            )
        )