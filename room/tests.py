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

    def test_delete_room_with_allocated_bed_fails(self):
        url = reverse('delete_room', args=[self.room_a.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('room_manage'))
        self.assertTrue(Room.objects.filter(pk=self.room_a.id).exists())

    def test_delete_building_with_allocated_bed_fails(self):
        url = reverse('building_delete', args=[self.building.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('building_list'))
        self.assertTrue(HostelBuilding.objects.filter(pk=self.building.id).exists())

    def test_year_wise_building_fee_structure(self):
        from room.models import BuildingFeeStructure
        from decimal import Decimal

        # 2026 Fee Structure: ₹60,000 / year
        fee_2026 = BuildingFeeStructure.objects.create(
            building=self.building,
            academic_year='2026',
            fee_type='YEARLY_PER_STUDENT',
            yearly_fee_per_student=Decimal('60000.00'),
            is_active=True
        )

        # 2027 Fee Structure: ₹65,000 / year
        fee_2027 = BuildingFeeStructure.objects.create(
            building=self.building,
            academic_year='2027',
            fee_type='YEARLY_PER_STUDENT',
            yearly_fee_per_student=Decimal('65000.00'),
            is_active=True
        )

        # Student admitted in 2026
        student_2026 = Student.objects.create(
            name='Student 2026',
            roll='202601',
            email='student2026@example.com',
            academic_year='2026',
            status='Active'
        )
        self.bed_a1.student = student_2026
        self.bed_a1.save()

        fee_info_2026 = student_2026.get_fee_info()
        self.assertEqual(fee_info_2026['yearly_fee'], Decimal('60000.00'))
        self.assertEqual(fee_info_2026['academic_year'], '2026')

        # Student admitted in 2027
        student_2027 = Student.objects.create(
            name='Student 2027',
            roll='202701',
            email='student2027@example.com',
            academic_year='2027',
            status='Active'
        )
        self.bed_a2.student = student_2027
        self.bed_a2.save()

        fee_info_2027 = student_2027.get_fee_info()
        self.assertEqual(fee_info_2027['yearly_fee'], Decimal('65000.00'))
        self.assertEqual(fee_info_2027['academic_year'], '2027')

    def test_fee_manager_and_transfer_recalculation(self):
        from room.models import HostelBuilding, BuildingFeeStructure, Room, Bed
        from student.models import Student, StudentFeePayment
        from decimal import Decimal

        # Building A: Fee ₹60,000 for 2026
        BuildingFeeStructure.objects.create(
            building=self.building,
            academic_year='2026',
            fee_type='YEARLY_PER_STUDENT',
            yearly_fee_per_student=Decimal('60000.00'),
            is_active=True
        )

        # Building B: Fee ₹75,000 for 2026
        building_b = HostelBuilding.objects.create(
            name='Boys Block B',
            code='BH-B',
            gender='Boys',
            total_floors=3,
            is_active=True
        )
        BuildingFeeStructure.objects.create(
            building=building_b,
            academic_year='2026',
            fee_type='YEARLY_PER_STUDENT',
            yearly_fee_per_student=Decimal('75000.00'),
            is_active=True
        )
        room_b_building = Room.objects.create(
            building=building_b,
            room_number='201',
            block='B',
            floor=1,
            capacity=2,
            status='AVAILABLE'
        )
        bed_b_building = Bed.objects.create(room=room_b_building, bed_number='1')

        # Student admitted in 2026 allocated to Building A
        student_test = Student.objects.create(
            name='Alice FeeTest',
            roll='202699',
            email='alice@example.com',
            academic_year='2026',
            status='Active'
        )
        self.bed_a1.student = student_test
        self.bed_a1.save()

        # Step 1: Check initial fee summary in Building A
        summary1 = student_test.get_calculated_fee_summary()
        self.assertEqual(summary1['total_fee'], Decimal('60000.00'))
        self.assertEqual(summary1['paid_fee'], Decimal('0.00'))
        self.assertEqual(summary1['remaining_fee'], Decimal('60000.00'))
        self.assertEqual(summary1['status'], 'DUE')

        # Step 2: Record payment of ₹20,000
        StudentFeePayment.objects.create(
            student=student_test,
            academic_year='2026',
            amount_paid=Decimal('20000.00'),
            payment_method='ONLINE'
        )

        summary2 = student_test.get_calculated_fee_summary()
        self.assertEqual(summary2['paid_fee'], Decimal('20000.00'))
        self.assertEqual(summary2['remaining_fee'], Decimal('40000.00'))
        self.assertEqual(summary2['status'], 'PARTIAL')

        # Step 3: Bed Transfer to Building B via change_room
        url = reverse('change_room', args=[self.bed_a1.id])
        data = {
            'room-select': room_b_building.id,
            'bed-select': '1',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('student_allocated_view', args=[room_b_building.id]))

        # Step 4: Verify fee recalculation in Building B with carried forward paid fee
        self.bed_a1.refresh_from_db()
        bed_b_building.refresh_from_db()
        self.assertIsNone(self.bed_a1.student)
        self.assertEqual(bed_b_building.student, student_test)

        summary3 = student_test.get_calculated_fee_summary()
        self.assertEqual(summary3['building_name'], 'Boys Block B')
        self.assertEqual(summary3['total_fee'], Decimal('75000.00'))
        self.assertEqual(summary3['paid_fee'], Decimal('20000.00')) # Carried forward payment
        self.assertEqual(summary3['remaining_fee'], Decimal('55000.00')) # 75,000 - 20,000 = 55,000

