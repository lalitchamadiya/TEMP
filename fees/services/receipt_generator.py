from django.utils import timezone
from fees.models import Receipt, Invoice, PaymentTransaction


class ReceiptGenerator:
    @staticmethod
    def generate_receipt_number():
        """
        Generates professional format: NBNH-YYYY-MM-XXXXXX
        e.g. NBNH-2026-07-000001
        """
        now = timezone.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        prefix = f"NBNH-{year}-{month}-"

        # Find max receipt number for this year-month
        latest = Receipt.objects.filter(receipt_number__startswith=prefix).order_by('-id').first()
        if latest:
            try:
                last_seq = int(latest.receipt_number.split('-')[-1])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:06d}"

    @staticmethod
    def generate_invoice_number():
        """
        Generates professional format: HMS-INV-YYYY-XXXXXX
        e.g. HMS-INV-2026-000001
        """
        now = timezone.now()
        year = now.strftime('%Y')
        prefix = f"HMS-INV-{year}-"

        latest = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-id').first()
        if latest:
            try:
                last_seq = int(latest.invoice_number.split('-')[-1])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:06d}"
