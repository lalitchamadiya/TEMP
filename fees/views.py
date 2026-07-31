import json
import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from student.models import Student
from room.models import HostelBuilding, Room, Bed
from authentication.models import AuditLog, Role, UserProfile

from fees.models import (
    FeeCategory, FeeComponent, FeeStructure, FeeStructureComponent,
    FeeDiscountRule, FeeFineRule, Invoice, InvoiceItem, StudentInstallment,
    PaymentTransaction, Receipt, Refund, StudentLedger, PaymentGatewayLog
)
from fees.forms import FeeStructureForm, FeeComponentForm
from fees.services.invoice_generator import InvoiceGenerator
from fees.services.payment_processor import PaymentProcessor
from fees.services.ledger_service import LedgerService


def _is_admin(user):
    if user.is_superuser:
        return True
    try:
        role = user.profile.role
        return role.is_superadmin or role.name in ('Admin', 'Staff', 'Accountant', 'Warden')
    except Exception:
        return False


# ──────────────────────────────────────────────────────
# 1. FEE STRUCTURE MANAGEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def fee_structure_create_view(request):
    if not _is_admin(request.user):
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')

    # Seed default Fee Categories & Components if empty
    if not FeeCategory.objects.exists():
        cat_hostel, _ = FeeCategory.objects.get_or_create(name='Hostel Rent', code='RENT', is_refundable=False)
        cat_mess, _ = FeeCategory.objects.get_or_create(name='Mess & Food', code='MESS', is_refundable=False)
        cat_sec, _ = FeeCategory.objects.get_or_create(name='Security Deposit', code='SECURITY', is_refundable=True)
        cat_util, _ = FeeCategory.objects.get_or_create(name='Utilities & Maintenance', code='UTILITIES', is_refundable=False)

        FeeComponent.objects.get_or_create(name='Base Hostel Rent', category=cat_hostel, default_amount=2500.00)
        FeeComponent.objects.get_or_create(name='Security Deposit', category=cat_sec, default_amount=5000.00)
        FeeComponent.objects.get_or_create(name='Admission Fee', category=cat_hostel, default_amount=1000.00)
        FeeComponent.objects.get_or_create(name='Mess Charges', category=cat_mess, default_amount=3000.00)
        FeeComponent.objects.get_or_create(name='Electricity Charges', category=cat_util, default_amount=500.00)
        FeeComponent.objects.get_or_create(name='Water Charges', category=cat_util, default_amount=200.00)
        FeeComponent.objects.get_or_create(name='Laundry Charges', category=cat_util, default_amount=300.00)
        FeeComponent.objects.get_or_create(name='Maintenance Charges', category=cat_util, default_amount=250.00)
        FeeComponent.objects.get_or_create(name='Internet / WiFi Charges', category=cat_util, default_amount=200.00)
        FeeComponent.objects.get_or_create(name='Parking Charges', category=cat_util, default_amount=150.00)

    buildings = HostelBuilding.objects.filter(is_archived=False)
    categories = FeeCategory.objects.prefetch_related('components').filter(is_active=True)
    components = FeeComponent.objects.filter(status=True).select_related('category')

    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_validate() if hasattr(form, 'is_validate') else form.is_valid():
            fs = form.save(commit=False)
            fs.created_by = request.user

            # Check existing version for building + room_type + academic_year
            existing = FeeStructure.objects.filter(
                building=fs.building, room_type=fs.room_type, academic_year=fs.academic_year
            ).order_by('-version').first()

            if existing:
                fs.version = existing.version + 1
                # Mark previous as ARCHIVED if published
                existing.status = 'ARCHIVED'
                existing.save()

            action_type = request.POST.get('action_type', 'PUBLISHED')
            fs.status = 'PUBLISHED' if action_type == 'PUBLISH' else 'DRAFT'
            fs.save()

            # Process Fee Components
            total_base = Decimal('0.00')
            comp_ids = request.POST.getlist('component_ids[]')
            comp_amounts = request.POST.getlist('component_amounts[]')
            comp_gst_flags = request.POST.getlist('component_gst_flags[]')

            for idx, cid in enumerate(comp_ids):
                if cid:
                    comp_obj = FeeComponent.objects.filter(pk=cid).first()
                    if comp_obj:
                        amt = Decimal(comp_amounts[idx]) if idx < len(comp_amounts) and comp_amounts[idx] else Decimal('0.00')
                        is_gst = str(cid) in comp_gst_flags or 'true' in comp_gst_flags

                        FeeStructureComponent.objects.create(
                            fee_structure=fs,
                            fee_component=comp_obj,
                            amount=amt,
                            order=idx + 1,
                            is_gst_applicable=is_gst,
                        )
                        total_base += amt

            fs.total_base_fee = total_base
            gst_val = Decimal('0.00')
            if fs.include_gst:
                gst_val = total_base * (fs.gst_percent / Decimal('100.00'))
            fs.total_fee_with_gst = total_base + gst_val
            fs.save()

            # Process Discounts
            disc_names = request.POST.getlist('discount_names[]')
            disc_types = request.POST.getlist('discount_types[]')
            disc_calcs = request.POST.getlist('discount_calcs[]')
            disc_amounts = request.POST.getlist('discount_amounts[]')

            for i, dname in enumerate(disc_names):
                if dname and dname.strip():
                    amt = Decimal(disc_amounts[i]) if i < len(disc_amounts) and disc_amounts[i] else Decimal('0.00')
                    FeeDiscountRule.objects.create(
                        name=dname,
                        fee_structure=fs,
                        discount_type=disc_types[i] if i < len(disc_types) else 'SCHOLARSHIP',
                        calculation_type=disc_calcs[i] if i < len(disc_calcs) else 'FIXED',
                        amount=amt,
                    )

            # Process Fines
            fine_names = request.POST.getlist('fine_names[]')
            fine_types = request.POST.getlist('fine_types[]')
            fine_calcs = request.POST.getlist('fine_calcs[]')
            fine_amounts = request.POST.getlist('fine_amounts[]')

            for i, fname in enumerate(fine_names):
                if fname and fname.strip():
                    amt = Decimal(fine_amounts[i]) if i < len(fine_amounts) and fine_amounts[i] else Decimal('0.00')
                    FeeFineRule.objects.create(
                        name=fname,
                        fee_structure=fs,
                        fine_type=fine_types[i] if i < len(fine_types) else 'LATE_PAYMENT',
                        calculation_type=fine_calcs[i] if i < len(fine_calcs) else 'FIXED',
                        amount=amt,
                    )

            AuditLog.objects.create(
                actor=request.user,
                action='OTHER',
                details=f"Created Fee Structure: {fs.name} (v{fs.version}, Total: ₹{fs.total_fee_with_gst})"
            )

            messages.success(request, f"Fee Structure '{fs.name}' saved successfully!")
            return redirect('fees:fee_structure_list')
    else:
        form = FeeStructureForm()

    context = {
        'page_title': 'Create Fee Structure & Payment Configuration',
        'form': form,
        'buildings': buildings,
        'categories': categories,
        'components': components,
    }
    return render(request, 'fees/fee_structure_create.html', context)


@login_required(login_url='/authentication/login/')
def fee_structure_list_view(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    structures = FeeStructure.objects.select_related('building', 'created_by').prefetch_related('components').all()
    context = {
        'page_title': 'Fee Structures & Pricing Plans',
        'structures': structures,
    }
    return render(request, 'fees/fee_structure_list.html', context)


# ──────────────────────────────────────────────────────
# 2. STUDENT PAYMENT MODULE
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def student_payment_view(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    student_id = request.GET.get('student_id')
    student = None
    bed = None
    invoice = None
    ledger_entries = []
    installments = []
    summary = {
        'total_due': Decimal('0.00'),
        'paid_amount': Decimal('0.00'),
        'pending_amount': Decimal('0.00'),
        'fine_amount': Decimal('0.00'),
        'discount_amount': Decimal('0.00'),
        'security_deposit': Decimal('0.00'),
        'progress_pct': 0,
        'next_due_date': None,
    }

    if student_id:
        student = Student.objects.filter(pk=student_id).first()
        if student:
            bed = Bed.objects.filter(student=student).select_related('room', 'room__building').first()

            # Find active invoice or auto-generate if missing but bed allocated
            invoice = Invoice.objects.filter(student=student).order_by('-created_at').first()

            if not invoice and bed:
                # Find matching fee structure for building & room_type
                fs = FeeStructure.objects.filter(
                    building=bed.room.building,
                    room_type=bed.room.room_type,
                    status='PUBLISHED'
                ).order_by('-version').first()

                if not fs:
                    fs = FeeStructure.objects.filter(status='PUBLISHED').first()

                if fs:
                    invoice = InvoiceGenerator.generate_invoice_for_student(student, bed, fs)

            if invoice:
                installments = invoice.installments.all()
                summary['total_due'] = invoice.total_amount
                summary['paid_amount'] = invoice.paid_amount
                summary['pending_amount'] = invoice.pending_amount
                summary['fine_amount'] = invoice.fine_amount
                summary['discount_amount'] = invoice.discount_amount

                if invoice.total_amount > 0:
                    summary['progress_pct'] = round((invoice.paid_amount / invoice.total_amount) * 100, 1)

                next_inst = installments.filter(status__in=['UNPAID', 'PARTIAL']).first()
                if next_inst:
                    summary['next_due_date'] = next_inst.due_date

            ledger_entries = StudentLedger.objects.filter(student=student).order_by('-created_at')[:10]

    context = {
        'page_title': 'Student Payment & Fee Processing',
        'student': student,
        'bed': bed,
        'invoice': invoice,
        'installments': installments,
        'summary': summary,
        'ledger_entries': ledger_entries,
    }
    return render(request, 'fees/student_payment.html', context)


# ──────────────────────────────────────────────────────
# 3. TRANSACTION HISTORY & REFUNDS
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def transaction_history_view(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    qs = PaymentTransaction.objects.select_related('student', 'invoice', 'recorded_by', 'receipt').all()

    search = request.GET.get('q', '').strip()
    method = request.GET.get('method', '')
    status = request.GET.get('status', '')
    building_id = request.GET.get('building', '')

    if search:
        qs = qs.filter(
            Q(transaction_id__icontains=search) |
            Q(student__name__icontains=search) |
            Q(student__roll__icontains=search) |
            Q(invoice__invoice_number__icontains=search)
        )
    if method:
        qs = qs.filter(payment_method=method)
    if status:
        qs = qs.filter(status=status)
    if building_id:
        qs = qs.filter(invoice__bed__room__building_id=building_id)

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Receipt No', 'Transaction ID', 'Invoice No', 'Student', 'Method', 'Amount', 'Fine', 'Discount', 'Date', 'Status', 'Recorded By'])
        for t in qs:
            rec = t.receipt.receipt_number if hasattr(t, 'receipt') else 'N/A'
            writer.writerow([
                rec, t.transaction_id, t.invoice.invoice_number, t.student.name,
                t.get_payment_method_display(), t.amount_paid, t.fine_applied, t.discount_applied,
                t.payment_date.strftime('%Y-%m-%d %H:%M'), t.get_status_display(),
                t.recorded_by.username if t.recorded_by else 'System'
            ])
        return response

    buildings = HostelBuilding.objects.filter(is_archived=False)
    context = {
        'page_title': 'Payment Transaction History & Audit Ledger',
        'transactions': qs[:100],
        'buildings': buildings,
        'search': search,
        'selected_method': method,
        'selected_status': status,
        'selected_building': building_id,
    }
    return render(request, 'fees/transaction_history.html', context)


# ──────────────────────────────────────────────────────
# 4. STUDENT LEDGER STATEMENT
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def student_ledger_view(request, student_id):
    if not _is_admin(request.user):
        return redirect('dashboard')

    student = get_object_or_404(Student, pk=student_id)
    entries = StudentLedger.objects.filter(student=student).order_by('created_at', 'id')
    current_balance = LedgerService.get_student_balance(student)

    context = {
        'page_title': f"Financial Ledger Statement - {student.name}",
        'student': student,
        'entries': entries,
        'current_balance': current_balance,
    }
    return render(request, 'fees/student_ledger.html', context)


# ──────────────────────────────────────────────────────
# 5. FINANCIAL DASHBOARD & ANALYTICS
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def payment_dashboard_view(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    # 9 KPI Summary Metrics
    today_collection = PaymentTransaction.objects.filter(
        status='SUCCESSFUL', payment_date__date=today
    ).aggregate(s=Sum('amount_paid'))['s'] or Decimal('0.00')

    monthly_collection = PaymentTransaction.objects.filter(
        status='SUCCESSFUL', payment_date__date__gte=start_of_month
    ).aggregate(s=Sum('amount_paid'))['s'] or Decimal('0.00')

    pending_fees = Invoice.objects.filter(
        status__in=['ISSUED', 'PARTIAL', 'OVERDUE']
    ).aggregate(s=Sum('pending_amount'))['s'] or Decimal('0.00')

    total_due = Invoice.objects.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    late_payments = Invoice.objects.filter(status='OVERDUE').count()

    cash_collection = PaymentTransaction.objects.filter(
        status='SUCCESSFUL', payment_method='CASH'
    ).aggregate(s=Sum('amount_paid'))['s'] or Decimal('0.00')

    upi_collection = PaymentTransaction.objects.filter(
        status='SUCCESSFUL', payment_method='UPI'
    ).aggregate(s=Sum('amount_paid'))['s'] or Decimal('0.00')

    bank_collection = PaymentTransaction.objects.filter(
        status='SUCCESSFUL', payment_method__in=['BANK', 'CHEQUE', 'CARD']
    ).aggregate(s=Sum('amount_paid'))['s'] or Decimal('0.00')

    refund_amount = Refund.objects.filter(
        status='APPROVED'
    ).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

    total_transactions = PaymentTransaction.objects.count()

    # Recent Transactions
    recent_transactions = PaymentTransaction.objects.select_related('student', 'invoice', 'receipt').order_by('-payment_date')[:8]

    context = {
        'page_title': 'Fee Collection & Financial ERP Analytics',
        'today_collection': today_collection,
        'monthly_collection': monthly_collection,
        'pending_fees': pending_fees,
        'total_due': total_due,
        'late_payments': late_payments,
        'cash_collection': cash_collection,
        'upi_collection': upi_collection,
        'bank_collection': bank_collection,
        'refund_amount': refund_amount,
        'total_transactions': total_transactions,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'fees/payment_dashboard.html', context)


# ──────────────────────────────────────────────────────
# 6. RECEIPT & QR VERIFICATION
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def receipt_detail_view(request, pk):
    receipt = get_object_or_404(Receipt.objects.select_related('transaction', 'invoice', 'student', 'created_by'), pk=pk)
    context = {
        'receipt': receipt,
        'page_title': f"Receipt #{receipt.receipt_number}",
    }
    return render(request, 'fees/receipt_detail.html', context)


def receipt_verify_view(request, qr_hash):
    """Public verification page for scanned QR codes"""
    receipt = Receipt.objects.filter(qr_code_hash=qr_hash).select_related('transaction', 'invoice', 'student').first()
    context = {
        'receipt': receipt,
        'is_valid': receipt is not None,
        'page_title': 'Receipt QR Verification',
    }
    return render(request, 'fees/receipt_verify.html', context)


# ──────────────────────────────────────────────────────
# 7. AJAX ENDPOINTS
# ──────────────────────────────────────────────────────
@login_required(login_url='/authentication/login/')
def student_search_ajax(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'students': []})

    qs = Student.objects.filter(
        Q(name__icontains=query) |
        Q(roll__icontains=query) |
        Q(phone_number__icontains=query) |
        Q(email__icontains=query)
    )[:10]

    results = []
    for s in qs:
        bed = Bed.objects.filter(student=s).select_related('room', 'room__building').first()
        room_desc = f"{bed.room.building.name} - Room {bed.room.room_number}" if bed else "No Bed Allocated"
        results.append({
            'id': s.student_id,
            'name': s.name,
            'roll': s.roll or f"STD-{s.student_id}",
            'phone': s.phone_number,
            'photo': s.photo.url if s.photo else '',
            'room_desc': room_desc,
        })
    return JsonResponse({'students': results})


@login_required(login_url='/authentication/login/')
def room_type_details_ajax(request):
    building_id = request.GET.get('building_id')
    room_type = request.GET.get('room_type', '2_BED')

    rooms = Room.objects.filter(building_id=building_id, room_type=room_type)
    avg_rent = rooms.aggregate(avg=Sum('monthly_rent'))['avg'] or 2500.00
    if rooms.count() > 0:
        avg_rent = avg_rent / rooms.count()

    total_beds = Bed.objects.filter(room__building_id=building_id, room__room_type=room_type).count()
    vacant_beds = Bed.objects.filter(room__building_id=building_id, room__room_type=room_type, student__isnull=True).count()

    return JsonResponse({
        'base_rent': float(avg_rent),
        'total_beds': total_beds,
        'vacant_beds': vacant_beds,
        'total_rooms': rooms.count(),
    })


@login_required(login_url='/authentication/login/')
def process_payment_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    try:
        invoice_id = request.POST.get('invoice_id')
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method', 'UPI')
        fine_applied = request.POST.get('fine_applied', 0)
        discount_applied = request.POST.get('discount_applied', 0)
        remarks = request.POST.get('remarks', '')

        bank_name = request.POST.get('bank_name')
        cheque_no = request.POST.get('cheque_no')
        upi_ref = request.POST.get('upi_ref')
        receipt_file = request.FILES.get('receipt_file')

        invoice = get_object_or_404(Invoice, pk=invoice_id)

        txn, receipt = PaymentProcessor.process_payment(
            invoice=invoice,
            amount_paid=amount_paid,
            payment_method=payment_method,
            recorded_by=request.user,
            fine_applied=fine_applied,
            discount_applied=discount_applied,
            remarks=remarks,
            bank_name=bank_name,
            cheque_no=cheque_no,
            upi_ref=upi_ref,
            receipt_file=receipt_file,
        )

        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully!',
            'receipt_id': receipt.pk,
            'receipt_number': receipt.receipt_number,
            'transaction_id': txn.transaction_id,
            'paid_amount': float(txn.amount_paid),
            'remaining_balance': float(txn.remaining_balance),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='/authentication/login/')
def refund_transaction_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    try:
        txn_id = request.POST.get('transaction_id')
        reason = request.POST.get('reason', 'Refund requested')
        refund = PaymentProcessor.refund_transaction(txn_id, reason, approved_by=request.user)

        return JsonResponse({
            'success': True,
            'message': f"Refund {refund.refund_number} approved successfully!",
            'refund_number': refund.refund_number,
            'amount': float(refund.amount),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
