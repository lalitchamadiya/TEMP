from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),

    path('create/', views.create_student, name='create_student'),
    path('check-roll-number/', views.check_roll_number, name='check_roll_number'),
    path('<int:pk>/update/', views.update_student, name='update_student'),
    path('<int:pk>/view/', views.view_student, name='view_student'),
    path('<int:pk>/delete/', views.delete_student, name='delete_student'),
]