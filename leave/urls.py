from django.urls import path
from . import views

urlpatterns = [
    path('', views.leave_base, name='leave_base'),
    path('leave_record/', views.leave_record, name='leave_record'),
    path('pending_leave/', views.pending_leave, name='pending_leave'),  # New URL for pending leave
    path('add_leave/', views.add_leave, name='add_leave'),
    path('check_enrollment', views.check_enrollment, name='check_enrollment'),
    path('edit_leave', views.edit_leave, name='edit_leave'),
    path('leave/delete/<int:leave_id>/', views.delete_leave, name='delete_leave'),
    path('leave/edit/<int:leave_id>/', views.edit_leave, name='edit_leave'),
    path('gate_pass_management/', views.gate_pass_management, name='gate_pass_management'),
    path('download_gate_pass/<int:gp_id>/', views.download_gate_pass_pdf, name='download_gate_pass'),
    path('leave_reports/', views.leave_reports, name='leave_reports'),
]


