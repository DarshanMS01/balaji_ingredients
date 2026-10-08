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
