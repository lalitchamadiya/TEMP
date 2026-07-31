from django.urls import path
from fees import views

app_name = 'fees'

urlpatterns = [
    # Fee Structure
    path('fee-structure/create/', views.fee_structure_create_view, name='fee_structure_create'),
    path('fee-structure/', views.fee_structure_list_view, name='fee_structure_list'),

    # Student Payment & Transactions
    path('student-payment/', views.student_payment_view, name='student_payment'),
    path('transaction-history/', views.transaction_history_view, name='transaction_history'),
    path('ledger/<int:student_id>/', views.student_ledger_view, name='student_ledger'),

    # Dashboard & Analytics
    path('dashboard/', views.payment_dashboard_view, name='payment_dashboard'),

    # Receipts & Verification
    path('receipt/<int:pk>/', views.receipt_detail_view, name='receipt_detail'),
    path('verify-receipt/<str:qr_hash>/', views.receipt_verify_view, name='receipt_verify'),

    # AJAX Endpoints
    path('ajax/student-search/', views.student_search_ajax, name='ajax_student_search'),
    path('ajax/room-type-details/', views.room_type_details_ajax, name='ajax_room_type_details'),
    path('ajax/process-payment/', views.process_payment_ajax, name='ajax_process_payment'),
    path('ajax/refund/', views.refund_transaction_ajax, name='ajax_refund'),
]
