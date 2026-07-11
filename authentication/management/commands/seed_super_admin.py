import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from authentication.models import Role, RolePermission, Module, UserProfile


class Command(BaseCommand):
    help = 'Auto-creates a superuser (if none exists) and seeds the Super Admin role with all permissions.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=== seed_super_admin starting ==='))

        # 1. Ensure Super Admin role exists
        role, created = Role.objects.get_or_create(
            name='Super Admin',
            defaults={
                'description': 'Root administrative role with absolute unrestricted permissions across the system.',
                'is_active': True,
                'is_superadmin': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created 'Super Admin' role."))
        else:
            role.is_superadmin = True
            role.is_active = True
            role.save()
            self.stdout.write(self.style.SUCCESS("✓ 'Super Admin' role already exists — updated."))

        # 2. Grant all permissions to Super Admin for every module
        modules = Module.objects.all()
        module_count = modules.count()
        if module_count == 0:
            self.stdout.write(self.style.WARNING(
                "⚠ No modules found — run 'seed_modules' first. Role permissions skipped."
            ))
        else:
            for module in modules:
                rp, _ = RolePermission.objects.get_or_create(role=role, module=module)
                rp.can_view = rp.can_add = rp.can_edit = rp.can_delete = True
                rp.can_approve = rp.can_reject = rp.can_export = rp.can_print = True
                rp.can_import = rp.can_hide = rp.can_disable = True
                rp.save()
            self.stdout.write(self.style.SUCCESS(
                f"✓ Granted all permissions across {module_count} modules."
            ))

        # 3. Auto-create superuser from environment variables if none exists
        superusers = User.objects.filter(is_superuser=True)
        if not superusers.exists():
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@1234')

            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            superusers = User.objects.filter(is_superuser=True)
            self.stdout.write(self.style.SUCCESS(
                f"✓ Superuser '{username}' created automatically from environment variables."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"✓ {superusers.count()} superuser(s) already exist — skipping creation."
            ))

        # 4. Link ALL superusers to Super Admin role + group
        group, _ = Group.objects.get_or_create(name='Super Admin')
        for user in superusers:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            group.user_set.add(user)
            self.stdout.write(self.style.SUCCESS(
                f"✓ Linked '{user.username}' → Super Admin role & group."
            ))

        self.stdout.write(self.style.HTTP_INFO('=== seed_super_admin complete ==='))
