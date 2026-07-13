from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count
from .forms import CreateRoomForm, CreateRoom
from .models import Room, Bed, Floor, HostelBuilding, CAPACITY_MAP
from student.models import Student
from django.urls import reverse
from paybill.models import FeeStructure
from django.contrib.auth.decorators import login_required
from authentication.decorators import role_required, permission_required
from django.core.exceptions import PermissionDenied
import json


@login_required(login_url='/authentication/login')
@permission_required('room', 'view')
def room_base(request):
    hostel = get_active_hostel(request)
    if not hostel:
        return render(request, 'room/room_base.html', {
            'error': 'No active hostel found.'
        })

    rooms = Room.objects.filter(hostel=hostel)
    beds = Bed.objects.filter(room__hostel=hostel)
    
    total_allocated_beds = beds.filter(student__isnull=False).count()
    total_unallocated_beds = beds.filter(student__isnull=True, room__status='ACTIVE').count()
    total_boys_rooms = rooms.filter(gender='BOY').count()
    total_girls_rooms = rooms.filter(gender='GIRL').count()
    total_available_rooms = rooms.filter(status='ACTIVE').count()
    total_maintenance_rooms = rooms.filter(status='MAINTENANCE').count()
    
    total_reserved_beds = beds.filter(room__category='RESERVED', student__isnull=True).count()
    total_students = Student.objects.filter(hostel=hostel).count()
    upcoming_vacancies = 0 # Placeholder for future logic

    return render(request, 'room/room_base.html', {
        'total_allocated_beds': total_allocated_beds,
        'total_unallocated_beds': total_unallocated_beds,
        'total_boys_rooms': total_boys_rooms,
        'total_girls_rooms': total_girls_rooms,
        'total_availabel_room': total_available_rooms,
        'total_maintenance_rooms': total_maintenance_rooms,
        'total_reserved_beds': total_reserved_beds,
        'upcoming_vacancies': upcoming_vacancies,
        'total_student': total_students,
        'active_hostel': hostel,
    })


@login_required(login_url='/authentication/login')
@permission_required('room', 'view')
def student_details_list(request):
    students = Student.objects.all()
    rooms = Room.objects.all()
    beds = Bed.objects.select_related('room', 'student').all()
    return render(request, 'room/student_details_list.html', {'students': students, 'rooms': rooms, 'beds': beds})


@login_required(login_url='/authentication/login')
@permission_required('room', 'view')
def room_manage(request):
    buildings = HostelBuilding.objects.filter(is_active=True)
    rooms = Room.objects.select_related('building', 'floor').order_by('room_number')
        
    selected_building_id = request.GET.get('building', '')
    q = request.GET.get('q', '').strip()

    if selected_building_id:
        rooms = rooms.filter(building_id=selected_building_id)
    if q:
        rooms = rooms.filter(
            Q(room_number__icontains=q) | Q(room_name__icontains=q)
        )

    selected_building = None
    if selected_building_id:
        selected_building = buildings.filter(pk=selected_building_id).first()

    return render(request, 'room/manage.html', {
        'rooms': rooms,
        'buildings': buildings,
        'selected_building': selected_building,
        'selected_building_id': selected_building_id,
        'search_query': q,
    })


@login_required(login_url='/authentication/login')
@permission_required('room', 'view')
def room_available(request):
    rooms = Room.objects.all().order_by('room_number')
    return render(request, 'room/available.html', {'rooms': rooms})


# ── AJAX: Rooms filtered by building (JSON) ───────────────────────────────────
@login_required(login_url='/authentication/login')
def rooms_by_building(request):
    building_id = request.GET.get('building_id', '')
    rooms_qs = Room.objects.select_related('building', 'floor').order_by('room_number')
    if building_id:
        rooms_qs = rooms_qs.filter(building_id=building_id)

    data = []
    for r in rooms_qs:
        occupied = r.beds.filter(student__isnull=False).count()
        total = r.beds.count()
        data.append({
            'id': r.id,
            'room_number': r.room_number,
            'room_name': r.room_name or '',
            'room_type': r.get_room_type_display(),
            'gender': r.get_gender_display(),
            'status': r.get_status_display(),
            'building': r.building.name if r.building else '',
            'block': r.get_block_display() if r.block else '',
            'capacity': r.capacity,
            'occupied': occupied,
            'available': total - occupied,
        })
    return JsonResponse({'rooms': data, 'count': len(data)})


# ── Hostel Building Management ────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
@permission_required('room', 'view')
def building_list(request):
    buildings = HostelBuilding.objects.annotate(room_count=Count('rooms')).order_by('name')
    return render(request, 'room/building_list.html', {'buildings': buildings})


@login_required(login_url='/authentication/login')
@permission_required('room', 'add')
def building_create(request):
    from .forms import HostelBuildingForm
    if request.method == 'POST':
        form = HostelBuildingForm(request.POST)
        if form.is_valid():
            building = form.save()
            # Auto-create floors based on total_floors
            total = building.total_floors or 0
            for fn in range(1, total + 1):
                from .models import HostelBlock
                block, _ = HostelBlock.objects.get_or_create(
                    building=building,
                    name='Main Block'
                )
                Floor.objects.get_or_create(building=building, block=block, floor_number=fn)
            messages.success(request, f'Building "{building.name}" created with {total} floor(s).')
            return redirect('building_list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = HostelBuildingForm()
    return render(request, 'room/building_form.html', {'form': form, 'action': 'Create'})


@login_required(login_url='/authentication/login')
@permission_required('room', 'add')
def building_edit(request, pk):
    from .forms import HostelBuildingForm
    building = get_object_or_404(HostelBuilding, pk=pk)

        
    if request.method == 'POST':
        form = HostelBuildingForm(request.POST, instance=building)
        if form.is_valid():
            form.save()
            messages.success(request, f'Building "{building.name}" updated.')
            return redirect('building_list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = HostelBuildingForm(instance=building)
    return render(request, 'room/building_form.html', {'form': form, 'action': 'Edit', 'building': building})


@login_required(login_url='/authentication/login')
@permission_required('room', 'delete')
def building_delete(request, pk):
    building = get_object_or_404(HostelBuilding, pk=pk)

        
    if request.method == 'POST':
        if Room.objects.filter(building=building).exists():
            messages.error(request, 'Cannot delete: rooms are assigned to this building.')
            return redirect('building_list')
        building.delete()
        messages.success(request, f'Building "{building.name}" deleted.')
    return redirect('building_list')


@login_required(login_url='/authentication/login')
@permission_required('room', 'add')
def building_toggle(request, pk):
    building = get_object_or_404(HostelBuilding, pk=pk)

        
    building.is_active = not building.is_active
    building.save()
    state = 'activated' if building.is_active else 'deactivated'
    messages.success(request, f'Building "{building.name}" {state}.')
    return redirect('building_list')


@login_required(login_url='/authentication/login')
@permission_required('room', 'add')
def room_allocate(request):
    rooms = Room.objects.all().order_by('room_number')
    students = Student.objects.all()
    available_rooms = Room.objects.filter(beds__student__isnull=True).distinct()
    buildings = HostelBuilding.objects.filter(is_active=True)
    from .models import BLOCK_CHOICES

    total_amount = FeeStructure.objects.aggregate(total=Sum('amount'))['total'] or 0

    context_base = {
        'rooms': available_rooms,
        'students': students,
        'buildings': buildings,
        'blocks': BLOCK_CHOICES,
        'total_amount': total_amount,
        'beds': []
    }

    if request.method == 'POST':
        if 'room-select' in request.POST and 'bed-select' not in request.POST:
            selected_room_val = request.POST.get('room-select', '').strip()
            try:
                if selected_room_val.isdigit():
                    room = Room.objects.get(pk=int(selected_room_val))
                else:
                    room = Room.objects.get(room_number=selected_room_val)
                unallocated_beds = room.beds.filter(student__isnull=True).select_related('student')
                unallocated_students = Student.objects.filter(bed__isnull=True)

                if room.gender == 'BOY':
                    unallocated_students = unallocated_students.filter(gender='Male')
                elif room.gender == 'GIRL':
                    unallocated_students = unallocated_students.filter(gender='Female')

                return render(request, 'room/allocate.html', {
                    **context_base,
                    'students': unallocated_students,
                    'beds': unallocated_beds,
                    'selected_room': room,
                })
            except (Room.DoesNotExist, Room.MultipleObjectsReturned):
                return render(request, 'room/allocate.html', {
                    **context_base,
                    'error': 'Invalid room number shadow'
                })
        elif 'bed-select' in request.POST:
            selected_room_val = request.POST.get('room-select', '').strip()
            selected_bed_number = request.POST.get('bed-select')
            selected_enrollment_number = request.POST.get('student-select')

            try:
                if selected_room_val.isdigit():
                    room = Room.objects.get(pk=int(selected_room_val))
                else:
                    room = Room.objects.get(room_number=selected_room_val)
                beds = room.beds.filter(bed_number=selected_bed_number)

                unallocated_students = Student.objects.filter(bed__isnull=True)
                if room.gender == 'BOY':
                    unallocated_students = unallocated_students.filter(gender='Male')
                elif room.gender == 'GIRL':
                    unallocated_students = unallocated_students.filter(gender='Female')

                if beds.exists():
                    bed = beds.first()
                    if bed.student is not None:
                        return render(request, 'room/allocate.html', {
                            **context_base,
                            'students': unallocated_students,
                            'beds': room.beds.filter(student__isnull=True),
                            'error': 'Bed is already allocated'
                        })
                    else:
                        try:
                            if selected_enrollment_number.isdigit():
                                student = Student.objects.get(pk=int(selected_enrollment_number))
                            else:
                                student = Student.objects.get(roll=selected_enrollment_number)
                            if Bed.objects.filter(student=student).exists():
                                return render(request, 'room/allocate.html', {
                                    **context_base,
                                    'students': unallocated_students,
                                    'beds': room.beds.filter(student__isnull=True),
                                    'error': 'Student is already allocated'
                                })

                            # Gender mismatch validation
                            if room.gender == 'BOY' and student.gender != 'Male':
                                return render(request, 'room/allocate.html', {
                                    **context_base,
                                    'students': unallocated_students,
                                    'beds': room.beds.filter(student__isnull=True),
                                    'error': f'This room/building ({room.room_number}) is for Boys, but student is {student.gender}'
                                })
                            elif room.gender == 'GIRL' and student.gender != 'Female':
                                return render(request, 'room/allocate.html', {
                                    **context_base,
                                    'students': unallocated_students,
                                    'beds': room.beds.filter(student__isnull=True),
                                    'error': f'This room/building ({room.room_number}) is for Girls, but student is {student.gender}'
                                })

                            yearly_amount = (room.monthly_rent or 0) * 12
                            bed.total_amount = yearly_amount
                            bed.remaining_amount = yearly_amount
                            bed.student = student
                            bed.save()
                            return redirect('room_manage')
                        except Student.DoesNotExist:
                            return render(request, 'room/allocate.html', {
                                **context_base,
                                'students': unallocated_students,
                                'beds': room.beds.filter(student__isnull=True),
                                'error': 'Student not found'
                            })
                else:
                    return render(request, 'room/allocate.html', {
                        **context_base,
                        'students': unallocated_students,
                        'beds': room.beds.filter(student__isnull=True),
                        'error': 'Bed not found'
                    })
            except Room.DoesNotExist:
                return render(request, 'room/allocate.html', {
                    **context_base,
                    'error': 'Invalid room number shadow'
                })
    else:
        return render(request, 'room/allocate.html', context_base)


# ── AJAX: Check room number uniqueness ────────────────────────────────────────
@login_required(login_url='/authentication/login')
def check_room_number(request):
    number = request.GET.get('number', '').strip()
    building_id = request.GET.get('building_id', '').strip()
    room_id = request.GET.get('room_id', '').strip()
    if not number:
        return JsonResponse({'available': False, 'message': 'Enter a room number.'})
    query = Room.objects.filter(room_number__iexact=number)
    if building_id:
        query = query.filter(building_id=building_id)
    if room_id:
        try:
            query = query.exclude(pk=int(room_id))
        except ValueError:
            pass
    exists = query.exists()
    return JsonResponse({
        'available': not exists,
        'message': 'Room number is available.' if not exists else f'Room "{number}" is already taken in this building.',
    })


# ── AJAX: Get floors for a given building ────────────────────────────────────
@login_required(login_url='/authentication/login')
def get_floors(request):
    building_id = request.GET.get('building_id', '')
    if not building_id:
        return JsonResponse({'floors': []})
    floors = Floor.objects.filter(building_id=building_id).order_by('floor_number')
    data = [{'id': f.id, 'label': f'Floor {f.floor_number}'} for f in floors]
    return JsonResponse({'floors': data})


# ── AJAX: Get rooms filtered by building, block, floor for allocation ──────────
@login_required(login_url='/authentication/login')
def get_rooms_for_allocation(request):
    building_id = request.GET.get('building_id')
    block = request.GET.get('block')
    floor_id = request.GET.get('floor_id')

    rooms_qs = Room.objects.filter(status='ACTIVE')
    if building_id:
        rooms_qs = rooms_qs.filter(building_id=building_id)
    if block:
        rooms_qs = rooms_qs.filter(block=block)
    if floor_id:
        rooms_qs = rooms_qs.filter(floor_id=floor_id)

    rooms_data = []
    for r in rooms_qs.order_by('room_number'):
        vacant_count = r.beds.filter(student__isnull=True).count()
        rooms_data.append({
            'room_id': r.pk,
            'room_number': r.room_number,
            'gender': r.gender,
            'gender_display': r.get_gender_display(),
            'vacant_beds': vacant_count,
            'capacity': r.capacity
        })
    return JsonResponse({'rooms': rooms_data})


# ── AJAX: Get beds and resident status for a room ──────────────────────────────
@login_required(login_url='/authentication/login')
def get_beds_for_room(request):
    room_id = request.GET.get('room_id')
    room_number = request.GET.get('room_number')
    building_id = request.GET.get('building_id')

    if not room_id and not room_number:
        return JsonResponse({'beds': []})

    try:
        if room_id:
            room = Room.objects.get(pk=room_id)
        elif building_id:
            room = Room.objects.get(room_number=room_number, building_id=building_id)
        else:
            room = Room.objects.get(room_number=room_number)
        beds = room.beds.all().order_by('bed_number')
        beds_data = []
        for b in beds:
            student_info = None
            if b.student:
                photo_url = b.student.photo.url if b.student.photo else '/static/image/User.jpg'
                student_info = {
                    'name': b.student.name,
                    'roll': b.student.roll,
                    'photo': photo_url,
                }
            beds_data.append({
                'id': b.id,
                'bed_number': b.bed_number,
                'student': student_info
            })
        return JsonResponse({
            'room_number': room.room_number,
            'gender': room.gender,
            'gender_display': room.get_gender_display(),
            'beds': beds_data
        })
    except Room.DoesNotExist:
        return JsonResponse({'beds': [], 'error': 'Room not found'})
    except Room.MultipleObjectsReturned:
        return JsonResponse({'beds': [], 'error': 'Multiple rooms found — please pass room_id'})


# ── AJAX: Get unallocated students filtered by gender ──────────────────────────
@login_required(login_url='/authentication/login')
def get_students_by_gender(request):
    room_gender = request.GET.get('room_gender')
    students = Student.objects.filter(bed__isnull=True, status='Active')
    
    if room_gender == 'BOY':
        students = students.filter(gender='Male')
    elif room_gender == 'GIRL':
        students = students.filter(gender='Female')

    students_data = [{'id': s.student_id, 'roll': s.roll, 'name': s.name, 'phone': s.phone_number} for s in students.order_by('name')]
    return JsonResponse({'students': students_data})


# ── Create Room (Main View) ───────────────────────────────────────────────────
@login_required(login_url='/authentication/login')
@permission_required('room', 'add')
def create_room(request):
    buildings = HostelBuilding.objects.filter(is_active=True)
    capacity_map = CAPACITY_MAP

    if request.method == 'POST':
        form = CreateRoomForm(request.POST, user=request.user)
        if form.is_valid():
            room = form.save()
            # Auto-create beds based on capacity
            cap = room.capacity
            for i in range(1, cap + 1):
                Bed.objects.create(
                    room=room,
                    bed_number=f'Bed {i}',
                    total_amount=room.monthly_rent or 0,
                    remaining_amount=room.monthly_rent or 0,
                    paid_amount=0,
                )
            messages.success(
                request,
                f'Room {room.room_number} created successfully with {cap} bed{"s" if cap != 1 else ""}.'
            )
            return redirect('room_manage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CreateRoomForm(user=request.user)

    return render(request, 'room/create_room.html', {
        'form': form,
        'buildings': buildings,
        'capacity_map': capacity_map,
    })


@login_required(login_url='/authentication/login')
@permission_required('room', 'change')
def edit_room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    buildings = HostelBuilding.objects.filter(is_active=True)
    capacity_map = CAPACITY_MAP

    if request.method == 'POST':
        old_capacity = room.capacity
        old_rent = room.monthly_rent
        form = CreateRoomForm(request.POST, instance=room, user=request.user)
        if form.is_valid():
            new_capacity = form.cleaned_data['capacity']

            # If capacity decreases, verify no students are in the deleted beds
            if new_capacity < old_capacity:
                total_allocated = room.beds.filter(student__isnull=False).count()
                if total_allocated > new_capacity:
                    messages.error(request, f"Cannot reduce capacity to {new_capacity} as there are {total_allocated} occupied bed{'s' if total_allocated != 1 else ''} in this room.")
                    return render(request, 'room/create_room.html', {
                        'form': form,
                        'buildings': buildings,
                        'capacity_map': capacity_map,
                        'room': room,
                        'action': 'Edit',
                    })

            room = form.save()

            # Adjust beds
            current_beds_count = room.beds.count()
            if new_capacity > current_beds_count:
                for i in range(current_beds_count + 1, new_capacity + 1):
                    Bed.objects.create(
                        room=room,
                        bed_number=f'Bed {i}',
                        total_amount=room.monthly_rent or 0,
                        remaining_amount=room.monthly_rent or 0,
                        paid_amount=0,
                    )
            elif new_capacity < current_beds_count:
                # Delete excess vacant beds from the end (prefer deleting empty ones)
                excess_count = current_beds_count - new_capacity
                vacant_beds = list(room.beds.filter(student__isnull=True).order_by('-bed_number'))
                beds_to_delete = vacant_beds[:excess_count]
                for eb in beds_to_delete:
                    eb.delete()
                # Rename the remaining beds so they are ordered 1..N
                all_beds = room.beds.all().order_by('id')
                for idx, b in enumerate(all_beds, 1):
                    b.bed_number = f'Bed {idx}'
                    b.save()

            # If monthly rent changed, update empty beds total/remaining amounts
            if room.monthly_rent != old_rent:
                for bed in room.beds.filter(student__isnull=True):
                    bed.total_amount = room.monthly_rent or 0
                    bed.remaining_amount = room.monthly_rent or 0
                    bed.save()

            messages.success(request, f'Room {room.room_number} updated successfully.')
            return redirect('room_manage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CreateRoomForm(instance=room, user=request.user)

    return render(request, 'room/create_room.html', {
        'form': form,
        'buildings': buildings,
        'capacity_map': capacity_map,
        'room': room,
        'action': 'Edit',
    })


@login_required(login_url='/authentication/login')
@permission_required('room', 'delete')
def delete_room(request, pk):
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        messages.error(request, 'Room does not exist.')
        return redirect('room_manage')
        


    allocated_beds = room.beds.filter(student__isnull=False).exists()
    if allocated_beds:
        messages.error(request, 'Room cannot be deleted. Please transfer allocated beds first.')
        return redirect('room_manage')

    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully.')
        return redirect('room_manage')

    return redirect('room_manage')


@login_required(login_url='/authentication/login')
@permission_required('room', 'delete')
def delete_allocation(request, bed_id):
    bed = get_object_or_404(Bed, id=bed_id)
    room_id = bed.room.id
    if request.method == 'POST':
        bed.student = None
        bed.paid_amount = 0
        bed.remaining_amount = 0
        bed.total_amount = 0
        bed.save()
        messages.success(request, 'Allocation deleted successfully.')
    
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('student_allocated_view', room_id=room_id)


@login_required(login_url='/authentication/login')
@permission_required('room', 'view')
def student_allocated_view(request, room_id):
    rooms = Room.objects.all().order_by('room_number')
    room = get_object_or_404(Room, pk=room_id)
    beds = room.beds.select_related('student').all()
    total_beds = beds.count()
    occupied_beds = beds.filter(student__isnull=False).count()
    vacant_beds = total_beds - occupied_beds

    return render(request, 'room/student_allocated_view.html', {
        'room': room,
        'room_number': room.room_number,
        'rooms': rooms,
        'beds': beds,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'vacant_beds': vacant_beds,
    })


@login_required(login_url='/authentication/login')
def search_unallocated_students(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'students': []})

    allocated_student_ids = Bed.objects.filter(student__isnull=False).values_list('student_id', flat=True)
    students = Student.objects.filter(
        status='Active'
    ).exclude(
        student_id__in=allocated_student_ids
    ).filter(
        Q(name__icontains=q) | Q(roll__icontains=q)
    ).order_by('name')[:15]

    students_data = [{
        'id': s.student_id,
        'name': s.name,
        'roll': s.roll,
        'photo': s.photo.url if s.photo else None,
    } for s in students]

    return JsonResponse({'students': students_data})


@login_required(login_url='/authentication/login')
@permission_required('room', 'change')
def allocate_bed_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)
    try:
        data = json.loads(request.body)
        bed_id = data.get('bed_id')
        student_id = data.get('student_id')
        
        bed = get_object_or_404(Bed, id=bed_id)
        student = get_object_or_404(Student, student_id=student_id)
        
        room = bed.room
        if room.gender == 'BOY' and student.gender != 'Male':
            return JsonResponse({'status': 'error', 'message': f'This room/building ({room.room_number}) is for Boys, but student is {student.gender}.'})
        elif room.gender == 'GIRL' and student.gender != 'Female':
            return JsonResponse({'status': 'error', 'message': f'This room/building ({room.room_number}) is for Girls, but student is {student.gender}.'})
            
        already_allocated = Bed.objects.filter(student=student).exists()
        if already_allocated:
            return JsonResponse({'status': 'error', 'message': f'Student {student.name} is already allocated to a bed.'})
        
        yearly_amount = (room.monthly_rent or 0) * 12
        bed.total_amount = yearly_amount
        bed.remaining_amount = yearly_amount
        bed.paid_amount = 0
        bed.student = student
        bed.save()
        
        return JsonResponse({'status': 'success', 'message': f'Bed {bed.bed_number} successfully allocated to {student.name}.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def get_active_hostel(request):
    from authentication.models import Hostel
    hostels = Hostel.objects.all()

    active_hostel_id = request.session.get('active_hostel_id')
    if active_hostel_id:
        hostel = hostels.filter(id=active_hostel_id).first()
        if hostel:
            return hostel
    hostel = hostels.first()
    if hostel and request.user.is_authenticated:
        request.session['active_hostel_id'] = hostel.id
    return hostel


@login_required(login_url='/authentication/login')
@permission_required('room', 'change')
def room_auto_allocate(request):
    """
    Dry-run recommendation list preview prior to bulk allocation.
    """
    hostel = get_active_hostel(request)
    if not hostel:
        messages.error(request, 'No active hostel found. Please build a hostel entry first.')
        return redirect('room_base')

    unallocated_students = Student.objects.filter(hostel=hostel, status='Active', bed__isnull=True).order_by('name')
    vacant_beds = Bed.objects.filter(room__hostel=hostel, student__isnull=True, room__status='ACTIVE').select_related('room', 'room__building')

    recommendations = []
    assigned_bed_ids = set()
    
    boys_beds = [b for b in vacant_beds if b.room.gender == 'BOY']
    girls_beds = [b for b in vacant_beds if b.room.gender == 'GIRL']

    for student in unallocated_students:
        allocated = False
        target_beds = boys_beds if student.gender == 'Male' else girls_beds
        
        for bed in target_beds:
            if bed.id not in assigned_bed_ids:
                recommendations.append({
                    'student': student,
                    'bed': bed,
                    'room': bed.room,
                    'building': bed.room.building,
                })
                assigned_bed_ids.add(bed.id)
                allocated = True
                break
        if not allocated:
            recommendations.append({
                'student': student,
                'bed': None,
                'status': 'No matching vacant beds available'
            })

    return render(request, 'room/auto_allocate.html', {
        'recommendations': recommendations,
        'unallocated_count': unallocated_students.count(),
        'vacant_beds_count': vacant_beds.count(),
    })


@login_required(login_url='/authentication/login')
@permission_required('room', 'change')
def room_auto_allocate_execute(request):
    """
    Database execute transaction for bulk allocation of matched students.
    """
    if request.method != 'POST':
        return redirect('room_auto_allocate')

    hostel = get_active_hostel(request)
    if not hostel:
        messages.error(request, 'No active hostel found.')
        return redirect('room_base')

    unallocated_students = Student.objects.filter(hostel=hostel, status='Active', bed__isnull=True).order_by('name')
    vacant_beds = Bed.objects.filter(room__hostel=hostel, student__isnull=True, room__status='ACTIVE').select_related('room')

    boys_beds = list(vacant_beds.filter(room__gender='BOY'))
    girls_beds = list(vacant_beds.filter(room__gender='GIRL'))
    
    allocated_count = 0
    from django.db import transaction

    with transaction.atomic():
        for student in unallocated_students:
            target_beds = boys_beds if student.gender == 'Male' else girls_beds
            if target_beds:
                bed = target_beds.pop(0)
                yearly_amount = (bed.room.monthly_rent or 0) * 12
                bed.total_amount = yearly_amount
                bed.remaining_amount = yearly_amount
                bed.paid_amount = 0
                bed.student = student
                bed.save()
                allocated_count += 1

    if allocated_count > 0:
        messages.success(request, f'Smart Engine successfully auto-allocated {allocated_count} student(s)!')
    else:
        messages.warning(request, 'No auto-allocations were performed.')

    return redirect('room_manage')

