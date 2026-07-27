from django.core.management.base import BaseCommand
from authentication.models import Module, PermissionElement


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

        # 3. Seed / Update standard permission elements
        elements_data = [
            # ROOM MODULE
            {
                'code': 'btn_create_room',
                'name': 'New Room Button',
                'category': 'button',
                'description': 'Allows clicking "New Room" and submitting the create form.',
                'module_code': 'room'
            },
            {
                'code': 'btn_edit_room',
                'name': 'Edit Room Button',
                'category': 'button',
                'description': 'Allows editing room configuration values.',
                'module_code': 'room'
            },
            {
                'code': 'btn_delete_room',
                'name': 'Delete Room Button',
                'category': 'button',
                'description': 'Allows deleting a room and associated records.',
                'module_code': 'room'
            },
            {
                'code': 'btn_bed_add',
                'name': 'Add Bed Button',
                'category': 'button',
                'description': 'Allows adding new beds to a room.',
                'module_code': 'room'
            },
            {
                'code': 'item_live_bed_map',
                'name': 'Live Bed Map UI',
                'category': 'item',
                'description': 'Displays graphic representation of room layout and bed usage.',
                'module_code': 'room'
            },
            {
                'code': 'btn_building_deactivate',
                'name': 'Toggle Building Status Button',
                'category': 'button',
                'description': 'Allows activating or deactivating a building.',
                'module_code': 'room'
            },

            # STUDENT MODULE
            {
                'code': 'btn_student_add',
                'name': 'New Student Button',
                'category': 'button',
                'description': 'Allows creating a new student record.',
                'module_code': 'student'
            },
            {
                'code': 'btn_student_edit',
                'name': 'Edit Student Button',
                'category': 'button',
                'description': 'Allows editing student profile fields.',
                'module_code': 'student'
            },
            {
                'code': 'btn_student_delete',
                'name': 'Delete Student Button',
                'category': 'button',
                'description': 'Allows deleting student records.',
                'module_code': 'student'
            },
            {
                'code': 'btn_student_import',
                'name': 'Import Student CSV Button',
                'category': 'button',
                'description': 'Allows uploading a CSV file to bulk import students.',
                'module_code': 'student'
            },
            {
                'code': 'btn_student_export',
                'name': 'Export Student CSV Button',
                'category': 'button',
                'description': 'Allows downloading a CSV export of active students.',
                'module_code': 'student'
            },
            {
                'code': 'btn_student_print',
                'name': 'Print Student Registry Button',
                'category': 'button',
                'description': 'Allows triggering browser print view of student table.',
                'module_code': 'student'
            },

            # PAYBILL MODULE
            {
                'code': 'btn_paybill_add',
                'name': 'New Paybill / Fee Invoice Button',
                'category': 'button',
                'description': 'Allows generating a new fee invoice or transaction bill.',
                'module_code': 'paybill'
            },
            {
                'code': 'btn_paybill_delete',
                'name': 'Delete Paybill Button',
                'category': 'button',
                'description': 'Allows deleting paybills or invoices.',
                'module_code': 'paybill'
            },

            # LEAVE MODULE
            {
                'code': 'btn_leave_approve',
                'name': 'Approve Leave Request Button',
                'category': 'button',
                'description': 'Allows staff/warden to approve pending leave requests.',
                'module_code': 'leave'
            },
            {
                'code': 'btn_leave_reject',
                'name': 'Reject Leave Request Button',
                'category': 'button',
                'description': 'Allows staff/warden to reject pending leave requests.',
                'module_code': 'leave'
            },

            # AUDIT & ADMIN CONTROLS
            {
                'code': 'item_global_search',
                'name': 'Search Bar in Top Navigation',
                'category': 'item',
                'description': 'Shows general search bar on dashboard head menu.',
                'module_code': 'user_management'
            },
            {
                'code': 'btn_user_lock',
                'name': 'Lock User Account Toggle Button',
                'category': 'button',
                'description': 'Allows Super Admin to lock/unlock user login sessions.',
                'module_code': 'user_management'
            },
            {
                'code': 'btn_user_reset_pass',
                'name': 'Reset Password Action Button',
                'category': 'button',
                'description': 'Allows forcing password reset for user accounts.',
                'module_code': 'user_management'
            },
        ]

        elem_count = 0
        for edata in elements_data:
            mod = Module.objects.filter(code=edata['module_code']).first()
            elem, created = PermissionElement.objects.get_or_create(
                code=edata['code'],
                defaults={
                    'name': edata['name'],
                    'category': edata['category'],
                    'description': edata['description'],
                    'module': mod,
                }
            )
            if not created:
                elem.name = edata['name']
                elem.category = edata['category']
                elem.description = edata['description']
                elem.module = mod
                elem.save()
            else:
                elem_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(elements_data)} permission elements. (Created: {elem_count}, Updated: {len(elements_data) - elem_count})"
        ))
