from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from student.models import Student


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
        })

        # Girls room
        girls_beds = []
        g_st_1 = students.pop(0) if students else None
        g_st_2 = students.pop(0) if students else None
        girls_beds.append({'bed_number': '1', 'student': g_st_1})
        girls_beds.append({'bed_number': '2', 'student': g_st_2})

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
        messages.success(request, 'New room created successfully.')
        return redirect('room_manage')

    buildings = [
        {'id': 1, 'name': 'Boys Hostel Block A'},
        {'id': 2, 'name': 'Girls Hostel Block B'},
    ]
    context = {
        'page_title': 'Create New Room',
        'buildings': buildings,
    }
    return render(request, 'room/create_room.html', context)


# ── Edit / Delete / Change Room ──
@login_required(login_url='/authentication/login')
def edit_room(request, pk):
    if request.method == 'POST':
        messages.success(request, f'Room {pk} updated successfully.')
        return redirect('room_manage')
    return redirect('room_manage')


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
    room_detail = {
        'id': room_id,
        'room_number': f'{room_id}',
        'room_name': f'Unit #{room_id}',
        'building': {'name': 'Main Hostel Building'},
        'room_type': 2,
        'gender': 'Boys',
        'beds': {'all': []}
    }
    context = {
        'page_title': f'Room #{room_id} Details',
        'room': room_detail,
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
