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
   path('student_pay_fee/', views.student_pay_fee, name='student_pay_fee'),
   path('payment_success/', views.payment_success, name='payment_success'),
   path('student_fee_details/', views.student_fee_details, name='student_fee_details'),
   path('verify_payment/', views.verify_payment, name='verify_payment'),
   path('razorpay_webhook/', views.razorpay_webhook, name='razorpay_webhook'),
   path('fee_receipt/<str:transaction_id>/', views.fee_receipt, name='fee_receipt'),
   path('download_fee_receipt/<str:transaction_id>/', views.download_fee_receipt, name='download_fee_receipt'),
   path('my_gate_passes/', views.my_gate_passes, name='my_gate_passes'),
   path('active-pass/<int:leave_id>/', views.view_active_pass, name='view_active_pass'),
]