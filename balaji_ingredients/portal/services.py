"""
portal/services.py
Services for email notifications and Razorpay token payments.
"""

import logging
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_rfq_confirmation_email(quote_request):
    """Notify client and admin when an RFQ is submitted."""
    try:
        subject = f"[Balaji Ingredients] Quotation Request Received #{quote_request.id:04d}"
        message = (
            f"Dear {quote_request.full_name},\n\n"
            f"Thank you for your enquiry with Balaji Ingredients.\n\n"
            f"We have received your quotation request for: {quote_request.product_name or 'General Ingredient Requirement'}\n"
            f"Volume: {quote_request.quantity_volume}\n"
            f"Packaging: {quote_request.packaging_preference}\n"
            f"Delivery Location: {quote_request.destination_city or 'To be confirmed'}\n\n"
            "Our commercial desk is calculating current spot rates and logistics costs. "
            "A formal quotation will be sent to your email shortly.\n\n"
            "Best regards,\n"
            "Commercial Desk\n"
            "Balaji Ingredients\n"
            "info@balaji-ingredients.com"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote_request.email],
            fail_silently=True
        )

        # Notify internal admin
        admin_subject = f"NEW RFQ ALERT #{quote_request.id:04d} - {quote_request.company_name}"
        admin_message = (
            f"New B2B RFQ submitted:\n"
            f"Company: {quote_request.company_name}\n"
            f"Contact: {quote_request.full_name} ({quote_request.phone}, {quote_request.email})\n"
            f"Product: {quote_request.product_name}\n"
            f"Volume: {quote_request.quantity_volume}\n"
            f"Destination: {quote_request.destination_city} ({quote_request.destination_pincode})\n"
            f"Notes: {quote_request.notes}\n"
        )
        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Error sending RFQ email: {e}")


def send_order_dispatch_email(order):
    """Notify client when order status changes to Dispatched with LR and vehicle details."""
    try:
        subject = f"[Balaji Ingredients] Consignment Dispatched: Order {order.order_number}"
        message = (
            f"Dear {order.user.company_profile.company_name if hasattr(order.user, 'company_profile') else order.user.username},\n\n"
            f"Your consignment for Order {order.order_number} has been dispatched.\n\n"
            f"Carrier: {order.carrier_name or 'Contracted Freight Carrier'}\n"
            f"LR / Consignment No: {order.tracking_consignment_no or 'N/A'}\n"
            f"Vehicle Number: {order.vehicle_number or 'N/A'}\n"
            f"Dispatch Date: {order.dispatch_date or 'Today'}\n"
            f"Expected Arrival: {order.expected_delivery_date or 'Per transit schedule'}\n\n"
            "You can log in to your Client Portal at any time to view real-time tracking milestones and download your Proforma Invoice.\n\n"
            "Best regards,\n"
            "Logistics & Operations\n"
            "Balaji Ingredients"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Error sending dispatch notification: {e}")


def get_razorpay_client():
    """Returns Razorpay client instance if configured."""
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
    if key_id and key_secret:
        try:
            import razorpay
            return razorpay.Client(auth=(key_id, key_secret))
        except ImportError:
            return None
    return None


import hashlib
import hmac
import json
import uuid
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone
from .models import Order, PaymentTransaction


def get_payment_credentials():
    """
    Returns configured merchant payment credentials.
    Supports Razorpay, custom UPI merchant gateways, or secure testing adapter.
    """
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None) or key_secret or settings.SECRET_KEY

    is_live = bool(key_id and key_secret and not key_id.startswith('your_'))
    return {
        'key_id': key_id if is_live else 'rzp_test_balaji2026',
        'key_secret': key_secret if is_live else 'test_secret_balaji_key',
        'webhook_secret': webhook_secret,
        'is_live': is_live,
    }


def compute_signature(message, secret):
    """Computes HMAC-SHA256 signature for payment verification."""
    return hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def create_payment_transaction(order, amount=None, provider='razorpay', idempotency_key=None):
    """
    Creates a new PaymentTransaction record on the server for the specified order.
    Calculates exact payable amount safely using Decimal.
    """
    if amount is None:
        amount = order.outstanding_balance
    else:
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            amount = order.outstanding_balance

    if amount <= Decimal('0.00'):
        raise ValueError("Payable amount must be greater than zero.")

    creds = get_payment_credentials()
    txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    # Generate or request provider order ID
    provider_order_id = ''
    if creds['is_live']:
        client = get_razorpay_client()
        if client:
            try:
                razorpay_order = client.order.create({
                    'amount': int(amount * 100),  # amount in paise
                    'currency': 'INR',
                    'receipt': order.order_number,
                    'notes': {
                        'order_number': order.order_number,
                        'customer': order.customer_name or (order.user.username if order.user else 'Guest'),
                    }
                })
                provider_order_id = razorpay_order.get('id', '')
            except Exception as e:
                logger.error(f"Error creating Razorpay order: {e}")
                provider_order_id = f"order_err_{uuid.uuid4().hex[:8]}"

    if not provider_order_id:
        # Deterministic, signed test provider order ID
        provider_order_id = f"order_{order.order_number}_{uuid.uuid4().hex[:6]}"

    # Save to Order
    order.razorpay_order_id = provider_order_id
    order.save(update_fields=['razorpay_order_id'])

    transaction_obj = PaymentTransaction.objects.create(
        order=order,
        transaction_id=txn_id,
        provider=provider,
        amount=amount,
        currency='INR',
        status='initiated',
        provider_order_id=provider_order_id,
        idempotency_key=idempotency_key or f"idem_{uuid.uuid4().hex[:10]}",
    )
    return transaction_obj


@transaction.atomic
def verify_payment_callback(order_number, provider_order_id, provider_payment_id, signature, verified_amount=None, raw_payload=None):
    """
    Verifies payment signature, confirms order match, compares amounts with Decimal,
    and atomically updates PaymentTransaction and Order records.
    Guards against double-counting and race conditions via select_for_update().
    """
    creds = get_payment_credentials()

    # 1. Signature Verification
    expected_message = f"{provider_order_id}|{provider_payment_id}"
    expected_signature = compute_signature(expected_message, creds['key_secret'])

    signature_valid = False
    if creds['is_live']:
        client = get_razorpay_client()
        if client:
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': provider_order_id,
                    'razorpay_payment_id': provider_payment_id,
                    'razorpay_signature': signature
                })
                signature_valid = True
            except Exception:
                signature_valid = False
        else:
            signature_valid = hmac.compare_digest(expected_signature, str(signature or ''))
    else:
        signature_valid = hmac.compare_digest(expected_signature, str(signature or ''))

    if not signature_valid:
        return {
            'success': False,
            'error': 'Invalid payment signature. Transaction verification failed.',
            'status_code': 400
        }

    # 2. Lock Order to prevent concurrent modifications
    try:
        order = Order.objects.select_for_update().get(order_number=order_number)
    except Order.DoesNotExist:
        return {
            'success': False,
            'error': f"Order #{order_number} not found.",
            'status_code': 404
        }

    # 3. Locate or match PaymentTransaction
    txn = PaymentTransaction.objects.filter(
        order=order,
        provider_order_id=provider_order_id
    ).first()

    if not txn:
        # Check if transaction exists under another order (order mismatch guard!)
        foreign_txn = PaymentTransaction.objects.filter(provider_order_id=provider_order_id).first()
        if foreign_txn and foreign_txn.order_id != order.id:
            return {
                'success': False,
                'error': f"Transaction {provider_order_id} belongs to order #{foreign_txn.order.order_number}, not #{order_number}.",
                'status_code': 400
            }
        # Create transaction if missing
        txn = PaymentTransaction.objects.create(
            order=order,
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            provider='razorpay',
            amount=Decimal(str(verified_amount or order.outstanding_balance)),
            status='initiated',
            provider_order_id=provider_order_id,
        )

    # 4. Idempotency Check — Do not double-count duplicate callbacks/webhooks
    if txn.status == 'success' and txn.provider_payment_id == provider_payment_id:
        return {
            'success': True,
            'message': 'Transaction already processed and verified successfully.',
            'order_number': order.order_number,
            'payment_status': order.payment_status,
            'verified_paid_amount': float(order.verified_paid_amount),
            'outstanding_balance': float(order.outstanding_balance),
            'duplicate': True,
        }

    # 5. Amount Resolution
    if verified_amount is not None:
        try:
            payment_amount = Decimal(str(verified_amount))
        except (InvalidOperation, TypeError, ValueError):
            payment_amount = txn.amount
    else:
        payment_amount = txn.amount

    # 6. Update PaymentTransaction
    txn.status = 'success'
    txn.amount = payment_amount
    txn.provider_payment_id = provider_payment_id
    txn.provider_signature = signature
    txn.signature_verified = True
    txn.verified_at = timezone.now()
    if raw_payload:
        txn.raw_response = raw_payload
    txn.save()

    # 7. Update Order Totals and Status
    order.razorpay_payment_id = provider_payment_id
    
    total_verified = order.verified_paid_amount  # uses Decimal Sum
    if total_verified >= order.total_amount:
        order.payment_status = 'paid'
        if order.status == 'pending':
            order.status = 'confirmed'
        if total_verified > order.total_amount:
            excess = total_verified - order.total_amount
            order.admin_notes = (
                f"{order.admin_notes}\n[{timezone.now().strftime('%d %b %Y %H:%M')}] "
                f"EXCESS PAYMENT RECORDED: ₹{excess:.2f} received beyond invoice total."
            ).strip()
    elif total_verified > Decimal('0.00'):
        order.payment_status = 'partial'
    else:
        order.payment_status = 'failed'

    order.save()

    # Log in Admin Audit Log
    try:
        from admin_dashboard.models import AuditLog
        AuditLog.objects.create(
            user=order.user if order.user else None,
            action="Verified Automatic Payment",
            model_name="Order",
            object_id=order.id,
            details=(
                f"Automatic payment verified for #{order.order_number}. "
                f"Received: ₹{payment_amount:.2f}. Total Verified: ₹{total_verified:.2f} / ₹{order.total_amount:.2f}. "
                f"Status: {order.get_payment_status_display()}. Txn ID: {provider_payment_id}"
            )
        )
    except Exception:
        pass

    return {
        'success': True,
        'message': f"Payment of ₹{payment_amount:.2f} successfully verified.",
        'order_number': order.order_number,
        'payment_status': order.payment_status,
        'verified_paid_amount': float(order.verified_paid_amount),
        'outstanding_balance': float(order.outstanding_balance),
        'excess_amount': float(order.excess_amount),
    }


@transaction.atomic
def handle_payment_webhook(payload_bytes, signature_header):
    """
    Processes incoming merchant gateway webhook notifications.
    Verifies signature and idempotently updates order records.
    """
    creds = get_payment_credentials()
    webhook_secret = creds['webhook_secret']

    # 1. Verify Webhook Signature
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, str(signature_header or '')):
        logger.warning("Payment webhook signature mismatch")
        return {'success': False, 'error': 'Invalid webhook signature', 'status_code': 400}

    # 2. Parse Event Payload
    try:
        data = json.loads(payload_bytes.decode('utf-8'))
    except Exception as e:
        return {'success': False, 'error': f"Malformed JSON: {e}", 'status_code': 400}

    event = data.get('event', '')
    payload = data.get('payload', {}).get('payment', {}).get('entity', {})

    if not payload:
        return {'success': True, 'message': 'Event ignored, no payment entity'}

    provider_order_id = payload.get('order_id', '')
    provider_payment_id = payload.get('id', '')
    amount_in_paise = payload.get('amount', 0)
    verified_amount = Decimal(str(amount_in_paise)) / Decimal('100.00')

    notes = payload.get('notes', {})
    order_number = notes.get('order_number')

    if not order_number and provider_order_id:
        order_match = Order.objects.filter(razorpay_order_id=provider_order_id).first()
        if order_match:
            order_number = order_match.order_number

    if not order_number:
        return {'success': False, 'error': 'Unable to associate webhook with an order', 'status_code': 400}

    if event in ['payment.captured', 'order.paid']:
        dummy_sig = compute_signature(f"{provider_order_id}|{provider_payment_id}", creds['key_secret'])
        return verify_payment_callback(
            order_number=order_number,
            provider_order_id=provider_order_id,
            provider_payment_id=provider_payment_id,
            signature=dummy_sig,
            verified_amount=verified_amount,
            raw_payload=data
        )
    elif event == 'payment.failed':
        try:
            order = Order.objects.get(order_number=order_number)
            PaymentTransaction.objects.create(
                order=order,
                transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                provider='razorpay',
                amount=verified_amount,
                status='failed',
                provider_order_id=provider_order_id,
                provider_payment_id=provider_payment_id,
                raw_response=data
            )
            if order.payment_status != 'paid':
                order.payment_status = 'failed'
                order.save(update_fields=['payment_status'])
            return {'success': True, 'message': 'Payment failure recorded'}
        except Order.DoesNotExist:
            return {'success': False, 'error': 'Order not found', 'status_code': 404}

    return {'success': True, 'message': f"Event {event} acknowledged"}
