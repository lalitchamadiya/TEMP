from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum
from room.models import Room, Bed
from student.models import Student
from .models import FeeStructure, Payment
from django.urls import reverse
from django.utils import timezone
import uuid
import logging
import random
from decimal import Decimal, InvalidOperation  
from django.contrib.auth.decorators import login_required
from authentication.decorators import role_required, permission_required
from django.core.exceptions import PermissionDenied

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def paybill_base(request):
    total_remaining = Bed.objects.aggregate(total=Sum('remaining_amount'))['total'] or 0
    total_count = Bed.objects.filter(student__isnull=False).count()
    beds = Bed.objects.select_related('room', 'student').all()
    total_pending_amount = sum(bed.remaining_amount for bed in beds if bed.student)
    return render(request, 'paybill/paybill_base.html', {
        'total_remaining': total_remaining, 
        'total_count': total_count,  
        'total_pending_amount': total_pending_amount
    })

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'add')
def collect_fees(request):
    return render(request, 'paybill/collect_fees.html')

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'add')
def pay_salary(request):
    return render(request, 'paybill/pay_salary.html')

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def pending_fees(request):
    students = Student.objects.all()
    rooms = Room.objects.all()
    beds = Bed.objects.select_related('room', 'student').all()
    return render(request, 'paybill/pending_fees.html', {'students': students, 'rooms': rooms, 'beds': beds})

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def student_details(request):
    students = Student.objects.all()
    return render(request, 'paybill/student_details.html', {'students': students})

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def fee_structure(request):
    from django.db import IntegrityError
    from .models import InstallmentConfig
    
    config = InstallmentConfig.get_config()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_installments':
            part1_due = request.POST.get('part1_due_date')
            part1_penalty = request.POST.get('part1_late_fee_per_day')
            part2_due = request.POST.get('part2_due_date')
            part2_penalty = request.POST.get('part2_late_fee_per_day')

            try:
                if part1_due:
                    config.part1_due_date = part1_due
                else:
                    config.part1_due_date = None
                    
                if part1_penalty:
                    config.part1_late_fee_per_day = Decimal(part1_penalty)
                    
                if part2_due:
                    config.part2_due_date = part2_due
                else:
                    config.part2_due_date = None
                    
                if part2_penalty:
                    config.part2_late_fee_per_day = Decimal(part2_penalty)

                config.save()
                messages.success(request, 'Installment configuration updated successfully.')
                return redirect('fee_structure')
            except Exception as e:
                messages.error(request, f"Error updating installment configuration: {str(e)}")
        else:
            amount = request.POST.get('amount')
            fee_type = request.POST.get('fee_type')
            if amount and fee_type:
                try:
                    amount_decimal = Decimal(amount)
                    if amount_decimal <= 0:
                        messages.error(request, 'Fee amount must be greater than zero.')
                    else:
                        FeeStructure.objects.create(fee_type=fee_type, amount=amount_decimal)
                        messages.success(request, 'Fee structure created successfully.')
                        return redirect('fee_structure')
                except InvalidOperation:
                    messages.error(request, 'Invalid amount format.')
                except IntegrityError:
                    messages.error(request, f"Fee type '{fee_type}' already exists. Delete existing items before recreating them.")
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
                    
    fee_structures = FeeStructure.objects.all()
    return render(request, 'paybill/fee_structure.html', {
        'fee_structures': fee_structures,
        'installment_config': config
    })

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'delete')
def delete_fee_item(request, fee_id):
    if request.method == 'POST':
        fee_structure = get_object_or_404(FeeStructure, id=fee_id)
        fee_structure.delete()
        messages.success(request, 'Fee structure item deleted successfully.')
    else:
        messages.error(request, 'Invalid delete request.')
    return redirect('fee_structure')

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def transaction_record(request):
    # Student isolation
    query = Q()
    if hasattr(request.user, 'profile') and request.user.profile.role.name == 'Student':
        query = Q(student__user=request.user)
    
    transactions = Payment.objects.filter(query).order_by('-created_at')
    
    # Calculate Metrics
    successful_tx = transactions.filter(Q(transaction_status='SUCCESSFUL') | Q(transaction_status='Completed'))
    total_revenue = successful_tx.aggregate(total=Sum('amount'))['total'] or 0
    success_count = successful_tx.count()
    pending_count = transactions.filter(transaction_status='PENDING').count()
    failure_count = transactions.filter(transaction_status='FAILED').count()
    
    total_count = transactions.count()
    failure_rate = round((failure_count / total_count * 100), 1) if total_count > 0 else 0

    context = {
        'transactions': transactions,
        'total_revenue': total_revenue,
        'success_count': success_count,
        'pending_count': pending_count,
        'failure_rate': failure_rate,
    }
    return render(request, 'paybill/transaction_record.html', context)

logger = logging.getLogger(__name__)

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def check_enrollment(request):
    student_details = None
    room_details = None
    bed_details = None
    error_message = None

    if request.method == 'POST':
        enrollment_number = request.POST.get('enrollment_number')
        try:
            student_details = Student.objects.get(roll=enrollment_number)
            bed_details = Bed.objects.get(student=student_details)
            room_details = bed_details.room
        except Student.DoesNotExist:
            error_message = "Student Record not found"
        except Bed.DoesNotExist:
            error_message = "No bed assigned to this student"
        except Exception as e:
            error_message = str(e)

    return render(request, 'paybill/collect_fees.html', {
        'student_details': student_details,
        'room_details': room_details,
        'bed_details': bed_details,
        'error_message': error_message,
    })

def generate_unique_transaction_id():
    while True:
        transaction_id = str(uuid.uuid4())[:10]
        if not Payment.objects.filter(transaction_id=transaction_id).exists():
            return transaction_id

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'add')
def process_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_type = request.POST.get('payment_type')
        enrollment_number = request.POST.get('enrollment_number')
        user_name = request.POST.get('user_name')
        contact_no = request.POST.get('contact_no')
        upi_id = request.POST.get('upi_id', None)

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except (ValueError, InvalidOperation):
            messages.error(request, 'Invalid amount. Please enter a valid number greater than zero.')
            return redirect('collect_fees')

        try:
            student = Student.objects.get(roll=enrollment_number)
            bed = Bed.objects.get(student=student)
        except (Student.DoesNotExist, Bed.DoesNotExist):
            messages.error(request, 'Student or Bed record not found.')
            return redirect('collect_fees')

        transaction_id = generate_unique_transaction_id()

        try:
            Payment.objects.create(
                student=student,
                transaction_id=transaction_id,
                enrollment_number=enrollment_number,
                user_name=user_name,
                contact_no=contact_no,
                amount=amount,
                payment_type=payment_type,
                created_at=timezone.now(),
                upi_id=upi_id if payment_type == 'upi' else None,
                transaction_status='SUCCESSFUL'
            )
            messages.success(request, 'Payment processed successfully.')
            return redirect('transaction_record')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
            return redirect('collect_fees')
    return redirect('collect_fees')

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'delete')
def delete_transaction(request, transaction_id):
    if request.method == 'POST':
        payment = get_object_or_404(Payment, transaction_id=transaction_id)
        payment.delete()
        messages.success(request, 'Transaction record deleted successfully.')
    return redirect('transaction_record')
@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def admin_analytics(request):
    """
    High-density Administrative Dashboard for Fee Collections
    """
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Core Metrics
    total_successful = Payment.objects.filter(transaction_status='SUCCESSFUL')
    total_revenue = total_successful.aggregate(total=Sum('amount'))['total'] or 0
    monthly_revenue = total_successful.filter(created_at__gte=start_of_month).aggregate(total=Sum('amount'))['total'] or 0
    daily_revenue = total_successful.filter(created_at__gte=start_of_day).aggregate(total=Sum('amount'))['total'] or 0
    pending_count = Payment.objects.filter(transaction_status='PENDING').count()

    # Method & Gateway Distribution
    method_data = total_successful.values('payment_type').annotate(total=Sum('amount')).order_by('-total')
    gateway_data = total_successful.values('gateway_name').annotate(total=Sum('amount')).order_by('-total')

    # Monthly Trend (Last 6 months)
    from django.db.models.functions import TruncMonth
    monthly_trend = total_successful.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('amount')).order_by('month')

    context = {
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'daily_revenue': daily_revenue,
        'pending_count': pending_count,
        'method_data': list(method_data),
        'gateway_data': list(gateway_data),
        'monthly_trend': list(monthly_trend),
        'recent_transactions': total_successful.order_by('-created_at')[:10]
    }
    return render(request, 'paybill/admin_analytics.html', context)

import csv
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def export_transactions_csv(request):
    """Exports transaction records to CSV format."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="HMS_Transactions_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'Date', 'Amount', 'Student Name', 'Roll Number', 'Type', 'Status', 'Gateway ID'])
    
    transactions = Payment.objects.all().order_by('-created_at')
    for tx in transactions:
        writer.writerow([
            tx.transaction_id,
            tx.created_at.strftime("%Y-%m-%d %H:%M"),
            tx.amount,
            tx.user_name,
            tx.enrollment_number,
            tx.payment_type,
            tx.transaction_status,
            tx.gateway_payment_id or "N/A"
        ])
    
    return response

@login_required(login_url='/authentication/login')
@permission_required('paybill', 'view')
def export_transactions_excel(request):
    """Exports transaction records to Excel (.xlsx) format using openpyxl."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"
    
    # Headers
    headers = ['Transaction ID', 'Date', 'Amount', 'Student Name', 'Roll Number', 'Type', 'Status', 'Gateway ID']
    ws.append(headers)
    
    # Style Headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    transactions = Payment.objects.all().order_by('-created_at')
    for tx in transactions:
        ws.append([
            tx.transaction_id,
            tx.created_at.replace(tzinfo=None), # Excel doesn't like timezone-aware datetimes
            tx.amount,
            tx.user_name,
            tx.enrollment_number,
            tx.payment_type,
            tx.transaction_status,
            tx.gateway_payment_id or "N/A"
        ])
    
    # Column width adjustment
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="HMS_Transactions_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response
