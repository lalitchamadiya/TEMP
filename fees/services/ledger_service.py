from decimal import Decimal
from django.db import transaction, models
from fees.models import StudentLedger


class LedgerService:
    @staticmethod
    @transaction.atomic
    def record_entry(student, transaction_type, reference_no, debit=0, credit=0, description=""):
        """
        Record an immutable double-entry ledger record for a student.
        Debit (+) increases student's balance due (e.g. Invoice, Fine).
        Credit (-) decreases student's balance due (e.g. Payment, Discount).
        """
        debit = Decimal(str(debit or 0))
        credit = Decimal(str(credit or 0))

        # Get latest running balance for student
        latest_entry = StudentLedger.objects.filter(student=student).order_by('-created_at', '-id').first()
        prev_balance = latest_entry.running_balance if latest_entry else Decimal('0.00')

        running_balance = prev_balance + debit - credit

        entry = StudentLedger.objects.create(
            student=student,
            transaction_type=transaction_type,
            reference_no=reference_no,
            debit=debit,
            credit=credit,
            running_balance=running_balance,
            description=description,
        )
        return entry

    @staticmethod
    def get_student_balance(student):
        latest = StudentLedger.objects.filter(student=student).order_by('-created_at', '-id').first()
        return latest.running_balance if latest else Decimal('0.00')
