from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.warden_dashboard, name='warden_dashboard'),
]
