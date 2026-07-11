import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from authentication.models import Role, RolePermission, Module, UserProfile


class Command(BaseCommand):
    help = 'Auto-creates a superuser (if none exists) and seeds the Super Admin role with all permissions.'

    def handle(self, *args, **options):
        # 1. Ensure Super Admin role exists
        role, created = Role.objects.get_or_create(
            name='Super Admin',
            defaults={
                'description': 'Root administrative role with absolute unrestricted permissions across the system.',
                'is_active': True,
                'is_superadmin': True
            }
        )
        if not created:
            role.is_superadmin = True
            role.is_active = True
            role.save()

        # 2. Grant all permissions to Super Admin for every module
        modules = Module.objects.all()
        for module in modules:
            rp, _ = RolePermission.objects.get_or_create(role=role, module=module)
            rp.can_view = True
            rp.can_add = True
            rp.can_edit = True
            rp.can_delete = True
            rp.can_approve = True
            rp.can_reject = True
            rp.can_export = True
            rp.can_print = True
            rp.can_import = True
            rp.can_hide = True
            rp.can_disable = True
            rp.save()

        # 3. Auto-create superuser from environment variables if none exists
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@1234')

            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Superuser '{username}' created automatically."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Superuser '{user.username}' already exists — skipping creation."
            ))

        if user:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            group, _ = Group.objects.get_or_create(name='Super Admin')
            group.user_set.add(user)

            self.stdout.write(self.style.SUCCESS(
                f"Successfully linked superuser '{user.username}' to 'Super Admin' role and system group."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "No django superuser found. Please create one with 'python manage.py createsuperuser' then re-run this."
            ))
        
        self.stdout.write(self.style.SUCCESS(
            "Successfully seeded Super Admin role and granted all permissions."
        ))
