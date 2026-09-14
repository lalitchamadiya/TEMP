from django.urls import path
from . import views


app_name = 'student_app'

urlpatterns = [
   path('student_profile/', views.student_profile, name='student_profile'),
   path('dashboard/', views.student_dashboard, name='student_dashboard'),
   path('student_profile_update/', views.student_profile_update, name='student_profile_update'),
   path('food_schedule/', views.food_schedule, name='food_schedule'),
   path('leave_request/', views.student_leave_request, name='student_leave_request'),
   path('student_leave_details/', views.student_leave_details, name='student_leave_details'),
   path('change_password/', views.change_password, name='change_password'),
    path('gate_pass/', views.student_gate_pass, name='student_gate_pass'),
    path('gate-passes-status/', views.student_gate_passes_status_json, name='student_gate_passes_status'),
    path('active-pass/<int:leave_id>/', views.view_active_pass, name='view_active_pass'),
    path('active-pass-status/<int:leave_id>/', views.active_pass_status_json, name='active_pass_status'),
]