from django.core.management.base import BaseCommand
from authentication.models import Module


class Command(BaseCommand):
    help = 'Seeds all system modules with their metadata for dynamic RBAC and navigation, removing defunct ones.'

    def handle(self, *args, **options):
        # Module list matching code and names in the existing DB
        modules_data = [
            {
                'code': 'user_management',
                'name': 'User Management',
                'menu_label': 'User Management',
                'icon': 'bi-people',
                'url_name': 'user_management',
                'order': 10,
                'parent_code': ''
            },
            {
                'code': 'rbac',
                'name': 'Role Management',
                'menu_label': 'Role Management',
                'icon': 'bi-key',
                'url_name': 'role_list',
                'order': 15,
                'parent_code': ''
            },
            {
                'code': 'student',
                'name': 'Student Management',
                'menu_label': 'Student Registry',
                'icon': 'bi-people',
                'url_name': 'student_list',
                'order': 20,
                'parent_code': ''
            },
            {
                'code': 'room',
                'name': 'Room Allocation',
                'menu_label': 'Rooms & Beds',
                'icon': 'bi-house',
                'url_name': 'room_base',
                'order': 30,
                'parent_code': ''
            },
            {
                'code': 'paybill',
                'name': 'Payments & Billing',
                'menu_label': 'Fees & Invoices',
                'icon': 'bi-wallet2',
                'url_name': 'paybill_base',
                'order': 40,
                'parent_code': ''
            },
            {
                'code': 'leave',
                'name': 'Leave Requests',
                'menu_label': 'Leave Requests',
                'icon': 'bi-calendar-event',
                'url_name': 'leave_base',
                'order': 50,
                'parent_code': ''
            },
            {
                'code': 'visitor',
                'name': 'Visitor Management',
                'menu_label': 'Visitor Pass',
                'icon': 'bi-person-badge',
                'url_name': 'visitor_list',
                'order': 60,
                'parent_code': ''
            },
            {
                'code': 'staff',
                'name': 'Staff Coordinator',
                'menu_label': 'Staff Coordinator',
                'icon': 'bi-shield',
                'url_name': 'staff_list',
                'order': 70,
                'parent_code': ''
            },
            {
                'code': 'duty_management',
                'name': 'Duty Assignments',
                'menu_label': 'Duty Assignments',
                'icon': 'bi-calendar-check',
                'url_name': 'duty_list',
                'order': 72,
                'parent_code': ''
            },
            {
                'code': 'complaints',
                'name': 'Complaint Management',
                'menu_label': 'Complaint Tickets',
                'icon': 'bi-exclamation-triangle',
                'url_name': 'complaint_list',
                'order': 80,
                'parent_code': ''
            },
            {
                'code': 'inventory',
                'name': 'Inventory & Stock',
                'menu_label': 'Inventory Stock',
                'icon': 'bi-archive',
                'url_name': 'inventory_list',
                'order': 90,
                'parent_code': ''
            },
            {
                'code': 'security',
                'name': 'Gate & Security Logs',
                'menu_label': 'Security Gate Logs',
                'icon': 'bi-lock',
                'url_name': 'security_list',
                'order': 100,
                'parent_code': ''
            },
            {
                'code': 'hostel_manager',
                'name': 'Hostel Infra',
                'menu_label': 'Hostel Infra',
                'icon': 'bi-buildings',
                'url_name': 'hostel_manager',
                'order': 110,
                'parent_code': ''
            },
            {
                'code': 'fee_manager',
                'name': 'Fee Manager',
                'menu_label': 'Fee Manager',
                'icon': 'bi-cash-coin',
                'url_name': 'fee_manager',
                'order': 120,
                'parent_code': ''
            },
            {
                'code': 'reports_dashboard',
                'name': 'Reports',
                'menu_label': 'Reports',
                'icon': 'bi-bar-chart',
                'url_name': 'reports_dashboard',
                'order': 130,
                'parent_code': ''
            },
        ]

        # 1. Prune defunct modules
        valid_codes = [m['code'] for m in modules_data]
        deleted_count, _ = Module.objects.exclude(code__in=valid_codes).delete()
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f"Pruned {deleted_count} defunct modules from database."))

        # 2. Seed / Update modules
        count = 0
        for mdata in modules_data:
            module, created = Module.objects.get_or_create(
                code=mdata['code'],
                defaults={
                    'name': mdata['name'],
                    'menu_label': mdata['menu_label'],
                    'icon': mdata['icon'],
                    'url_name': mdata['url_name'],
                    'order': mdata['order'],
                    'parent_code': mdata['parent_code'],
                }
            )
            if not created:
                # Update existing ones to synchronize
                module.name = mdata['name']
                module.menu_label = mdata['menu_label']
                module.icon = mdata['icon']
                module.url_name = mdata['url_name']
                module.order = mdata['order']
                module.parent_code = mdata['parent_code']
                module.save()
            else:
                count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(modules_data)} system modules. (Created: {count}, Updated: {len(modules_data) - count})"
        ))
