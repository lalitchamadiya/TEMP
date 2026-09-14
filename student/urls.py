from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('fee-manager/', views.fee_manager, name='fee_manager'),
    path('fee-installments/', views.fee_installments, name='fee_installments'),
    path('fee-penalties/', views.fee_penalties, name='fee_penalties'),
    path('<int:student_id>/record-payment/', views.record_fee_payment, name='record_fee_payment'),

    path('create/', views.create_student, name='create_student'),
    path('check-roll-number/', views.check_roll_number, name='check_roll_number'),
    path('<int:pk>/update/', views.update_student, name='update_student'),
    path('<int:pk>/view/', views.view_student, name='view_student'),
    path('<int:pk>/delete/', views.delete_student, name='delete_student'),
]