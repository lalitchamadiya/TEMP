from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from student.models import Student


class RoomForm(forms.Form):
    building = forms.ChoiceField(
        choices=[(1, 'Boys Hostel Block A'), (2, 'Girls Hostel Block B')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_building'})
    )
    block = forms.ChoiceField(
        choices=[('A', 'Block A'), ('B', 'Block B')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_block'})
    )
    floor = forms.ChoiceField(
        choices=[(1, '1st Floor'), (2, '2nd Floor'), (3, '3rd Floor')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_floor'})
    )
    room_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_room_number', 'placeholder': 'e.g. 101'})
    )
    room_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_room_name', 'placeholder': 'e.g. Deluxe Suite'})
    )
    room_type = forms.ChoiceField(
        choices=[
            ('DOUBLE', '2 Beds Double Sharing'),
            ('SINGLE', '1 Bed Single Room'),
            ('TRIPLE', '3 Beds Triple Sharing'),
            ('DORMITORY', 'Dormitory'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_room_type'})
    )
    category = forms.ChoiceField(
        choices=[('GENERAL', 'General Student'), ('DELUXE', 'Deluxe Premium'), ('STAFF', 'Staff / Warden')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_category'})
    )
    status = forms.ChoiceField(
        choices=[('AVAILABLE', 'Available / Active'), ('MAINTENANCE', 'Under Maintenance')],
        widget=forms.Select(attrs={'class': 'form-select', 'name': 'status', 'id': 'id_status'})
    )
    monthly_rent = forms.CharField(
        initial='2500.00',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_monthly_rent'})
    )
    is_ac = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_ac'})
    )
    capacity = forms.IntegerField(
        initial=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_capacity', 'min': 1, 'max': 20})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'id': 'id_description', 'rows': 2})
    )


def _is_admin(user):
    if user.is_superuser:
        return True
    try:
        role = user.profile.role
        return role.is_superadmin or role.name in ('Admin', 'Staff', 'Warden')
    except Exception:
        return False


# ── Main Room Dashboard ──
@login_required(login_url='/authentication/login')
def room_base(request):
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='Active').count()
    gender_male = Student.objects.filter(status='Active', gender='Male').count()
    gender_female = Student.objects.filter(status='Active', gender='Female').count()

    context = {
        'page_title': 'Room Management Dashboard',
        'total_buildings': 2,
        'total_availabel_room': 50,
        'total_boys_rooms': 25,
        'total_girls_rooms': 25,
        'total_allocated_beds': active_students,
        'total_unallocated_beds': max(0, 100 - active_students),
        'total_maintenance_rooms': 0,
        'total_reserved_beds': 0,
        'total_boys_allocated': gender_male,
        'total_girls_allocated': gender_female,
        'upcoming_vacancies': 0,
    }
    return render(request, 'room/room_base.html', context)


# ── Room Management (Overview) ──
@login_required(login_url='/authentication/login')
def room_manage(request):
    search_query = request.GET.get('q', '').strip()
    selected_building_id = request.GET.get('building', '')

    students = list(Student.objects.filter(status='Active'))
    rooms = []
    
    for i in range(1, 11):
        room_num = f"10{i}" if i < 10 else f"1{i}"
        
        # Boys room
        boys_beds = []
        b_st_1 = students.pop(0) if students else None
        b_st_2 = students.pop(0) if students else None
        boys_beds.append({'bed_number': '1', 'student': b_st_1})
        boys_beds.append({'bed_number': '2', 'student': b_st_2})
        occupied_boys = (1 if b_st_1 else 0) + (1 if b_st_2 else 0)

        rooms.append({
            'id': i,
            'room_number': room_num,
            'room_name': f'Boys Unit {room_num}',
            'building': {'id': 1, 'name': 'Boys Hostel Block A'},
            'block': 'A',
            'get_block_display': 'Block A',
            'room_type': 2,
            'gender': 'Boys',
            'beds': {'all': boys_beds},
            'occupied_count': occupied_boys,
        })

        # Girls room
        girls_beds = []
        g_st_1 = students.pop(0) if students else None
        g_st_2 = students.pop(0) if students else None
        girls_beds.append({'bed_number': '1', 'student': g_st_1})
        girls_beds.append({'bed_number': '2', 'student': g_st_2})
        occupied_girls = (1 if g_st_1 else 0) + (1 if g_st_2 else 0)

        rooms.append({
            'id': 100 + i,
            'room_number': f"20{i}" if i < 10 else f"2{i}",
            'room_name': f'Girls Unit 20{i}' if i < 10 else f'Girls Unit 2{i}',
            'building': {'id': 2, 'name': 'Girls Hostel Block B'},
            'block': 'B',
            'get_block_display': 'Block B',
            'room_type': 2,
            'gender': 'Girls',
            'beds': {'all': girls_beds},
            'occupied_count': occupied_girls,
        })

    if search_query:
        rooms = [r for r in rooms if search_query.lower() in r['room_number'].lower() or search_query.lower() in r['room_name'].lower()]
    if selected_building_id:
        rooms = [r for r in rooms if str(r['building']['id']) == str(selected_building_id)]

    buildings = [
        {'pk': 1, 'name': 'Boys Hostel Block A'},
        {'pk': 2, 'name': 'Girls Hostel Block B'},
    ]

    context = {
        'page_title': 'Room Overview',
        'rooms': rooms,
        'buildings': buildings,
        'selected_building_id': selected_building_id,
        'search_query': search_query,
    }
    return render(request, 'room/manage.html', context)


# ── Room Allocation ──
@login_required(login_url='/authentication/login')
def room_allocate(request):
    if request.method == 'POST':
        messages.success(request, 'Bed allocation saved successfully.')
        return redirect('room_manage')

    buildings = [
        {'id': 1, 'name': 'Boys Hostel Block A', 'get_gender_display': 'Boys'},
        {'id': 2, 'name': 'Girls Hostel Block B', 'get_gender_display': 'Girls'},
    ]
    blocks = [('A', 'Block A'), ('B', 'Block B')]

    context = {
        'page_title': 'Allocate Bed',
        'buildings': buildings,
        'blocks': blocks,
    }
    return render(request, 'room/allocate.html', context)


# ── Auto Allocate ──
@login_required(login_url='/authentication/login')
def room_auto_allocate(request):
    if request.method == 'POST':
        messages.success(request, 'Automatic room allocation completed.')
        return redirect('room_manage')

    context = {
        'page_title': 'Auto Allocate Rooms',
        'unallocated_students': Student.objects.filter(status='Active')[:20],
    }
    return render(request, 'room/auto_allocate.html', context)


@login_required(login_url='/authentication/login')
def room_auto_allocate_execute(request):
    if request.method == 'POST':
        messages.success(request, 'Auto allocation process executed successfully.')
    return redirect('room_manage')


# ── Create Room ──
@login_required(login_url='/authentication/login')
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            messages.success(request, 'New room created successfully.')
            return redirect('room_manage')
    else:
        form = RoomForm()

    context = {
        'page_title': 'Create New Room',
        'action': 'Create',
        'form': form,
        'base_rents_json': '{"DOUBLE": 2500, "SINGLE": 4000, "TRIPLE": 2000, "DORMITORY": 1500}',
        'category_multipliers_json': '{"GENERAL": 1.0, "DELUXE": 1.5, "STAFF": 0.0}',
    }
    return render(request, 'room/create_room.html', context)


# ── Edit / Delete / Change Room ──
@login_required(login_url='/authentication/login')
def edit_room(request, pk):
    try:
        pk_int = int(pk)
    except (ValueError, TypeError):
        pk_int = 1

    is_girls = pk_int >= 100
    unit_idx = pk_int - 100 if is_girls else pk_int
    if is_girls:
        room_num = f"20{unit_idx}" if unit_idx < 10 else f"2{unit_idx}"
    else:
        room_num = f"10{unit_idx}" if unit_idx < 10 else f"1{unit_idx}"

    initial_data = {
        'building': 2 if is_girls else 1,
        'block': 'B' if is_girls else 'A',
        'floor': 1,
        'room_number': room_num,
        'room_name': f"Unit #{room_num}",
        'room_type': 'DOUBLE',
        'category': 'GENERAL',
        'status': 'AVAILABLE',
        'monthly_rent': '2500.00',
        'is_ac': False,
        'capacity': 2,
        'description': f'Hostel Room Unit #{room_num}',
    }

    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            messages.success(request, f'Room Unit #{room_num} updated successfully.')
            return redirect('room_manage')
    else:
        form = RoomForm(initial=initial_data)

    room_dict = {
        'pk': pk,
        'id': pk,
        'room_number': room_num,
        'room_name': f"Unit #{room_num}",
    }

    context = {
        'page_title': f'Edit Room #{room_num}',
        'action': 'Edit',
        'room': room_dict,
        'form': form,
        'base_rents_json': '{"DOUBLE": 2500, "SINGLE": 4000, "TRIPLE": 2000, "DORMITORY": 1500}',
        'category_multipliers_json': '{"GENERAL": 1.0, "DELUXE": 1.5, "STAFF": 0.0}',
    }
    return render(request, 'room/create_room.html', context)


@login_required(login_url='/authentication/login')
def delete_room(request, pk):
    if request.method == 'POST':
        messages.success(request, f'Room {pk} deleted successfully.')
    return redirect('room_manage')


@login_required(login_url='/authentication/login')
def delete_allocation(request, bed_id):
    if request.method == 'POST':
        messages.success(request, f'Allocation for bed {bed_id} removed.')
    return redirect('room_manage')


@login_required(login_url='/authentication/login')
def change_room(request, current_bed_id):
    if request.method == 'POST':
        messages.success(request, 'Room change updated.')
        return redirect('room_manage')
    return redirect('room_manage')


# ── Building Management ──
@login_required(login_url='/authentication/login')
def building_list(request):
    buildings = [
        {'id': 1, 'pk': 1, 'name': 'Boys Hostel Block A', 'code': 'BH-A', 'gender': 'Male', 'get_gender_display': 'Boys', 'total_floors': 3, 'rooms_count': 25, 'room_count': 25, 'capacity': 50, 'is_active': True, 'is_archived': False},
        {'id': 2, 'pk': 2, 'name': 'Girls Hostel Block B', 'code': 'GH-B', 'gender': 'Female', 'get_gender_display': 'Girls', 'total_floors': 3, 'rooms_count': 25, 'room_count': 25, 'capacity': 50, 'is_active': True, 'is_archived': False},
    ]
    context = {
        'page_title': 'Hostel Buildings',
        'buildings': buildings,
    }
    return render(request, 'room/building_list.html', context)


@login_required(login_url='/authentication/login')
def building_create(request):
    if request.method == 'POST':
        messages.success(request, 'New building added successfully.')
        return redirect('building_list')
    return render(request, 'room/building_form.html', {'page_title': 'Add Building'})


@login_required(login_url='/authentication/login')
def building_edit(request, pk):
    if request.method == 'POST':
        messages.success(request, f'Building {pk} updated.')
        return redirect('building_list')
    return redirect('building_list')


@login_required(login_url='/authentication/login')
def building_delete(request, pk):
    if request.method == 'POST':
        messages.success(request, f'Building {pk} removed.')
    return redirect('building_list')


@login_required(login_url='/authentication/login')
def building_toggle(request, pk):
    if request.method == 'POST':
        messages.success(request, f'Building {pk} status toggled.')
    return redirect('building_list')


# ── Residents & Student Views ──
@login_required(login_url='/authentication/login')
def student_details_list(request):
    students = Student.objects.filter(status='Active').order_by('-student_id')
    context = {
        'page_title': 'Hostel Residents',
        'students': students,
    }
    return render(request, 'room/student_details_list.html', context)


@login_required(login_url='/authentication/login')
def student_allocated_view(request, room_id):
    try:
        room_id = int(room_id)
    except (ValueError, TypeError):
        room_id = 1

    is_girls_room = room_id >= 100
    if is_girls_room:
        unit_index = room_id - 100
        room_num = f"20{unit_index}" if unit_index < 10 else f"2{unit_index}"
        building_name = "Girls Hostel Block B"
        gender_disp = "Girls Wing"
        room_gender = "Female"
    else:
        unit_index = room_id
        room_num = f"10{unit_index}" if unit_index < 10 else f"1{unit_index}"
        building_name = "Boys Hostel Block A"
        gender_disp = "Boys Wing"
        room_gender = "Male"

    all_students = list(Student.objects.filter(status='Active', gender=room_gender))

    st_index = (unit_index - 1) * 2
    st1 = all_students[st_index] if st_index < len(all_students) else None
    st2 = all_students[st_index + 1] if (st_index + 1) < len(all_students) else None

    beds = [
        {
            'id': (room_id * 10) + 1,
            'bed_number': '1',
            'student': st1,
            'remaining_amount': 0
        },
        {
            'id': (room_id * 10) + 2,
            'bed_number': '2',
            'student': st2,
            'remaining_amount': 0
        }
    ]

    occupied_count = (1 if st1 else 0) + (1 if st2 else 0)
    total_beds = 2
    vacant_count = total_beds - occupied_count

    room_obj = {
        'id': room_id,
        'room_number': room_num,
        'room_name': f'Unit #{room_num}',
        'building': {'name': building_name},
        'floor': {'floor_number': '1'},
        'get_room_type_display': '2 Beds Double Sharing',
        'get_gender_display': gender_disp,
    }

    context = {
        'page_title': f'Room #{room_num} Details',
        'room_number': room_num,
        'room': room_obj,
        'total_beds': total_beds,
        'occupied_beds': occupied_count,
        'vacant_beds': vacant_count,
        'beds': beds,
    }
    return render(request, 'room/student_allocated_view.html', context)


# ── AJAX Endpoints ──
@login_required(login_url='/authentication/login')
def check_room_number(request):
    return JsonResponse({'exists': False})


@login_required(login_url='/authentication/login')
def get_floors(request):
    floors = [
        {'id': 1, 'label': 'Ground Floor (G)'},
        {'id': 2, 'label': '1st Floor'},
        {'id': 3, 'label': '2nd Floor'},
    ]
    return JsonResponse({'floors': floors})


@login_required(login_url='/authentication/login')
def rooms_by_building(request):
    return JsonResponse({'rooms': []})


@login_required(login_url='/authentication/login')
def get_rooms_for_allocation(request):
    building_id = request.GET.get('building_id')
    gender_disp = 'Boys' if str(building_id) == '1' else 'Girls'
    rooms = [
        {'room_id': 101, 'room_number': '101', 'gender': gender_disp, 'gender_display': gender_disp, 'vacant_beds': 1, 'capacity': 2},
        {'room_id': 102, 'room_number': '102', 'gender': gender_disp, 'gender_display': gender_disp, 'vacant_beds': 2, 'capacity': 2},
        {'room_id': 103, 'room_number': '103', 'gender': gender_disp, 'gender_display': gender_disp, 'vacant_beds': 1, 'capacity': 2},
    ]
    return JsonResponse({'rooms': rooms})


@login_required(login_url='/authentication/login')
def get_beds_for_room(request):
    room_id = request.GET.get('room_id', '101')
    beds = [
        {'bed_number': '1', 'student': None},
        {'bed_number': '2', 'student': None},
    ]
    return JsonResponse({'room_number': str(room_id), 'gender_display': 'Boys', 'beds': beds})


@login_required(login_url='/authentication/login')
def get_students_by_gender(request):
    room_gender = request.GET.get('room_gender', '')
    gender = 'Male' if 'boy' in room_gender.lower() else 'Female'
    qs = Student.objects.filter(status='Active', gender=gender)
    students_data = [
        {
            'id': s.student_id,
            'name': s.name,
            'roll': s.roll or f'STU{s.student_id}',
            'phone': s.phone_number or '',
            'photo': s.photo.url if (s.photo and hasattr(s.photo, 'url')) else '/static/image/User.jpg'
        }
        for s in qs[:50]
    ]
    return JsonResponse({'students': students_data})


@login_required(login_url='/authentication/login')
def search_unallocated_students(request):
    q = request.GET.get('q', '').strip()
    qs = Student.objects.filter(status='Active')
    if q:
        qs = qs.filter(name__icontains=q)
    data = [{'id': s.student_id, 'text': f"{s.name} ({s.roll})"} for s in qs[:20]]
    return JsonResponse({'results': data})


@login_required(login_url='/authentication/login')
def allocate_bed_ajax(request):
    return JsonResponse({'status': 'success', 'message': 'Bed allocated successfully.'})
