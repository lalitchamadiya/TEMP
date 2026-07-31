from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from fees.models import (
    Invoice, InvoiceItem, StudentInstallment, FeeStructure, FeeStructureComponent
)
from fees.services.receipt_generator import ReceiptGenerator
from fees.services.ledger_service import LedgerService


class InvoiceGenerator:
    @staticmethod
    @transaction.atomic
    def generate_invoice_for_student(student, bed, fee_structure, issue_date=None, due_date=None):
        """
        Creates an immutable Invoice, InvoiceItems, Installment Breakdown,
        and posts an entry to the Student Financial Ledger.
        """
        if not issue_date:
            issue_date = timezone.now().date()
        if not due_date:
            due_date = issue_date + timedelta(days=30)

        inv_num = ReceiptGenerator.generate_invoice_number()

        # Calculate totals from components
        struct_components = FeeStructureComponent.objects.filter(fee_structure=fee_structure)
        subtotal = Decimal('0.00')
        gst_total = Decimal('0.00')

        for sc in struct_components:
            subtotal += sc.amount
            if fee_structure.include_gst and sc.is_gst_applicable:
                gst_total += sc.amount * (fee_structure.gst_percent / Decimal('100.00'))

        total_amount = subtotal + gst_total

        invoice = Invoice.objects.create(
            invoice_number=inv_num,
            student=student,
            bed=bed,
            fee_structure=fee_structure,
            academic_year=fee_structure.academic_year,
            subtotal=subtotal,
            gst_amount=gst_total,
            discount_amount=Decimal('0.00'),
            fine_amount=Decimal('0.00'),
            total_amount=total_amount,
            paid_amount=Decimal('0.00'),
            pending_amount=total_amount,
            status='ISSUED',
            issue_date=issue_date,
            due_date=due_date,
            is_locked=True,
        )

        # Create Line Items
        for sc in struct_components:
            comp_gst = Decimal('0.00')
            if fee_structure.include_gst and sc.is_gst_applicable:
                comp_gst = sc.amount * (fee_structure.gst_percent / Decimal('100.00'))

            InvoiceItem.objects.create(
                invoice=invoice,
                fee_component=sc.fee_component,
                component_name=sc.fee_component.name,
                base_amount=sc.amount,
                gst_amount=comp_gst,
                discount_amount=Decimal('0.00'),
                net_amount=sc.amount + comp_gst,
            )

        # Build Installments
        freq = fee_structure.payment_frequency
        num_installments = 1
        if freq == 'MONTHLY':
            num_installments = 12
        elif freq == 'QUARTERLY':
            num_installments = 4
        elif freq == 'HALF_YEARLY':
            num_installments = 2

        inst_amount = total_amount / Decimal(str(num_installments))

        curr_due = issue_date
        for i in range(1, num_installments + 1):
            if i > 1:
                if freq == 'MONTHLY':
                    curr_due = curr_due + timedelta(days=30)
                elif freq == 'QUARTERLY':
                    curr_due = curr_due + timedelta(days=90)
                elif freq == 'HALF_YEARLY':
                    curr_due = curr_due + timedelta(days=180)

            StudentInstallment.objects.create(
                invoice=invoice,
                installment_no=i,
                due_date=curr_due,
                amount=inst_amount,
                paid_amount=Decimal('0.00'),
                status='UNPAID',
            )

        # Post to Student Financial Ledger
        LedgerService.record_entry(
            student=student,
            transaction_type='INVOICE',
            reference_no=inv_num,
            debit=total_amount,
            credit=Decimal('0.00'),
            description=f"Hostel Fee Invoice #{inv_num} issued ({fee_structure.name})"
        )

        return invoice
