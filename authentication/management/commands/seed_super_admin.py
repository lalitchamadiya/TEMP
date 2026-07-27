"""
Management command: seed_super_admin
=====================================
Creates (or updates) the Super Admin role, grants it full permissions on every
module, and ensures at least one superuser exists that is linked to that role.

Usage examples
--------------
# Use environment variables / built-in defaults
python manage.py seed_super_admin

# Pass credentials directly
python manage.py seed_super_admin --username root --email root@example.com --password Secret@99

# Force-recreate the superuser even if one already exists
python manage.py seed_super_admin --force

Environment variables (fallback when CLI flags are not provided)
----------------------------------------------------------------
  DJANGO_SUPERUSER_USERNAME   (default: admin)
  DJANGO_SUPERUSER_EMAIL      (default: admin@hostel.local)
  DJANGO_SUPERUSER_PASSWORD   (default: Admin@1234)
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db import transaction

from authentication.models import Module, Role, RolePermission, UserProfile


# ---------------------------------------------------------------------------
# Defaults (lowest priority – overridden by env vars / CLI flags)
# ---------------------------------------------------------------------------
DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL    = "admin@hostel.local"
DEFAULT_PASSWORD = "Admin@1234"


class Command(BaseCommand):
    help = (
        "Seeds the Super Admin role with full permissions on every module "
        "and ensures at least one superuser account is linked to it."
    )

    # ------------------------------------------------------------------
    # CLI argument definitions
    # ------------------------------------------------------------------
    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            dest="username",
            default=None,
            help=(
                "Username for the superuser account. "
                "Falls back to $DJANGO_SUPERUSER_USERNAME or 'admin'."
            ),
        )
        parser.add_argument(
            "--email",
            dest="email",
            default=None,
            help=(
                "E-mail for the superuser account. "
                "Falls back to $DJANGO_SUPERUSER_EMAIL or 'admin@hostel.local'."
            ),
        )
        parser.add_argument(
            "--password",
            dest="password",
            default=None,
            help=(
                "Password for the superuser account. "
                "Falls back to $DJANGO_SUPERUSER_PASSWORD or 'Admin@1234'."
            ),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            default=False,
            help=(
                "If a superuser already exists, create an additional one using "
                "the supplied credentials instead of skipping creation."
            ),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve(self, cli_value: str | None, env_key: str, default: str) -> str:
        """Return the first non-None value: CLI flag → env var → hard-coded default."""
        if cli_value is not None:
            return cli_value
        return os.environ.get(env_key, default)

    def _ok(self, msg: str):
        self.stdout.write(self.style.SUCCESS(f"  [OK]   {msg}"))

    def _warn(self, msg: str):
        self.stdout.write(self.style.WARNING(f"  [WARN] {msg}"))

    def _info(self, msg: str):
        self.stdout.write(self.style.HTTP_INFO(f"  [-->]  {msg}"))

    def _section(self, title: str):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"[ {title} ]"))

    # ------------------------------------------------------------------
    # Main handler
    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 55))
        self.stdout.write(self.style.MIGRATE_HEADING("   seed_super_admin  --  Hostel Management System"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 55))

        with transaction.atomic():
            role         = self._seed_role()
            self._seed_permissions(role)
            user         = self._seed_superuser(options)
            self._link_superusers(role)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 55))
        self.stdout.write(self.style.SUCCESS("  seed_super_admin  completed successfully."))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 55))

    # ------------------------------------------------------------------
    # Step 1 – Role
    # ------------------------------------------------------------------
    def _seed_role(self) -> Role:
        self._section("Step 1 / 4  --  Super Admin Role")

        role, created = Role.objects.get_or_create(
            name="Super Admin",
            defaults={
                "description": (
                    "Root administrative role with unrestricted access "
                    "to every module and action in the system."
                ),
                "is_active":     True,
                "is_superadmin": True,
            },
        )

        if created:
            self._ok("'Super Admin' role created.")
        else:
            # Ensure flags are correct even on existing records
            updated = False
            if not role.is_superadmin:
                role.is_superadmin = True
                updated = True
            if not role.is_active:
                role.is_active = True
                updated = True
            if updated:
                role.save(update_fields=["is_superadmin", "is_active"])
                self._ok("'Super Admin' role already existed - flags corrected.")
            else:
                self._ok("'Super Admin' role already exists and is up-to-date.")

        return role

    # ------------------------------------------------------------------
    # Step 2 – Module permissions
    # ------------------------------------------------------------------
    def _seed_permissions(self, role: Role) -> None:
        self._section("Step 2 / 4  --  Module Permissions")

        modules = Module.objects.all()
        total   = modules.count()

        if total == 0:
            self._warn(
                "No modules found in the database.  "
                "Run  python manage.py seed_modules  first, then re-run this command."
            )
            return

        ALL_PERMS = dict(
            can_view=True, can_add=True, can_edit=True, can_delete=True,
            can_approve=True, can_reject=True, can_export=True, can_print=True,
            can_import=True, can_hide=True, can_disable=True,
        )

        created_count = updated_count = 0
        for module in modules:
            rp, created = RolePermission.objects.get_or_create(
                role=role, module=module, defaults=ALL_PERMS
            )
            if not created:
                # Ensure every permission flag is True
                changed = False
                for field, value in ALL_PERMS.items():
                    if getattr(rp, field) != value:
                        setattr(rp, field, value)
                        changed = True
                if changed:
                    rp.save(update_fields=list(ALL_PERMS.keys()))
                    updated_count += 1
            else:
                created_count += 1

        self._ok(
            f"Processed {total} module(s) - "
            f"{created_count} created, {updated_count} updated, "
            f"{total - created_count - updated_count} already complete."
        )

    # ------------------------------------------------------------------
    # Step 3 – Superuser account
    # ------------------------------------------------------------------
    def _seed_superuser(self, options: dict) -> User | None:
        self._section("Step 3 / 4  --  Superuser Account")

        username = self._resolve(options["username"], "DJANGO_SUPERUSER_USERNAME", DEFAULT_USERNAME)
        email    = self._resolve(options["email"],    "DJANGO_SUPERUSER_EMAIL",    DEFAULT_EMAIL)
        password = self._resolve(options["password"], "DJANGO_SUPERUSER_PASSWORD", DEFAULT_PASSWORD)
        force    = options["force"]

        # Show which credential source is being used (mask password)
        self._info(f"Username : {username}")
        self._info(f"E-mail   : {email}")
        self._info(f"Password : {'*' * len(password)}")

        existing_superusers = User.objects.filter(is_superuser=True)

        if existing_superusers.exists() and not force:
            self._ok(
                f"{existing_superusers.count()} superuser(s) already exist. "
                "Use --force to add another one."
            )
            return None

        # Check for duplicate username
        if User.objects.filter(username=username).exists():
            if force:
                raise CommandError(
                    f"Username '{username}' already exists. "
                    "Choose a different --username or remove the existing account first."
                )

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self._ok(f"Superuser '{username}' created with e-mail '{email}'.")
        return user

    # ------------------------------------------------------------------
    # Step 4 -- Link all superusers to role + group
    # ------------------------------------------------------------------
    def _link_superusers(self, role: Role) -> None:
        self._section("Step 4 / 4  --  Linking Superusers >> Role & Group")

        group, group_created = Group.objects.get_or_create(name="Super Admin")
        if group_created:
            self._ok("'Super Admin' Django group created.")

        superusers = User.objects.filter(is_superuser=True)

        for user in superusers:
            # Ensure UserProfile exists and is assigned the Super Admin role
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.role != role:
                profile.role = role
                profile.save(update_fields=["role"])

            # Add to Django group (idempotent)
            group.user_set.add(user)

            self._ok(f"'{user.username}' >> Super Admin role & group.")

        if not superusers.exists():
            self._warn("No superuser accounts found to link.")
