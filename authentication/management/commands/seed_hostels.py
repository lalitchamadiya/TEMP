from django.core.management.base import BaseCommand
from authentication.models import Hostel
from room.models import HostelBuilding, Room
from student.models import Student
from hms.models import StaffProfile

class Command(BaseCommand):
    help = 'Seed default Central Hostel and associate existing hostelless records'

    def handle(self, *args, **options):
        self.stdout.write("Seeding default Hostel...")
        default_hostel, created = Hostel.objects.get_or_create(
            name="Central Hostel",
            defaults={
                'address': '123 University Campus, Academic Block Road',
                'phone_number': '+1-555-0199',
                'email': 'central.hostel@university.edu',
                'theme_color': '#0d6efd'
            }
        )
        if created:
            self.stdout.write("Created 'Central Hostel'.")
        else:
            self.stdout.write("'Central Hostel' already exists.")

        # Update buildings
        buildings_updated = HostelBuilding.objects.filter(hostel__isnull=True).update(hostel=default_hostel)
        self.stdout.write(f"Updated {buildings_updated} HostelBuildings.")

        # Update rooms
        rooms_updated = Room.objects.filter(hostel__isnull=True).update(hostel=default_hostel)
        self.stdout.write(f"Updated {rooms_updated} Rooms.")

        # Update students
        students_updated = Student.objects.filter(hostel__isnull=True).update(hostel=default_hostel)
        self.stdout.write(f"Updated {students_updated} Students.")

        # Update staff profiles
        staff_updated = StaffProfile.objects.filter(hostel__isnull=True).update(hostel=default_hostel)
        self.stdout.write(f"Updated {staff_updated} StaffProfiles.")

        self.stdout.write(self.style.SUCCESS("Hostel seeding complete!"))
