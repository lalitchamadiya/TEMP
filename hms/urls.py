from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name='dashboard'),
    path("superadmin/", views.superadmin_dashboard, name='superadmin_dashboard'),
    path("admin-dash/", views.org_admin_dashboard, name='org_admin_dashboard'),
    
    # Staff Management
    path("staff/", views.staff_list, name='staff_list'),
    path("staff/create/", views.staff_create, name='staff_create'),
    path("staff/<int:pk>/edit/", views.staff_edit, name='staff_edit'),
    path("staff/<int:pk>/delete/", views.staff_delete, name='staff_delete'),
    path("staff/<int:pk>/toggle-status/", views.staff_toggle_status, name='staff_toggle_status'),
    path("staff/duties/", views.duty_list, name='duty_list'),
    path("staff/duties/assign/", views.duty_assign, name='duty_assign'),
    path("staff/duties/<int:pk>/edit/", views.duty_edit, name='duty_edit'),
    path("staff/duties/<int:pk>/delete/", views.duty_delete, name='duty_delete'),
    path("staff/duties/ajax/get-floors/", views.get_floors_for_building, name='get_floors_for_building'),
    
    # Visitor Management
    path("visitors/", views.visitor_list, name='visitor_list'),
    path("visitors/create/", views.visitor_create, name='visitor_create'),
    path("visitors/<int:pk>/status/<str:status>/", views.visitor_update_status, name='visitor_update_status'),
    path("visitors/<int:pk>/checkout/", views.visitor_checkout, name='visitor_checkout'),
    
    # Inventory Management
    path("inventory/", views.inventory_list, name='inventory_list'),
    path("inventory/create/", views.inventory_create, name='inventory_create'),
    path("inventory/<int:pk>/edit/", views.inventory_edit, name='inventory_edit'),
    path("inventory/<int:pk>/delete/", views.inventory_delete, name='inventory_delete'),
    
    # Complaint Management
    path("complaints/", views.complaint_list, name='complaint_list'),
    path("complaints/<int:pk>/assign/", views.complaint_assign, name='complaint_assign'),
    path("complaints/<int:pk>/resolve/", views.complaint_resolve, name='complaint_resolve'),
    
    # Security Management
    path("security/", views.security_list, name='security_list'),
    path("security/guard/create/", views.security_guard_create, name='security_guard_create'),
    path("security/incident/create/", views.incident_report_create, name='incident_report_create'),
    
    # Hostel Logistics Manager (Rooms and Beds CRUD)
    path("hostel/", views.hostel_manager, name='hostel_manager'),
    path("hostel/block/create/", views.hostel_block_create, name='hostel_block_create'),
    path("hostel/floor/create/", views.hostel_floor_create, name='hostel_floor_create'),
    path("hostel/room/create/", views.hostel_room_create, name='hostel_room_create'),
    path("hostel/bed/create/", views.hostel_bed_create, name='hostel_bed_create'),
    path("hostel/bed/<int:pk>/allocate/", views.hostel_allocate_bed, name='hostel_allocate_bed'),
    path("hostel/bed/<int:pk>/deallocate/", views.hostel_deallocate_bed, name='hostel_deallocate_bed'),

    # Fee Management
    path("fees/", views.fee_manager, name='fee_manager'),
    path("fees/structure/create/", views.fee_structure_create, name='fee_structure_create'),
    path("fees/payment/create/", views.fee_payment_create, name='fee_payment_create'),
    
    # Reports
    path("reports/", views.reports_dashboard, name='reports_dashboard'),
    path("reports/export/<str:module>/", views.export_report, name='export_report'),

    # Multi-Hostel Control Center
    path("control-center/", views.superadmin_control_center, name='superadmin_control_center'),
    path("control-center/hostel/<int:pk>/toggle/", views.hostel_toggle_status_ajax, name='hostel_toggle_status_ajax'),
    path("control-center/transfer/student/", views.transfer_student, name='transfer_student'),
    path("control-center/transfer/staff/", views.transfer_staff, name='transfer_staff'),
    path("control-center/report/csv/", views.cross_hostel_report_csv, name='cross_hostel_report_csv'),
]