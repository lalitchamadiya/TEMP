from django.urls import path
from . import views
from .views import process_payment, delete_transaction, export_transactions_csv, export_transactions_excel

urlpatterns = [
    path('', views.paybill_base, name='paybill_base'),
    path('collect_fees', views.collect_fees, name='collect_fees'),
    path('pay_salary', views.pay_salary, name='pay_salary'),
    path('pending_fees', views.pending_fees, name='pending_fees'),
    path('transaction_record/', views.transaction_record, name='transaction_record'),
    path('check_enrollment_fee', views.check_enrollment, name='check_enrollment_fee'),
    path('process_payment/', process_payment, name='process_payment'),
    path('delete_transaction/<str:transaction_id>/', delete_transaction, name='delete_transaction'),
    path('fee_structure', views.fee_structure, name='fee_structure'),
    path('delete_fee_item/<int:fee_id>/', views.delete_fee_item, name='delete_fee_item'),
    path('student_details/', views.student_details, name='student_details'),
    path('admin_analytics/', views.admin_analytics, name='admin_analytics'),
    path('export/csv/', export_transactions_csv, name='export_transactions_csv'),
    path('export/excel/', export_transactions_excel, name='export_transactions_excel'),
  
   
]
