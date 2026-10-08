"""
portal/models.py
B2B Client Profile, Orders, Order Items, and Shipment Tracking.
"""

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class CompanyProfile(models.Model):
    BUSINESS_TYPES = [
        ('manufacturer', 'Food Manufacturer / FMCG'),
        ('processor', 'Flour Mill / Spice Processor / Dal Mill'),
        ('distributor', 'Wholesaler / Distributor'),
        ('retail_chain', 'Supermarket / Retail Chain'),
        ('exporter', 'Export / Trading House'),
        ('horeca', 'Hotel / Restaurant / Catering (HoReCa)'),
        ('other', 'Other Business Enterprise'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=150)
    gstin = models.CharField(max_length=25, blank=True, verbose_name="GSTIN")
    pan_number = models.CharField(max_length=20, blank=True, verbose_name="PAN Number")
    business_type = models.CharField(max_length=40, choices=BUSINESS_TYPES, default='manufacturer')
    phone = models.CharField(max_length=30)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False, help_text="Checked after GST verification")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'B2B Company Profile'
        verbose_name_plural = 'B2B Company Profiles'

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('ready_dispatch', 'Ready for Dispatch'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('cod', 'COD'),
        ('verification_pending', 'Verification Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    QUALITY_CHOICES = [
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
        ('Export Quality', 'Export Quality'),
        ('Custom', 'Custom Requirements'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    quote_request = models.ForeignKey(
        'products.QuoteRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    order_number = models.CharField(max_length=50, unique=True, editable=False)

    # Customer Information
    customer_name = models.CharField(max_length=150, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    # Delivery Information
    delivery_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=30, blank=True, verbose_name="GSTIN")
    additional_requirements = models.TextField(blank=True)

    # Quality & Order Specifications
    quality = models.CharField(max_length=50, choices=QUALITY_CHOICES, default='Standard')
    custom_quality_notes = models.TextField(blank=True)
    is_quote_request = models.BooleanField(default=False)

    # Payment & Financials
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='cod')
    upi_utr_number = models.CharField(max_length=100, blank=True, verbose_name="UPI Transaction / UTR Number", help_text="Transaction reference number from customer UPI app")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    delivery_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Delivery charges confirmed by Balaji Ingredients")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="GST / Tax")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    advance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Payment gateway attributes (for future Razorpay expansion)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)

    # Logistics & Dispatch Information
    carrier_name = models.CharField(max_length=120, blank=True, help_text="e.g. VRL Logistics, Safechem Express")
    tracking_consignment_no = models.CharField(max_length=100, blank=True, help_text="LR / Consignment Note No.")
    vehicle_number = models.CharField(max_length=50, blank=True, help_text="e.g. KA-01-AB-1234")
    dispatch_date = models.DateField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)

    shipping_address = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes added by Balaji admin")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'B2B Commercial Order'
        verbose_name_plural = 'B2B Commercial Orders'

    def __str__(self):
        name = self.company_name or (self.user.username if self.user else self.customer_name)
        return f"{self.order_number} — {name} (₹{self.total_amount})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            seq = f"{Order.objects.count() + 101:06d}"
            self.order_number = f"BI-2026-{seq}"
        if not self.total_amount:
            self.total_amount = self.subtotal + self.delivery_charges + self.tax_amount
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        steps = {
            'pending': 15,
            'quote_confirmed': 35,
            'processing': 60,
            'dispatched': 85,
            'delivered': 100,
            'cancelled': 0
        }
        return steps.get(self.status, 15)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    product_name = models.CharField(max_length=150)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity in metric units")
    unit = models.CharField(max_length=30, default='Metric Tons')
    packaging = models.CharField(max_length=100, default='50kg PP Bags with Liner')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price per Metric Ton / Unit in INR")
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Order Line Item'
        verbose_name_plural = 'Order Line Items'

    def __str__(self):
        return f"{self.product_name} - {self.quantity} {self.unit} @ ₹{self.unit_price}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        super().save(*args, **kwargs)


class B2BDocument(models.Model):
    DOC_TYPES = [
        ('spec_sheet', 'Product Specification Sheet'),
        ('certificate', 'Certification & License'),
        ('quality_report', 'Quality & COA Lab Report'),
        ('invoice', 'Commercial / Proforma Invoice'),
        ('purchase_order', 'Purchase Order'),
        ('quote_doc', 'Quotation Document'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=40, choices=DOC_TYPES, default='spec_sheet')
    category = models.CharField(max_length=100, default='General')
    doc_number = models.CharField(max_length=80, blank=True)
    file_size = models.CharField(max_length=30, default='1.2 MB PDF')
    file_url = models.CharField(max_length=255, default='#')
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'B2B Document'
        verbose_name_plural = 'B2B Documents'

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon = models.CharField(max_length=40, default='bell')
    link = models.CharField(max_length=255, blank=True, default='/dashboard')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.title} - Read: {self.is_read}"


class SupportTicket(models.Model):
    SUPPORT_TYPES = [
        ('sales', 'Contact Sales & Pricing'),
        ('technical', 'Technical & Food Science Support'),
        ('order', 'Order & Logistics Support'),
        ('quality', 'Quality Assurance & COA'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    ticket_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    order_id = models.CharField(max_length=80, blank=True)
    support_type = models.CharField(max_length=40, choices=SUPPORT_TYPES, default='sales')
    subject = models.CharField(max_length=250)
    message = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    admin_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'

    def __str__(self):
        return f"{self.ticket_id} - {self.subject} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            uid = uuid.uuid4().hex[:6].upper()
            self.ticket_id = f"TICK-{uid}"
        super().save(*args, **kwargs)


class PaymentConfig(models.Model):
    """
    Dynamic Business Payment Settings for UPI ID, Payee details, and QR Code.
    Manageable directly by Admin.
    """
    business_upi_id = models.CharField(
        max_length=100,
        default='9902155348@axl',
        help_text="Official Business UPI ID (e.g. 9902155348@axl)"
    )
    payee_name = models.CharField(
        max_length=150,
        default='Balaji Ingredients',
        help_text="Payee business display name for UPI payments"
    )
    qr_image = models.ImageField(
        upload_to='payment_qr/',
        blank=True,
        null=True,
        help_text="Upload custom Business UPI QR Code image"
    )
    qr_image_url = models.CharField(
        max_length=255,
        default='images/upi_qr.jpg',
        help_text="Static / fallback image path for QR Code"
    )
    is_active = models.BooleanField(default=True, help_text="Set as active configuration for customer checkout")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Business UPI Payment Setting'
        verbose_name_plural = 'Business UPI Payment Settings'

    def __str__(self):
        return f"UPI Setting: {self.business_upi_id} ({self.payee_name})"

    @classmethod
    def get_active_config(cls):
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config, _ = cls.objects.get_or_create(
                business_upi_id='9902155348@axl',
                defaults={
                    'payee_name': 'Balaji Ingredients',
                    'qr_image_url': 'images/upi_qr.jpg',
                    'is_active': True,
                }
            )
        return config

