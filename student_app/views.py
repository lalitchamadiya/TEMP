from django.contrib import messages
from django.shortcuts import get_object_or_404, render , redirect
from leave.models import HostelLeave, GatePass
from student.forms import StudentForm, StudentSelfUpdateForm
from student.models import Student 
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from paybill.models import Payment, FeeStructure, GatewayConfig
from paybill.services import PaymentGatewayFactory, PaymentGatewayError
from django.utils.timezone import now
import uuid
from django.db import models
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
try:
    from xhtml2pdf import pisa
except ImportError:  # pragma: no cover
    pisa = None



@login_required(login_url='/authentication/login')
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Bed/Room info
    bed = student.bed_set.first()
    
    # Fee Info
    total_fee = FeeStructure.objects.aggregate(total=Sum('amount'))['total'] or 0
    paid_fee = Payment.objects.filter(student=student).aggregate(total_paid=Sum('amount'))['total_paid'] or 0
    pending_fee = total_fee - paid_fee
    payment_percentage = (paid_fee / total_fee * 100) if total_fee > 0 else 0
    
    # Leave Info
    recent_leaves = HostelLeave.objects.filter(student=student).order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'bed': bed,
        'total_fee': total_fee,
        'paid_fee': paid_fee,
        'pending_fee': pending_fee,
        'payment_percentage': payment_percentage,
        'recent_leaves': recent_leaves,
    }
    return render(request, 'student_app/student_dashboard.html', context)


@login_required(login_url='/authentication/login')
def my_gate_passes(request):
    student = get_object_or_404(Student, user=request.user)
    gate_passes = GatePass.objects.filter(leave_request__student=student).order_by('-created_at')
    return render(request, 'student_app/my_gate_passes.html', {'gate_passes': gate_passes})


@login_required(login_url='/authentication/login')
def student_profile(request):
    student = get_object_or_404(Student, user=request.user)
    return render(request, 'student_app/student_profile.html', {'student': student})


@login_required(login_url='/authentication/login')
def student_profile_update(request):
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        form = StudentSelfUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully')
            return redirect('student_app:student_profile')
        else:
            # If the form is not valid, add an error message
            messages.error(request, 'Please correct the errors below.')
            if not form.is_valid():
                print(form.errors)
    else:
        form = StudentSelfUpdateForm(instance=student)
        
    return render(request, 'student_app/student_profile_update.html', {'form': form,'student': student})


@login_required(login_url='/authentication/login')
def food_schedule(request):
    food_schedule = {
        'Monday': {
            'breakfast': 'Thepla',
            'breakfast_image': 'https://media.istockphoto.com/id/1807607799/photo/thepla-or-methi-thepla-gujarati-dish.webp?a=1&b=1&s=612x612&w=0&k=20&c=XD1obx3pjZGOEhaz-bUMl0JQzPA5HmEdLqvqKp-7apA=',
            'lunch': 'Gujarati Thali',
            'lunch_image': 'https://media.istockphoto.com/id/469160387/photo/gujarati-thali.webp?a=1&b=1&s=612x612&w=0&k=20&c=wX5kx52ZHpYsmGAasLdOBSkE3MpKVOeTiFcmkb5wgRI=',
            'dinner': 'Undhiyu',
            'dinner_image': 'https://media.istockphoto.com/id/1177420020/photo/undhiyu-is-a-gujarati-mixed-vegetable-dish-specialty-of-surat-india-served-in-a-bowl-with-or.webp?a=1&b=1&s=612x612&w=0&k=20&c=p3vdeTPkJARqNfrfrmOzcCU-OWkARcnUZbnyHYuo6vc=',
        },
        'Tuesday': {
            'breakfast': 'Dhokla',
            'breakfast_image': 'https://media.istockphoto.com/id/2154971502/photo/famous-gujrati-snack-dhokla-made-with-gram-flour-and-sugar-syrup-decorated-with-mint-and.webp?a=1&b=1&s=612x612&w=0&k=20&c=MacEDJlATPi0-ztKaDwBRJxq4k9KPKI6MhZwEoZdQeg=',
            'lunch': 'Kadhi and Khichdi',
            'lunch_image': 'https://media.istockphoto.com/id/1255780592/photo/dal-khichadi-and-kadhi-with-papad-and-raw-mango-pickle.webp?a=1&b=1&s=612x612&w=0&k=20&c=tlOmaex2c7oT0eB-XllGD88T-MXaAXWR4l7OSQhks-w=',
            'dinner': 'Handvo',
            'dinner_image': 'https://media.istockphoto.com/id/2154972036/photo/gujrati-food-handvo-decorated-with-mint-chutney-curry-leaves-lemons-and-tomato-sauce.webp?a=1&b=1&s=612x612&w=0&k=20&c=7tbcEfR-Cexekj3YhRkLCkg2_PZwvwWZYblEbk2h6pU=',
        },
        'Wednesday': {
            'breakfast': 'Fafda Jalebi',
            'breakfast_image': 'https://media.istockphoto.com/id/1413554835/photo/popular-indian-sweet-jalebi-and-fafda-served-with-sambhara-gujarati-snack-is-mostly-eaten.webp?a=1&b=1&s=612x612&w=0&k=20&c=ZrJsrIpUM7uvoXDu4oTolagi2xU7mZVcAdmrMSIecjw=',
            'lunch': 'Bharela Ringan (Stuffed Eggplant)',
            'lunch_image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQD5CEgKCjP_71K-lKyhtCzBF0isoOFeVQdCg&s',
            'dinner': 'Sev Tameta Nu Shaak',
            'dinner_image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAqqFS6rucXCp4dvGL_eXyFSuQkSp3Q9wGPQ&s',
        },
        'Thursday': {
            'breakfast': 'Khaman',
            'breakfast_image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/SPECIAL_SURATI_KHAMAN.jpg/250px-SPECIAL_SURATI_KHAMAN.jpg',
            'lunch': 'Dal Dhokli',
            'lunch_image': 'https://www.jcookingodyssey.com/wp-content/uploads/2025/02/gujarati-dal-dhokli.jpg',
            'dinner': 'Muthiya',
            'dinner_image': 'https://herbivorecucina.com/wp-content/uploads/2023/05/Kale-Muthiya-1.jpg',
        },
        'Friday': {
            'breakfast': 'Gota',
            'breakfast_image': 'https://i0.wp.com/binjalsvegkitchen.com/wp-content/uploads/2016/06/Methi-Na-Gota-H1.jpg?w=600&ssl=1',
            'lunch': 'Gujarati Shaak and Rotli',
            'lunch_image': 'https://static.wixstatic.com/media/5a630d_083f4a870ed749a9aaae18389a5aec18~mv2.jpg/v1/fill/w_740,h_1036,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/5a630d_083f4a870ed749a9aaae18389a5aec18~mv2.jpg',
            'dinner': 'Khichu',
            'dinner_image': 'https://www.theroute2roots.com/wp-content/uploads/2020/05/Khichu-12-of-4-1.jpeg',
        },
        'Saturday': {
            'breakfast': 'Puran Poli',
            'breakfast_image': 'https://shwetainthekitchen.com/wp-content/uploads/2020/03/IMG_7944-scaled.jpg',
            'lunch': 'Patra',
            'lunch_image': 'https://cookilicious.com/wp-content/uploads/2021/08/pathrode-patra-colocasia-pinwheels-4.jpg',
            'dinner': 'Dabeli',
            'dinner_image': 'https://i0.wp.com/binjalsvegkitchen.com/wp-content/uploads/2017/10/Kutchi-Dabeli-H1.jpg?w=600&ssl=1',
        },
        'Sunday': {
            'breakfast': 'Bhakhri and Chai',
            'breakfast_image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR01FZ4Zp0BOUrGz_pSQczh4yKLXNAJ2_tjtg&s',
            'lunch': 'Surti Locho',
            'lunch_image': 'https://www.cookingcarnival.com/wp-content/uploads/2020/06/Surti-locho-recipe-2.jpg',
            'dinner': 'Khaman Dhokla',
            'dinner_image': 'https://thespicemess.com/wp-content/uploads/2022/04/Khaman-Dhokla-57-1.jpg',
        },
    }
    return render(request, 'student_app/food_schedule.html', {'food_schedule': food_schedule})


@login_required(login_url='/authentication/login')
def student_leave_request(request):
    student_details = get_object_or_404(Student, email=request.user.email)
    latest_leave = HostelLeave.objects.filter(student=student_details).order_by('-created_at').first()

    if request.method == 'POST':
        reason = request.POST.get('reason')
        leave_date = request.POST.get('leave_date')

        leave_date = parse_date(leave_date)
        if not leave_date:
            messages.error(request, 'Invalid leave date.')
            return render(request, 'student_app/student_leave_request.html', {'student_details': student_details, 'latest_leave': latest_leave})

        try:
            # Check if the latest leave request is not marked as "entered"
            if latest_leave and latest_leave.status != 'entered':
                messages.error(request, 'You cannot submit a new leave request until you are not entered in hostel.')
                return redirect('student_app:student_leave_request')

            hostelleave = HostelLeave(
                student=student_details,
                leave_date=leave_date,
                return_date=request.POST.get('return_date'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                reason=reason,
                destination=request.POST.get('destination'),
                transport_mode=request.POST.get('transport_mode'),
                remarks=request.POST.get('remarks')
            )
            hostelleave.save()
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('student_app:student_leave_details')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return render(
        request,
        'student_app/student_leave_request.html',
        {
            'student_details': student_details,
            'latest_leave': latest_leave,
            'today_date': now().date().isoformat(),
        },
    )


@login_required(login_url='/authentication/login')
def student_leave_details(request):
    if request.user.is_authenticated:
        try:
            student = get_object_or_404(Student, email=request.user.email)
            leave_requests = HostelLeave.objects.filter(student=student).order_by('-created_at')
        except Student.DoesNotExist:
            leave_requests = []
    else:
        leave_requests = []

    return render(request, 'student_app/student_leave_details.html', {'leave_requests': leave_requests})

@login_required(login_url='/authentication/login')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(old_password):
            messages.error(request, 'Your current password is incorrect.')
            return redirect('student_app:change_password')

        if new_password1 != new_password2:
            messages.error(request, 'The new passwords do not match.')
            return redirect('student_app:change_password')

        if len(new_password1) < 8:
            messages.error(request, 'The new password must be at least 8 characters long.')
            return redirect('student_app:change_password')

        # Change the password
        request.user.set_password(new_password1)
        request.user.save()

        # Keep the user logged in after changing the password
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Your password has been successfully changed.')
        return redirect('student_app:student_profile')

    return render(request, 'student_app/student_profile_password_change.html')


@login_required(login_url='/authentication/login')
def student_pay_fee(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Calculate current fee detail options recursively
    from paybill.models import InstallmentConfig, FeeStructure
    from datetime import date
    from decimal import Decimal
    
    bed = student.bed_set.first()
    yearly_fee = bed.total_amount if bed else 0
    if yearly_fee == 0:
        yearly_fee = FeeStructure.objects.aggregate(total=models.Sum('amount'))['total'] or 0

    installment_config = InstallmentConfig.get_config()
    today = date.today()
    
    part1_base = Decimal(str(yearly_fee)) / 2
    part2_base = Decimal(str(yearly_fee)) - part1_base
    
    successful_payments = Payment.objects.filter(student=student, transaction_status='SUCCESSFUL')
    total_paid = 0
    for p in successful_payments:
        if p.fee_breakdown and 'base_amount' in p.fee_breakdown:
            try:
                total_paid += Decimal(str(p.fee_breakdown['base_amount']))
            except Exception:
                total_paid += p.amount
        else:
            total_paid += p.amount

    # Part 1
    part1_paid = min(total_paid, part1_base)
    part1_remaining = part1_base - part1_paid
    part1_penalty = Decimal(0)
    if part1_remaining > 0:
        if installment_config.part1_due_date and today > installment_config.part1_due_date:
            days_late = (today - installment_config.part1_due_date).days
            part1_penalty = Decimal(days_late) * Decimal(str(installment_config.part1_late_fee_per_day or 0))

    # Part 2
    part2_paid = min(max(total_paid - part1_base, 0), part2_base)
    part2_remaining = part2_base - part2_paid
    part2_penalty = Decimal(0)
    if part2_remaining > 0:
        if installment_config.part2_due_date and today > installment_config.part2_due_date:
            days_late = (today - installment_config.part2_due_date).days
            part2_penalty = Decimal(days_late) * Decimal(str(installment_config.part2_late_fee_per_day or 0))

    part1_total = part1_remaining + part1_penalty
    part2_total = part2_remaining + part2_penalty
    full_base = part1_remaining + part2_remaining
    full_penalty = part1_penalty + part2_penalty
    full_total = full_base + full_penalty

    if request.method == 'POST':
        payment_choice = request.POST.get('payment_choice')
        payment_method = request.POST.get('payment_method') # upi, net_banking, etc.
        
        if payment_choice == 'part1':
            base_amount = part1_remaining
            late_fee = part1_penalty
            fee_amount = part1_total
            installment_name = "Part 1"
        elif payment_choice == 'part2':
            base_amount = part2_remaining
            late_fee = part2_penalty
            fee_amount = part2_total
            installment_name = "Part 2"
        elif payment_choice == 'full':
            base_amount = full_base
            late_fee = full_penalty
            fee_amount = full_total
            installment_name = "Full"
        else:
            messages.error(request, "Invalid payment choice selection.")
            return redirect('student_app:student_pay_fee')

        if fee_amount <= 0:
            messages.error(request, "Selected payment option is already fully cleared.")
            return redirect('student_app:student_pay_fee')

        try:
            gateway = PaymentGatewayFactory.get_gateway() # Gets the active gateway
            transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
            
            # Save breakdown so save receiver or dashboard can extract base amount
            fee_breakdown = {
                'installment': installment_name,
                'base_amount': str(base_amount),
                'late_fee': str(late_fee)
            }
            
            payment = Payment.objects.create(
                student=student,
                transaction_id=transaction_id,
                enrollment_number=student.roll or str(student.student_id),
                user_name=student.name,
                contact_no=student.phone_number,
                amount=fee_amount,
                payment_type=payment_method.upper(),
                transaction_status='PENDING',
                gateway_name=gateway.config.name,
                fee_breakdown=fee_breakdown
            )

            # Create Order at Gateway
            order_data = gateway.create_order(float(fee_amount), student_id=student.student_id)
            
            if gateway.config.name == 'razorpay':
                payment.gateway_order_id = order_data['id']
                payment.save()
                
                context = {
                    'order': order_data,
                    'payment': payment,
                    'razorpay_key': gateway.config.api_key,
                    'student': student,
                }
                return render(request, 'student_app/razorpay_checkout.html', context)
            
            elif gateway.config.name == 'stripe':
                payment.gateway_order_id = order_data['id']
                payment.save()
                return render(request, 'student_app/stripe_checkout.html', {'client_secret': order_data['client_secret'], 'payment': payment})

            elif gateway.config.name == 'demo':
                payment.gateway_order_id = order_data['id']
                payment.save()
                context = {
                    'order': order_data,
                    'payment': payment,
                    'student': student,
                    'transaction_id': payment.transaction_id,
                }
                return render(request, 'student_app/demo_payment_gateway.html', context)

        except PaymentGatewayError as e:
            messages.error(request, str(e))
            return redirect('student_app:student_pay_fee')

    context = {
        'student': student,
        'part1_base': part1_base,
        'part1_remaining': part1_remaining,
        'part1_penalty': part1_penalty,
        'part1_total': part1_total,
        'part2_base': part2_base,
        'part2_remaining': part2_remaining,
        'part2_penalty': part2_penalty,
        'part2_total': part2_total,
        'full_base': full_base,
        'full_penalty': full_penalty,
        'full_total': full_total,
    }
    return render(request, 'student_app/student_pay_fee.html', context)

@csrf_exempt
def razorpay_webhook(request):
    """
    Handle Razorpay Webhooks (Server-to-Server notifications)
    """
    if request.method == 'POST':
        gateway = PaymentGatewayFactory.get_gateway('razorpay')
        webhook_secret = gateway.config.webhook_secret
        
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature')

        if not webhook_secret or not signature:
            return HttpResponse(status=400)

        import hmac
        import hashlib
        expected_signature = hmac.new(
            key=webhook_secret.encode('utf-8'),
            msg=payload.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        if signature == expected_signature:
            import json
            data = json.loads(payload)
            event = data.get('event')
            
            if event == 'payment.captured':
                payment_data = data['payload']['payment']['entity']
                order_id = payment_data.get('order_id')
                
                try:
                    payment = Payment.objects.get(gateway_order_id=order_id)
                    if payment.transaction_status != 'SUCCESSFUL':
                        payment.transaction_status = 'SUCCESSFUL'
                        payment.gateway_payment_id = payment_data.get('id')
                        payment.save()
                except Payment.DoesNotExist:
                    pass
            
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400)

    return HttpResponse(status=405)

@csrf_exempt
def verify_payment(request):
    if request.method == 'POST':
        gateway_name = request.POST.get('gateway', 'razorpay')
        try:
            gateway = PaymentGatewayFactory.get_gateway(gateway_name)
            
            if gateway_name == 'razorpay':
                params = {
                    'razorpay_order_id': request.POST.get('razorpay_order_id'),
                    'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
                    'razorpay_signature': request.POST.get('razorpay_signature')
                }
                if gateway.verify_payment(params):
                    payment = Payment.objects.get(gateway_order_id=params['razorpay_order_id'])
                    payment.transaction_status = 'SUCCESSFUL'
                    payment.gateway_payment_id = params['razorpay_payment_id']
                    payment.save()
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'failed', 'message': 'Invalid signature'})
            
            elif gateway_name == 'demo':
                params = {
                    'demo_signature': request.POST.get('demo_signature'),
                    'order_id': request.POST.get('order_id')
                }
                if gateway.verify_payment(params):
                    payment = Payment.objects.get(gateway_order_id=params['order_id'])
                    payment.transaction_status = 'SUCCESSFUL'
                    payment.gateway_payment_id = f"DEMO_PAY_{uuid.uuid4().hex[:10].upper()}"
                    payment.save()
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'failed', 'message': 'Simulated Failure'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'invalid_request'})


@login_required(login_url='/authentication/login')
def payment_success(request):
    return render(request, 'student_app/payment_success.html')

@login_required(login_url='/authentication/login')
def student_fee_details(request):
    student = get_object_or_404(Student, user=request.user)
    from paybill.models import InstallmentConfig
    from datetime import date
    from decimal import Decimal
    
    bed = student.bed_set.first()
    yearly_fee = bed.total_amount if bed else 0
    if yearly_fee == 0:
        yearly_fee = FeeStructure.objects.aggregate(total=models.Sum('amount'))['total'] or 0

    installment_config = InstallmentConfig.get_config()
    today = date.today()
    
    part1_base = Decimal(str(yearly_fee)) / 2
    part2_base = Decimal(str(yearly_fee)) - part1_base
    
    payments = Payment.objects.filter(student=student).order_by('-created_at')
    
    successful_payments = payments.filter(transaction_status='SUCCESSFUL')
    total_paid = 0
    for p in successful_payments:
        if p.fee_breakdown and 'base_amount' in p.fee_breakdown:
            try:
                total_paid += Decimal(str(p.fee_breakdown['base_amount']))
            except Exception:
                total_paid += p.amount
        else:
            total_paid += p.amount

    # Part 1 calculation
    part1_paid = min(total_paid, part1_base)
    part1_remaining = part1_base - part1_paid
    part1_penalty = Decimal(0)
    part1_days_late = 0
    
    if part1_remaining > 0:
        if installment_config.part1_due_date and today > installment_config.part1_due_date:
            part1_days_late = (today - installment_config.part1_due_date).days
            part1_penalty = Decimal(part1_days_late) * Decimal(str(installment_config.part1_late_fee_per_day or 0))
            part1_status = 'OVERDUE'
        else:
            part1_status = 'PENDING'
    else:
        part1_status = 'PAID'
        
    # Part 2 calculation
    part2_paid = min(max(total_paid - part1_base, 0), part2_base)
    part2_remaining = part2_base - part2_paid
    part2_penalty = Decimal(0)
    part2_days_late = 0
    
    if part2_remaining > 0:
        if installment_config.part2_due_date and today > installment_config.part2_due_date:
            part2_days_late = (today - installment_config.part2_due_date).days
            part2_penalty = Decimal(part2_days_late) * Decimal(str(installment_config.part2_late_fee_per_day or 0))
            part2_status = 'OVERDUE'
        else:
            part2_status = 'PENDING'
    else:
        part2_status = 'PAID'
        
    total_penalty = part1_penalty + part2_penalty
    pending_fee = part1_remaining + part2_remaining # base remaining
    
    fee_structures = FeeStructure.objects.all()

    context = {
        'student': student,
        'total_fee': yearly_fee,
        'paid_fee': total_paid,
        'pending_fee': pending_fee,
        'payments': payments,
        'fee_structures': fee_structures,
        'installment_config': installment_config,
        'part1_base': part1_base,
        'part1_paid': part1_paid,
        'part1_remaining': part1_remaining,
        'part1_penalty': part1_penalty,
        'part1_status': part1_status,
        'part1_days_late': part1_days_late,
        'part2_base': part2_base,
        'part2_paid': part2_paid,
        'part2_remaining': part2_remaining,
        'part2_penalty': part2_penalty,
        'part2_status': part2_status,
        'part2_days_late': part2_days_late,
        'total_penalty': total_penalty,
        'total_due_with_penalty': pending_fee + total_penalty,
    }
    return render(request, 'student_app/student_fee_details.html', context)

@login_required(login_url='/authentication/login')
def fee_receipt(request, transaction_id):
    is_student = hasattr(request.user, 'student')
    if is_student:
        payment = get_object_or_404(Payment, transaction_id=transaction_id, student__user=request.user)
        base_template = 'student_base.html'
    else:
        payment = get_object_or_404(Payment, transaction_id=transaction_id)
        base_template = 'base.html'
    return render(request, 'student_app/fee_receipt_view.html', {
        'payment': payment,
        'base_template': base_template,
        'is_student': is_student
    })

@login_required(login_url='/authentication/login')
def download_fee_receipt(request, transaction_id):
    if pisa is None:
        return HttpResponse('PDF generation dependency is not installed.', status=500)

    is_student = hasattr(request.user, 'student')
    if is_student:
        student = get_object_or_404(Student, user=request.user)
        payment = get_object_or_404(Payment, transaction_id=transaction_id, student=student)
    else:
        payment = get_object_or_404(Payment, transaction_id=transaction_id)
        student = payment.student

    context = {
        'payment': payment,
        'student': student,
        'today': now(),
    }

    # Render the PDF-optimized HTML template with payment details
    html = render_to_string('student_app/fee_receipt_pdf.html', context)

    # Create the HTTP response with the PDF file
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Fee_Receipt_{transaction_id}.pdf"'

    # Convert the HTML to PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Check for errors
    if pisa_status.err:
        return HttpResponse('We had some errors while generating the PDF', status=500)

    return response

