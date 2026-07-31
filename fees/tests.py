from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from student.models import Student
from room.models import HostelBuilding, Room, Bed
from fees.models import (
    FeeCategory, FeeComponent, FeeStructure, FeeStructureComponent,
    Invoice, PaymentTransaction, Receipt, Refund, StudentLedger
)
from fees.services.invoice_generator import InvoiceGenerator
from fees.services.payment_processor import PaymentProcessor
from fees.services.ledger_service import LedgerService


class FeesERPTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password123')
        self.building = HostelBuilding.objects.create(name='A Block', gender='BOYS')
        self.room = Room.objects.create(building=self.building, room_number='101', room_type='2_BED', capacity=2, monthly_rent=2500)
        self.bed = Bed.objects.create(room=self.room, bed_number='A1')
        self.student = Student.objects.create(name='John Doe', email='john@example.com', phone_number='9876543210')
        self.bed.student = self.student
        self.bed.save()

        # Categories & Components
        self.cat_rent = FeeCategory.objects.create(name='Hostel Rent', code='RENT')
        self.cat_mess = FeeCategory.objects.create(name='Mess Fee', code='MESS')

        self.comp_rent = FeeComponent.objects.create(name='Base Rent', category=self.cat_rent, default_amount=2500)
        self.comp_mess = FeeComponent.objects.create(name='Mess Charge', category=self.cat_mess, default_amount=3000)

        # Structure
        self.structure = FeeStructure.objects.create(
            name='Standard Boys 2026', building=self.building, room_type='2_BED',
            academic_year='2026-27', payment_frequency='MONTHLY', include_gst=True, gst_percent=18
        )
        FeeStructureComponent.objects.create(fee_structure=self.structure, fee_component=self.comp_rent, amount=2500, is_gst_applicable=True)
        FeeStructureComponent.objects.create(fee_structure=self.structure, fee_component=self.comp_mess, amount=3000, is_gst_applicable=False)

    def test_invoice_generation_and_ledger(self):
        """Test invoice creation, GST calculation, line items, installments & ledger post."""
        invoice = InvoiceGenerator.generate_invoice_for_student(self.student, self.bed, self.structure)
        self.assertIsNotNone(invoice)
        self.assertTrue(invoice.invoice_number.startswith('HMS-INV-'))
        # GST = 2500 * 0.18 = 450. Total = 2500 + 3000 + 450 = 5950
        self.assertEqual(invoice.total_amount, Decimal('5950.00'))
        self.assertEqual(invoice.pending_amount, Decimal('5950.00'))
        self.assertEqual(invoice.items.count(), 2)
        self.assertEqual(invoice.installments.count(), 12)

        # Ledger check
        balance = LedgerService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('5950.00'))

    def test_payment_processing_and_receipt(self):
        """Test partial payment, balance reduction, receipt & QR code generation."""
        invoice = InvoiceGenerator.generate_invoice_for_student(self.student, self.bed, self.structure)
        txn, receipt = PaymentProcessor.process_payment(
            invoice=invoice,
            amount_paid=2000,
            payment_method='UPI',
            recorded_by=self.user,
            upi_ref='UPI9988776655'
        )

        self.assertEqual(txn.amount_paid, Decimal('2000.00'))
        self.assertEqual(invoice.paid_amount, Decimal('2000.00'))
        self.assertEqual(invoice.pending_amount, Decimal('3950.00'))
        self.assertEqual(invoice.status, 'PARTIAL')

        # Receipt check
        self.assertTrue(receipt.receipt_number.startswith('NBNH-'))
        self.assertIsNotNone(receipt.qr_code_hash)

        # Ledger check: 5950 - 2000 = 3950
        balance = LedgerService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('3950.00'))

    def test_refund_workflow(self):
        """Test transaction refunding and balance reversal."""
        invoice = InvoiceGenerator.generate_invoice_for_student(self.student, self.bed, self.structure)
        txn, receipt = PaymentProcessor.process_payment(invoice=invoice, amount_paid=2000, payment_method='CASH', recorded_by=self.user)

        refund = PaymentProcessor.refund_transaction(txn.id, reason='Overpayment refund', approved_by=self.user)
        self.assertEqual(refund.status, 'APPROVED')

        # Invoice should revert back to unpaid / full balance
        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal('0.00'))
        self.assertEqual(invoice.pending_amount, Decimal('5950.00'))

        # Balance restored to 5950
        balance = LedgerService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('5950.00'))
