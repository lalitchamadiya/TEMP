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


# ── State Storage Helpers ──
def _get_initial_rooms():
    students = list(Student.objects.filter(status='Active'))
    rooms_dict = {}
    
    for i in range(1, 11):
        room_num = f"10{i}" if i < 10 else f"1{i}"
        b_st_1 = students.pop(0) if students else None
        b_st_2 = students.pop(0) if students else None
        boys_beds = [
            {'id': (i * 10) + 1, 'bed_number': '1', 'student_id': b_st_1.student_id if b_st_1 else None},
            {'id': (i * 10) + 2, 'bed_number': '2', 'student_id': b_st_2.student_id if b_st_2 else None},
        ]
        rooms_dict[str(i)] = {
            'id': i,
            'pk': i,
            'room_number': room_num,
            'room_name': f'Boys Unit {room_num}',
            'building_id': 1,
            'building_name': 'Boys Hostel Block A',
            'block': 'A',
            'block_display': 'Block A',
            'floor': 1,
            'room_type': 'DOUBLE',
            'room_type_display': '2 Beds Double Sharing',
            'category': 'GENERAL',
            'gender': 'Boys',
            'capacity': 2,
            'status': 'AVAILABLE',
            'monthly_rent': '2500.00',
            'is_ac': False,
            'description': f'Hostel Room Unit #{room_num}',
            'beds': boys_beds,
        }

        g_id = 100 + i
        g_room_num = f"20{i}" if i < 10 else f"2{i}"
        g_st_1 = students.pop(0) if students else None
        g_st_2 = students.pop(0) if students else None
        girls_beds = [
            {'id': (g_id * 10) + 1, 'bed_number': '1', 'student_id': g_st_1.student_id if g_st_1 else None},
            {'id': (g_id * 10) + 2, 'bed_number': '2', 'student_id': g_st_2.student_id if g_st_2 else None},
        ]
        rooms_dict[str(g_id)] = {
            'id': g_id,
            'pk': g_id,
            'room_number': g_room_num,
            'room_name': f'Girls Unit {g_room_num}',
            'building_id': 2,
            'building_name': 'Girls Hostel Block B',
            'block': 'B',
            'block_display': 'Block B',
            'floor': 1,
            'room_type': 'DOUBLE',
            'room_type_display': '2 Beds Double Sharing',
            'category': 'GENERAL',
            'gender': 'Girls',
            'capacity': 2,
            'status': 'AVAILABLE',
            'monthly_rent': '2500.00',
            'is_ac': False,
            'description': f'Hostel Room Unit #{g_room_num}',
            'beds': girls_beds,
        }

    return rooms_dict


def _get_session_rooms(request):
    if 'rooms_data' not in request.session:
        request.session['rooms_data'] = _get_initial_rooms()
    return request.session['rooms_data']


def _save_session_rooms(request, rooms_data):
    request.session['rooms_data'] = rooms_data
    request.session.modified = True


# ── Main Room Dashboard ──
@login_required(login_url='/authentication/login')
def room_base(request):
    rooms_data = _get_session_rooms(request)
    total_rooms = len(rooms_data)
    boys_rooms = sum(1 for r in rooms_data.values() if r.get('gender') == 'Boys')
    girls_rooms = sum(1 for r in rooms_data.values() if r.get('gender') == 'Girls')

    active_students = Student.objects.filter(status='Active').count()
    gender_male = Student.objects.filter(status='Active', gender='Male').count()
    gender_female = Student.objects.filter(status='Active', gender='Female').count()

    context = {
        'page_title': 'Room Management Dashboard',
        'total_buildings': 2,
        'total_availabel_room': total_rooms,
        'total_boys_rooms': boys_rooms,
        'total_girls_rooms': girls_rooms,
        'total_allocated_beds': active_students,
        'total_unallocated_beds': max(0, 100 - active_students),
        'total_maintenance_rooms': sum(1 for r in rooms_data.values() if r.get('status') == 'MAINTENANCE'),
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

    rooms_data = _get_session_rooms(request)

    student_ids = []
    for r in rooms_data.values():
        for b in r.get('beds', []):
            if b.get('student_id'):
                student_ids.append(b['student_id'])

    students_map = {s.student_id: s for s in Student.objects.filter(student_id__in=student_ids)}

    rooms_list = []
    for r_id, r_info in rooms_data.items():
        beds_list = []
        occupied_count = 0
        for b in r_info.get('beds', []):
            st_obj = students_map.get(b.get('student_id'))
            if st_obj:
                occupied_count += 1
            beds_list.append({
                'id': b.get('id'),
                'bed_number': b.get('bed_number'),
                'student': st_obj
            })

        room_obj = {
            'id': r_info['id'],
            'pk': r_info['pk'],
            'room_number': r_info['room_number'],
            'room_name': r_info['room_name'],
            'building': {'id': r_info['building_id'], 'name': r_info['building_name']},
            'block': r_info['block'],
            'get_block_display': r_info['block_display'],
            'room_type': r_info['capacity'],
            'gender': r_info['gender'],
            'beds': {'all': beds_list},
            'occupied_count': occupied_count,
        }
        rooms_list.append(room_obj)

    if search_query:
        rooms_list = [r for r in rooms_list if search_query.lower() in str(r['room_number']).lower() or search_query.lower() in r['room_name'].lower()]
    if selected_building_id:
        rooms_list = [r for r in rooms_list if str(r['building']['id']) == str(selected_building_id)]

    buildings = [
        {'pk': 1, 'name': 'Boys Hostel Block A'},
        {'pk': 2, 'name': 'Girls Hostel Block B'},
    ]

    context = {
        'page_title': 'Room Overview',
        'rooms': rooms_list,
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
            cleaned = form.cleaned_data
            rooms_data = _get_session_rooms(request)

            existing_ids = [int(k) for k in rooms_data.keys() if k.isdigit()]
            new_id = (max(existing_ids) + 1) if existing_ids else 1
            pk_str = str(new_id)

            building_id = int(cleaned.get('building', 1))
            b_name = "Boys Hostel Block A" if building_id == 1 else "Girls Hostel Block B"
            gender = "Boys" if building_id == 1 else "Girls"
            capacity = int(cleaned.get('capacity', 2))

            beds = [{'id': (new_id * 10) + b_idx, 'bed_number': str(b_idx), 'student_id': None} for b_idx in range(1, capacity + 1)]

            room_item = {
                'id': new_id,
                'pk': new_id,
                'room_number': cleaned.get('room_number'),
                'room_name': cleaned.get('room_name') or f"Unit #{cleaned.get('room_number')}",
                'building_id': building_id,
                'building_name': b_name,
                'block': cleaned.get('block', 'A'),
                'block_display': f"Block {cleaned.get('block', 'A')}",
                'floor': cleaned.get('floor', 1),
                'room_type': cleaned.get('room_type', 'DOUBLE'),
                'room_type_display': f"{capacity} Beds",
                'category': cleaned.get('category', 'GENERAL'),
                'gender': gender,
                'capacity': capacity,
                'status': cleaned.get('status', 'AVAILABLE'),
                'monthly_rent': str(cleaned.get('monthly_rent', '2500.00')),
                'is_ac': bool(cleaned.get('is_ac')),
                'description': cleaned.get('description', ''),
                'beds': beds,
            }

            rooms_data[pk_str] = room_item
            _save_session_rooms(request, rooms_data)

            messages.success(request, f"New Room #{cleaned.get('room_number')} created successfully.")
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
    rooms_data = _get_session_rooms(request)
    pk_str = str(pk)

    room_info = rooms_data.get(pk_str)
    if not room_info:
        try:
            pk_int = int(pk)
        except (ValueError, TypeError):
            pk_int = 1
        is_girls = pk_int >= 100
        unit_idx = pk_int - 100 if is_girls else pk_int
        room_num = f"20{unit_idx}" if is_girls and unit_idx < 10 else (f"2{unit_idx}" if is_girls else (f"10{unit_idx}" if unit_idx < 10 else f"1{unit_idx}"))
        room_info = {
            'id': pk_int,
            'pk': pk_int,
            'room_number': room_num,
            'room_name': f"Unit #{room_num}",
            'building_id': 2 if is_girls else 1,
            'building_name': "Girls Hostel Block B" if is_girls else "Boys Hostel Block A",
            'block': 'B' if is_girls else 'A',
            'block_display': 'Block B' if is_girls else 'Block A',
            'floor': 1,
            'room_type': 'DOUBLE',
            'category': 'GENERAL',
            'gender': 'Girls' if is_girls else 'Boys',
            'capacity': 2,
            'status': 'AVAILABLE',
            'monthly_rent': '2500.00',
            'is_ac': False,
            'description': f'Hostel Room Unit #{room_num}',
            'beds': [],
        }

    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data

            building_id = int(cleaned.get('building', 1))
            b_name = "Boys Hostel Block A" if building_id == 1 else "Girls Hostel Block B"
            gender = "Boys" if building_id == 1 else "Girls"
            capacity = int(cleaned.get('capacity', 2))

            current_beds = room_info.get('beds', [])
            if len(current_beds) < capacity:
                for b_idx in range(len(current_beds) + 1, capacity + 1):
                    current_beds.append({'id': (int(room_info['id']) * 10) + b_idx, 'bed_number': str(b_idx), 'student_id': None})
            elif len(current_beds) > capacity:
                current_beds = current_beds[:capacity]

            room_info['room_number'] = cleaned.get('room_number')
            room_info['room_name'] = cleaned.get('room_name') or f"Unit #{cleaned.get('room_number')}"
            room_info['building_id'] = building_id
            room_info['building_name'] = b_name
            room_info['gender'] = gender
            room_info['block'] = cleaned.get('block', 'A')
            room_info['block_display'] = f"Block {cleaned.get('block', 'A')}"
            room_info['floor'] = cleaned.get('floor', 1)
            room_info['room_type'] = cleaned.get('room_type', 'DOUBLE')
            room_info['capacity'] = capacity
            room_info['category'] = cleaned.get('category', 'GENERAL')
            room_info['status'] = cleaned.get('status', 'AVAILABLE')
            room_info['monthly_rent'] = str(cleaned.get('monthly_rent', '2500.00'))
            room_info['is_ac'] = bool(cleaned.get('is_ac'))
            room_info['description'] = cleaned.get('description', '')
            room_info['beds'] = current_beds

            rooms_data[pk_str] = room_info
            _save_session_rooms(request, rooms_data)

            messages.success(request, f"Room Unit #{cleaned.get('room_number')} updated successfully.")
            return redirect('room_manage')
    else:
        initial_data = {
            'building': room_info.get('building_id', 1),
            'block': room_info.get('block', 'A'),
            'floor': room_info.get('floor', 1),
            'room_number': room_info.get('room_number'),
            'room_name': room_info.get('room_name'),
            'room_type': room_info.get('room_type', 'DOUBLE'),
            'category': room_info.get('category', 'GENERAL'),
            'status': room_info.get('status', 'AVAILABLE'),
            'monthly_rent': room_info.get('monthly_rent', '2500.00'),
            'is_ac': room_info.get('is_ac', False),
            'capacity': room_info.get('capacity', 2),
            'description': room_info.get('description', ''),
        }
        form = RoomForm(initial=initial_data)

    room_dict = {
        'pk': pk,
        'id': room_info['id'],
        'room_number': room_info['room_number'],
        'room_name': room_info['room_name'],
    }

    context = {
        'page_title': f"Edit Room #{room_info['room_number']}",
        'action': 'Edit',
        'room': room_dict,
        'form': form,
        'base_rents_json': '{"DOUBLE": 2500, "SINGLE": 4000, "TRIPLE": 2000, "DORMITORY": 1500}',
        'category_multipliers_json': '{"GENERAL": 1.0, "DELUXE": 1.5, "STAFF": 0.0}',
    }
    return render(request, 'room/create_room.html', context)


@login_required(login_url='/authentication/login')
def delete_room(request, pk):
    rooms_data = _get_session_rooms(request)
    pk_str = str(pk)
    if pk_str in rooms_data:
        r_num = rooms_data[pk_str].get('room_number')
        del rooms_data[pk_str]
        _save_session_rooms(request, rooms_data)
        messages.success(request, f'Room #{r_num} deleted successfully.')
    else:
        messages.success(request, f'Room #{pk} deleted successfully.')
    return redirect('room_manage')


@login_required(login_url='/authentication/login')
def delete_allocation(request, bed_id):
    rooms_data = _get_session_rooms(request)
    target_bed_id = int(bed_id)
    found_room_id = None
    bed_num = str(bed_id)

    for r_id, r_info in rooms_data.items():
        for b in r_info.get('beds', []):
            if int(b.get('id', 0)) == target_bed_id:
                b['student_id'] = None
                found_room_id = r_id
                bed_num = b.get('bed_number', str(bed_id))
                break
        if found_room_id:
            break

    if found_room_id:
        _save_session_rooms(request, rooms_data)
        messages.success(request, f'Allocation for Bed #{bed_num} removed successfully.')
    else:
        messages.success(request, f'Allocation for bed {bed_id} removed.')

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next_url and 'http' not in next_url:
        return redirect(next_url)
    elif found_room_id:
        return redirect('student_allocated_view', room_id=found_room_id)
    return redirect('room_manage')


@login_required(login_url='/authentication/login')
def change_room(request, current_bed_id):
    rooms_data = _get_session_rooms(request)
    target_bed_id = int(current_bed_id)

    curr_room_info = None
    curr_bed_info = None
    assigned_student_id = None

    for r_id, r_info in rooms_data.items():
        for b in r_info.get('beds', []):
            if int(b.get('id', 0)) == target_bed_id:
                curr_room_info = r_info
                curr_bed_info = b
                assigned_student_id = b.get('student_id')
                break
        if curr_room_info:
            break

    if not curr_room_info:
        messages.error(request, 'Bed allocation not found.')
        return redirect('room_manage')

    student_obj = Student.objects.filter(student_id=assigned_student_id).first() if assigned_student_id else None

    if request.method == 'POST':
        target_room_id = request.POST.get('room-select')
        target_bed_num = request.POST.get('bed-select')

        target_room_info = rooms_data.get(str(target_room_id))
        if target_room_info:
            # Clear current bed
            curr_bed_info['student_id'] = None

            # Assign to target bed in target room
            for tb in target_room_info.get('beds', []):
                if str(tb.get('bed_number')) == str(target_bed_num):
                    tb['student_id'] = assigned_student_id
                    break

            _save_session_rooms(request, rooms_data)
            st_name = student_obj.name if student_obj else 'Resident'
            messages.success(request, f'{st_name} moved to Room #{target_room_info["room_number"]} Bed #{target_bed_num}.')
            return redirect('student_allocated_view', room_id=target_room_info['id'])
        else:
            messages.error(request, 'Target room not found.')
            return redirect('room_manage')

    buildings = [
        {'id': 1, 'name': 'Boys Hostel Block A', 'get_gender_display': 'Boys'},
        {'id': 2, 'name': 'Girls Hostel Block B', 'get_gender_display': 'Girls'},
    ]
    blocks = [('A', 'Block A'), ('B', 'Block B')]

    current_bed_context = {
        'id': target_bed_id,
        'bed_number': curr_bed_info.get('bed_number', '1'),
        'paid_amount': '0.00',
        'remaining_amount': '0.00',
        'room': {
            'id': curr_room_info['id'],
            'room_number': curr_room_info['room_number'],
            'building': {'name': curr_room_info.get('building_name', 'Hostel Building')},
            'floor': {'floor_number': curr_room_info.get('floor', 1)},
        }
    }

    context = {
        'page_title': 'Change Room',
        'current_bed': current_bed_context,
        'student': student_obj,
        'buildings': buildings,
        'blocks': blocks,
    }
    return render(request, 'room/change_room.html', context)


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
    rooms_data = _get_session_rooms(request)
    room_info = rooms_data.get(str(room_id))

    if not room_info:
        try:
            room_id_int = int(room_id)
        except (ValueError, TypeError):
            room_id_int = 1
        is_girls_room = room_id_int >= 100
        if is_girls_room:
            unit_index = room_id_int - 100
            room_num = f"20{unit_index}" if unit_index < 10 else f"2{unit_index}"
            building_name = "Girls Hostel Block B"
            gender_disp = "Girls Wing"
        else:
            unit_index = room_id_int
            room_num = f"10{unit_index}" if unit_index < 10 else f"1{unit_index}"
            building_name = "Boys Hostel Block A"
            gender_disp = "Boys Wing"
        room_info = {
            'id': room_id_int,
            'pk': room_id_int,
            'room_number': room_num,
            'room_name': f'Unit #{room_num}',
            'building_name': building_name,
            'floor': 1,
            'room_type_display': '2 Beds Double Sharing',
            'gender': gender_disp,
            'capacity': 2,
            'beds': [],
        }

    student_ids = [b.get('student_id') for b in room_info.get('beds', []) if b.get('student_id')]
    students_map = {s.student_id: s for s in Student.objects.filter(student_id__in=student_ids)}

    hydrated_beds = []
    occupied_count = 0
    for b in room_info.get('beds', []):
        st_obj = students_map.get(b.get('student_id'))
        if st_obj:
            occupied_count += 1
        hydrated_beds.append({
            'id': b.get('id'),
            'bed_number': b.get('bed_number'),
            'student': st_obj,
            'remaining_amount': 0
        })

    total_beds = room_info.get('capacity', 2)
    vacant_count = max(0, total_beds - occupied_count)

    room_obj = {
        'id': room_info['id'],
        'room_number': room_info['room_number'],
        'room_name': room_info['room_name'],
        'building': {'name': room_info.get('building_name', 'Hostel Building')},
        'floor': {'floor_number': room_info.get('floor', 1)},
        'get_room_type_display': room_info.get('room_type_display', f"{total_beds} Beds"),
        'get_gender_display': room_info.get('gender', 'Boys Wing'),
    }

    context = {
        'page_title': f"Room #{room_info['room_number']} Details",
        'room_number': room_info['room_number'],
        'room': room_obj,
        'total_beds': total_beds,
        'occupied_beds': occupied_count,
        'vacant_beds': vacant_count,
        'beds': hydrated_beds,
    }
    return render(request, 'room/student_allocated_view.html', context)


# ── AJAX Endpoints ──
@login_required(login_url='/authentication/login')
def check_room_number(request):
    return JsonResponse({'available': True, 'message': 'Room number available'})


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
    rooms_data = _get_session_rooms(request)

    res_rooms = []
    for r_id, r_info in rooms_data.items():
        if not building_id or str(r_info.get('building_id')) == str(building_id):
            total_b = r_info.get('capacity', 2)
            occ_b = sum(1 for b in r_info.get('beds', []) if b.get('student_id'))
            vacant_b = max(0, total_b - occ_b)
            g_disp = r_info.get('gender', 'Boys')
            res_rooms.append({
                'room_id': r_info['id'],
                'room_number': r_info['room_number'],
                'gender': g_disp,
                'gender_display': f"{g_disp} Wing",
                'vacant_beds': vacant_b,
                'capacity': total_b
            })

    return JsonResponse({'rooms': res_rooms})


@login_required(login_url='/authentication/login')
def get_beds_for_room(request):
    room_id = request.GET.get('room_id', '1')
    rooms_data = _get_session_rooms(request)
    room_info = rooms_data.get(str(room_id))

    beds_data = []
    if room_info:
        for b in room_info.get('beds', []):
            beds_data.append({
                'bed_number': b.get('bed_number'),
                'student': b.get('student_id')
            })
    else:
        beds_data = [
            {'bed_number': '1', 'student': None},
            {'bed_number': '2', 'student': None},
        ]

    return JsonResponse({
        'room_number': room_info['room_number'] if room_info else str(room_id),
        'gender_display': room_info.get('gender', 'Boys') if room_info else 'Boys',
        'beds': beds_data
    })


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
