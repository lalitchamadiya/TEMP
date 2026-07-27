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
    
    # Complaint Management
    path("complaints/", views.complaint_list, name='complaint_list'),
    path("complaints/<int:pk>/assign/", views.complaint_assign, name='complaint_assign'),
    path("complaints/<int:pk>/resolve/", views.complaint_resolve, name='complaint_resolve'),


    # Fee Management
    path("fees/", views.fee_manager, name='fee_manager'),
    path("fees/structure/create/", views.fee_structure_create, name='fee_structure_create'),
    path("fees/payment/create/", views.fee_payment_create, name='fee_payment_create'),
    
    # Reports
    path("reports/", views.reports_dashboard, name='reports_dashboard'),
    path("reports/export/<str:module>/", views.export_report, name='export_report'),


]