from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_base, name='room_base'),
    path('student_details_list', views.student_details_list, name='student_details_list'),
    path('room_allocate', views.room_allocate, name='room_allocate'),
    path('room_auto_allocate', views.room_auto_allocate, name='room_auto_allocate'),
    path('room_auto_allocate/execute', views.room_auto_allocate_execute, name='room_auto_allocate_execute'),
    path('room_manage', views.room_manage, name='room_manage'),
    path('create_room/', views.create_room, name='create_room'),
    path('room_manage/<pk>/edit/', views.edit_room, name='edit_room'),
    path('room_manage/<pk>/delete/', views.delete_room, name='delete_room'),
    path('delete-allocation/<int:bed_id>/', views.delete_allocation, name='delete_allocation'),
    path('change-room/<int:current_bed_id>/', views.change_room, name='change_room'),
    path('student_allocated_view/<int:room_id>/', views.student_allocated_view, name='student_allocated_view'),

    # AJAX endpoints
    path('check-room-number/', views.check_room_number, name='check_room_number'),
    path('get-floors/', views.get_floors, name='get_floors'),
    path('rooms-by-building/', views.rooms_by_building, name='rooms_by_building'),
    path('get-rooms-for-allocation/', views.get_rooms_for_allocation, name='get_rooms_for_allocation'),
    path('get-beds-for-room/', views.get_beds_for_room, name='get_beds_for_room'),
    path('get-students-by-gender/', views.get_students_by_gender, name='get_students_by_gender'),
    path('ajax/student-search/', views.search_unallocated_students, name='search_unallocated_students'),
    path('ajax/bed-allocate/', views.allocate_bed_ajax, name='allocate_bed_ajax'),

    # Building Management
    path('buildings/', views.building_list, name='building_list'),
    path('buildings/create/', views.building_create, name='building_create'),
    path('buildings/<int:pk>/edit/', views.building_edit, name='building_edit'),
    path('buildings/<int:pk>/delete/', views.building_delete, name='building_delete'),
    path('buildings/<int:pk>/toggle/', views.building_toggle, name='building_toggle'),
    path('buildings/<int:building_id>/fee-structure/add/', views.add_building_fee_structure, name='add_building_fee_structure'),
]
