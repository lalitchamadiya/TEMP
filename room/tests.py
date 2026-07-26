from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from room.models import HostelBuilding, Room, Bed
from student.models import Student


class RoomManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password', is_superuser=True, is_staff=True)
        self.client = Client()
        self.client.force_login(self.user)

        self.building = HostelBuilding.objects.create(
            name='Boys Block A',
            code='BH-A',
            gender='Boys',
            total_floors=3,
            is_active=True
        )

        self.room_a = Room.objects.create(
            building=self.building,
            room_number='101',
            room_name='Boys Unit 101',
            block='A',
            floor=1,
            room_type='2_BED',
            category='GENERAL',
            gender='Boys',
            capacity=2,
            status='AVAILABLE',
            monthly_rent=2500.00
        )
        self.room_b = Room.objects.create(
            building=self.building,
            room_number='102',
            room_name='Boys Unit 102',
            block='A',
            floor=1,
            room_type='2_BED',
            category='GENERAL',
            gender='Boys',
            capacity=2,
            status='AVAILABLE',
            monthly_rent=2500.00
        )

        self.bed_a1 = Bed.objects.create(room=self.room_a, bed_number='1')
        self.bed_a2 = Bed.objects.create(room=self.room_a, bed_number='2')
        self.bed_b1 = Bed.objects.create(room=self.room_b, bed_number='1')

        self.student = Student.objects.create(
            name='John Doe',
            roll='1001',
            email='john@example.com',
            gender='Male',
            status='Active'
        )

        self.bed_a1.student = self.student
        self.bed_a1.save()

    def test_room_dashboard_view(self):
        response = self.client.get(reverse('room_base'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'room/room_base.html')

    def test_room_manage_view(self):
        response = self.client.get(reverse('room_manage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'room/manage.html')

    def test_change_room(self):
        url = reverse('change_room', args=[self.bed_a1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            'room-select': self.room_b.id,
            'bed-select': '1',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('student_allocated_view', args=[self.room_b.id]))

        self.bed_a1.refresh_from_db()
        self.bed_b1.refresh_from_db()

        self.assertIsNone(self.bed_a1.student)
        self.assertEqual(self.bed_b1.student, self.student)
