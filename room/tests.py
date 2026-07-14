from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from authentication.models import Hostel
from room.models import HostelBuilding, Floor, Room, Bed
from student.models import Student

class RoomChangeTests(TestCase):
    def setUp(self):
        # Create user & client
        self.user = User.objects.create_user(username='warden', password='password')
        self.client = Client()
        
        # Grant room change perm (superuser bypasses)
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        # Create active hostel
        self.hostel = Hostel.objects.create(name='Central Hostel', is_active=True)
        # Setup session for active hostel (as processed by get_active_hostel)
        session = self.client.session
        session['active_hostel_id'] = self.hostel.id
        session.save()

        # Create building
        self.building = HostelBuilding.objects.create(
            name='Boys Block A',
            hostel=self.hostel,
            gender='BOY',
            is_active=True
        )

        # Create block
        from room.models import HostelBlock
        self.block = HostelBlock.objects.create(
            building=self.building,
            name='A',
            is_active=True
        )

        # Create floor
        self.floor = Floor.objects.create(
            building=self.building,
            block=self.block,
            floor_number=1
        )

        # Create rooms
        self.room_a = Room.objects.create(
            room_number='101',
            building=self.building,
            floor=self.floor,
            hostel=self.hostel,
            gender='BOY',
            status='ACTIVE',
            room_type='CUSTOM',
            capacity=2,
            monthly_rent=1500
        )
        self.room_b = Room.objects.create(
            room_number='102',
            building=self.building,
            floor=self.floor,
            hostel=self.hostel,
            gender='BOY',
            status='ACTIVE',
            room_type='CUSTOM',
            capacity=2,
            monthly_rent=2000
        )

        # Create beds
        self.bed_a1 = Bed.objects.create(room=self.room_a, bed_number='1')
        self.bed_a2 = Bed.objects.create(room=self.room_a, bed_number='2')
        self.bed_b1 = Bed.objects.create(room=self.room_b, bed_number='1')

        # Create student
        self.student_user = User.objects.create_user(username='student1', password='pwd')
        self.student = Student.objects.create(
            user=self.student_user,
            name='John Doe',
            roll='1001',
            email='john@example.com',
            gender='Male',
            status='Active'
        )

        # Allocate bed_a1 to student (initial state)
        self.bed_a1.student = self.student
        self.bed_a1.total_amount = 18000
        self.bed_a1.remaining_amount = 18000
        self.bed_a1.paid_amount = 0
        self.bed_a1.save()

    def test_change_room_get_request(self):
        url = reverse('change_room', args=[self.bed_a1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'room/change_room.html')
        self.assertIn('student', response.context)
        self.assertEqual(response.context['student'], self.student)

    def test_change_room_post_success(self):
        url = reverse('change_room', args=[self.bed_a1.id])
        data = {
            'room-select': self.room_b.id,
            'bed-select': '1',
        }
        # Post request
        response = self.client.post(url, data)
        
        # Verify redirect to student_allocated_view
        self.assertRedirects(response, reverse('student_allocated_view', args=[self.room_b.id]))

        # Refresh from db
        self.bed_a1.refresh_from_db()
        self.bed_b1.refresh_from_db()

        # Check deallocation
        self.assertIsNone(self.bed_a1.student)
        self.assertEqual(self.bed_a1.total_amount, 0)
        self.assertEqual(self.bed_a1.remaining_amount, 0)

        # Check target allocation
        self.assertEqual(self.bed_b1.student, self.student)
        # Rent should be new room monthly rent (2000) * 12 = 24000
        self.assertEqual(self.bed_b1.total_amount, 24000)
        self.assertEqual(self.bed_b1.remaining_amount, 24000)

        # Verify AuditLog created
        from authentication.models import AuditLog
        log = AuditLog.objects.filter(actor=self.user, action='edit').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.target_user, self.student_user)
        self.assertIn("Changed room for student John Doe", log.details)


class RoomPricingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password', is_superuser=True, is_staff=True)
        self.client = Client()
        self.client.force_login(self.user)
        self.hostel = Hostel.objects.create(name='Theme Hostel', is_active=True)
        session = self.client.session
        session['active_hostel_id'] = self.hostel.id
        session.save()

    def test_pricing_defaults_prepopulate(self):
        url = reverse('fee_structure')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verify pricing settings tables are pre-populated
        from room.models import RoomTypePricing, RoomCategoryPricing
        self.assertTrue(RoomTypePricing.objects.filter(hostel=self.hostel).exists())
        self.assertTrue(RoomCategoryPricing.objects.filter(hostel=self.hostel).exists())

    def test_pricing_save_and_suggested_rent(self):
        from room.models import RoomTypePricing, RoomCategoryPricing, Room
        # Prepopulate
        self.client.get(reverse('fee_structure'))

        # Post new custom prices
        url = reverse('fee_structure')
        data = {
            'action': 'save_prices',
            'price_DOUBLE': '6500.00',
            'mult_VIP': '1.50',
            'price_SINGLE': '8500.00',
            'mult_GENERAL': '1.00',
        }
        # Include all other keys from the categories to prevent defaults
        for key in ['TRIPLE', 'DORMITORY', 'DELUXE', 'AC', 'NON_AC']:
            data[f'price_{key}'] = '5000.00'
        for key in ['STAFF', 'RESERVED']:
            data[f'mult_{key}'] = '0.00'

        response = self.client.post(url, data)
        self.assertRedirects(response, url)

        # Verify database has updated pricing
        double_pricing = RoomTypePricing.objects.get(hostel=self.hostel, room_type='DOUBLE')
        self.assertEqual(double_pricing.base_rent, 6500.00)
        vip_pricing = RoomCategoryPricing.objects.get(hostel=self.hostel, category='VIP')
        self.assertEqual(vip_pricing.multiplier, 1.50)

        # Create room of type DOUBLE and category VIP, verify calculate_suggested_rent() matches
        building = HostelBuilding.objects.create(name='Theme Building', hostel=self.hostel)
        room = Room(
            room_number='201',
            building=building,
            hostel=self.hostel,
            room_type='DOUBLE',
            category='VIP',
            is_ac=False
        )
        # Suggested rent = 6500 * 1.5 = 9750
        suggested = room.calculate_suggested_rent()
        self.assertEqual(suggested, 9750.00)
