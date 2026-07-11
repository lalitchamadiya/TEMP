from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group

from student.models import Student  # import after settings configured


class Command(BaseCommand):
    help = 'Insert a student from the command line'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)
        parser.add_argument('--name', type=str, default='')
        parser.add_argument('--gender', type=str, choices=[c[0] for c in Student.GENDER_CHOICES], default='')
        parser.add_argument('--phone', type=str, default='')
        # add other options as needed

    def handle(self, *args, **options):
        email = options['email']
        if Student.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise CommandError('A student/user with this email already exists.')

        user = User.objects.create_user(
            username=email,
            email=email,
            password='default123',
        )
        group, _ = Group.objects.get_or_create(name='Students')
        user.groups.add(group)

        student = Student(
            user=user,
            email=email,
            name=options['name'],
            gender=options['gender'],
            phone_number=options['phone'],
        )
        student.save()
        self.stdout.write(self.style.SUCCESS(f'Student {email} created.'))