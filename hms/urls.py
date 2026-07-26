from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name='dashboard'),
    path("superadmin/", views.superadmin_dashboard, name='superadmin_dashboard'),
    path("superadmin/ajax/live-stats/", views.live_dashboard_stats, name='live_dashboard_stats'),

    
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
    path("staff/duties/definitions/create/", views.duty_create, name='duty_create'),
    path("staff/duties/definitions/<int:pk>/edit/", views.duty_edit_definition, name='duty_edit_definition'),
    path("staff/duties/definitions/<int:pk>/delete/", views.duty_delete_definition, name='duty_delete_definition'),
    path("staff/duties/ajax/get-floors/", views.get_floors_for_building, name='get_floors_for_building'),
    
    # Complaint Management
    path("complaints/", views.complaint_list, name='complaint_list'),
    path("complaints/<int:pk>/assign/", views.complaint_assign, name='complaint_assign'),
    path("complaints/<int:pk>/resolve/", views.complaint_resolve, name='complaint_resolve'),
    
    # Hostel Logistics Manager (Rooms and Beds CRUD & Building APIs)
    path("hostel/", views.hostel_manager, name='hostel_manager'),
    path("hostel/block/create/", views.hostel_block_create, name='hostel_block_create'),
    path("hostel/floor/create/", views.hostel_floor_create, name='hostel_floor_create'),
    path("hostel/room/create/", views.hostel_room_create, name='hostel_room_create'),
    path("hostel/bed/create/", views.hostel_bed_create, name='hostel_bed_create'),
    path("hostel/bed/<int:pk>/allocate/", views.hostel_allocate_bed, name='hostel_allocate_bed'),
    path("hostel/bed/<int:pk>/deallocate/", views.hostel_deallocate_bed, name='hostel_deallocate_bed'),

    # Building & Infrastructure Real-Time APIs
    path("api/buildings/", views.api_building_list, name='api_building_list'),
    path("api/buildings/<int:pk>/", views.api_building_detail, name='api_building_detail'),
    path("api/buildings/<int:pk>/tree/", views.api_building_tree, name='api_building_tree'),
    path("api/buildings/create/", views.api_building_create, name='api_building_create'),
    path("api/buildings/<int:pk>/update/", views.api_building_update, name='api_building_update'),
    path("api/buildings/<int:pk>/delete/", views.api_building_delete, name='api_building_delete'),
    path("api/blocks/create/", views.api_block_create, name='api_block_create'),
    path("api/floors/create/", views.api_floor_create, name='api_floor_create'),
    path("api/rooms/create/", views.api_room_create, name='api_room_create'),
    path("api/beds/create/", views.api_bed_create, name='api_bed_create'),


    # Fee Management
    path("fees/", views.fee_manager, name='fee_manager'),
    path("fees/structure/create/", views.fee_structure_create, name='fee_structure_create'),
    path("fees/payment/create/", views.fee_payment_create, name='fee_payment_create'),
    
    # Reports
    path("reports/", views.reports_dashboard, name='reports_dashboard'),
    path("reports/export/<str:module>/", views.export_report, name='export_report'),


]