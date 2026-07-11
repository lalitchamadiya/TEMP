from django.contrib import admin
from .models import Room, Bed, HostelBuilding, Floor


@admin.register(HostelBuilding)
class HostelBuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'total_floors', 'is_active')
    list_filter = ('gender', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'building', 'floor_number')
    list_filter = ('building',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_name', 'room_type', 'building', 'block', 'floor', 'gender', 'capacity', 'status')
    list_filter = ('room_type', 'category', 'gender', 'status', 'is_ac', 'building')
    search_fields = ('room_number', 'room_name')


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room', 'student', 'total_amount', 'paid_amount', 'remaining_amount')
    list_filter = ('room',)
    search_fields = ('bed_number', 'room__room_number')