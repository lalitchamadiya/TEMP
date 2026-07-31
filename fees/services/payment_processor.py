from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from fees.models import (
    PaymentTransaction, Receipt, Invoice, StudentInstallment, Refund
)
from fees.services.receipt_generator import ReceiptGenerator
from fees.services.ledger_service import LedgerService
from authentication.models import AuditLog


class PaymentProcessor:
    @staticmethod
    @transaction.atomic
    def process_payment(invoice, amount_paid, payment_method, recorded_by=None,
                        fine_applied=0, discount_applied=0, remarks=None,
                        bank_name=None, cheque_no=None, upi_ref=None, receipt_file=None):
        """
        Processes payment, updates outstanding invoice balance, allocates across installments,
        creates transaction & receipt, posts to ledger, and logs audit trail.
        """
        amount_paid = Decimal(str(amount_paid or 0))
        fine_applied = Decimal(str(fine_applied or 0))
        discount_applied = Decimal(str(discount_applied or 0))

        if amount_paid <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        # Update invoice totals for fine / discount if applied
        if fine_applied > 0:
            invoice.fine_amount += fine_applied
            invoice.total_amount += fine_applied
            invoice.pending_amount += fine_applied
            # Record fine in ledger
            LedgerService.record_entry(
                student=invoice.student,
                transaction_type='FINE',
                reference_no=invoice.invoice_number,
                debit=fine_applied,
                credit=0,
                description=f"Fine applied to Invoice #{invoice.invoice_number}"
            )

        if discount_applied > 0:
            invoice.discount_amount += discount_applied
            invoice.total_amount = max(Decimal('0.00'), invoice.total_amount - discount_applied)
            invoice.pending_amount = max(Decimal('0.00'), invoice.pending_amount - discount_applied)
            # Record discount in ledger
            LedgerService.record_entry(
                student=invoice.student,
                transaction_type='DISCOUNT',
                reference_no=invoice.invoice_number,
                debit=0,
                credit=discount_applied,
                description=f"Discount applied to Invoice #{invoice.invoice_number}"
            )

        # Allocate payment amount
        effective_payment = amount_paid
        invoice.paid_amount += effective_payment
        invoice.pending_amount = max(Decimal('0.00'), invoice.total_amount - invoice.paid_amount)

        if invoice.pending_amount == 0:
            invoice.status = 'PAID'
        elif invoice.paid_amount > 0:
            invoice.status = 'PARTIAL'
        invoice.save()

        # Allocate across installments
        remaining_alloc = effective_payment
        for inst in invoice.installments.all().order_by('installment_no'):
            if remaining_alloc <= 0:
                break
            needed = inst.amount - inst.paid_amount
            if needed > 0:
                if remaining_alloc >= needed:
                    inst.paid_amount += needed
                    inst.status = 'PAID'
                    remaining_alloc -= needed
                else:
                    inst.paid_amount += remaining_alloc
                    inst.status = 'PARTIAL'
                    remaining_alloc = Decimal('0.00')
                inst.save()

        # Generate Transaction ID
        now_str = timezone.now().strftime('%Y%m%d%H%M%S')
        txn_id = f"NBNH-TXN-{now_str}-{invoice.student.student_id}"

        payment_txn = PaymentTransaction.objects.create(
            transaction_id=txn_id,
            invoice=invoice,
            student=invoice.student,
            amount_paid=amount_paid,
            fine_applied=fine_applied,
            discount_applied=discount_applied,
            remaining_balance=invoice.pending_amount,
            payment_method=payment_method,
            bank_name=bank_name,
            cheque_no=cheque_no,
            upi_ref=upi_ref,
            recorded_by=recorded_by,
            receipt_file=receipt_file,
            remarks=remarks,
            status='SUCCESSFUL',
        )

        # Generate Receipt
        rec_num = ReceiptGenerator.generate_receipt_number()
        receipt = Receipt.objects.create(
            receipt_number=rec_num,
            transaction=payment_txn,
            invoice=invoice,
            student=invoice.student,
            created_by=recorded_by,
        )

        # Record Ledger Entry
        LedgerService.record_entry(
            student=invoice.student,
            transaction_type='PAYMENT',
            reference_no=rec_num,
            debit=0,
            credit=amount_paid,
            description=f"Payment received ({payment_method}) - Receipt #{rec_num}"
        )

        # Audit Log
        AuditLog.objects.create(
            actor=recorded_by,
            action='OTHER',
            target_user=invoice.student.user if invoice.student.user else None,
            details=f"Processed payment ₹{amount_paid} ({payment_method}) for Student {invoice.student.name}. Receipt: {rec_num}"
        )

        return payment_txn, receipt

    @staticmethod
    @transaction.atomic
    def refund_transaction(transaction_id, reason, approved_by=None):
        """
        Refunds a payment transaction, updates invoice balance, creates Refund record,
        posts to Student Ledger, and logs audit trail.
        """
        txn = PaymentTransaction.objects.select_for_update().get(pk=transaction_id)
        if txn.status == 'REFUNDED':
            raise ValueError("Transaction has already been refunded.")

        invoice = txn.invoice
        amount = txn.amount_paid

        txn.status = 'REFUNDED'
        txn.save()

        invoice.paid_amount = max(Decimal('0.00'), invoice.paid_amount - amount)
        invoice.pending_amount += amount

        if invoice.paid_amount == 0:
            invoice.status = 'ISSUED'
        else:
            invoice.status = 'PARTIAL'
        invoice.save()

        now_str = timezone.now().strftime('%Y%m')
        ref_num = f"NBNH-REF-{now_str}-{txn.id:06d}"

        refund = Refund.objects.create(
            refund_number=ref_num,
            original_transaction=txn,
            invoice=invoice,
            student=invoice.student,
            amount=amount,
            reason=reason,
            status='APPROVED',
            approved_by=approved_by,
        )

        # Record Ledger Entry
        LedgerService.record_entry(
            student=invoice.student,
            transaction_type='REFUND',
            reference_no=ref_num,
            debit=amount,
            credit=0,
            description=f"Refund issued for Txn #{txn.transaction_id} - Ref #{ref_num}"
        )

        # Audit Log
        AuditLog.objects.create(
            actor=approved_by,
            action='OTHER',
            target_user=invoice.student.user if invoice.student.user else None,
            details=f"Refunded ₹{amount} for Txn {txn.transaction_id}. Refund Ref: {ref_num}. Reason: {reason}"
        )

        return refund
