from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_base, name='room_base'),
]
