"""
admin_dashboard/models.py
Models for Inventory Stock Movements, Promotions/Coupons, and Administrative Audit Logs.
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Stock In / Procurement'),
        ('out', 'Stock Out / Damage & Scrap'),
        ('fulfillment', 'Order Fulfillment'),
        ('adjustment', 'Physical Audit Adjustment'),
    ]

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, default='adjustment')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text="Quantity in product unit (e.g. kg)")
    previous_stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    new_stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    reason = models.CharField(max_length=255, help_text="Reason or batch note for stock change")
    reference_order = models.CharField(max_length=100, blank=True, help_text="Order ID if related to order fulfillment")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_adjustments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'

    def __str__(self):
        return f"{self.product.name} ({self.get_movement_type_display()}): {self.quantity} [New: {self.new_stock}]"


class Promotion(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Discount (%)'),
        ('flat', 'Flat Amount Discount (₹)'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Coupon code in UPPERCASE, e.g. DIWALI10, BULK1000")
    title = models.CharField(max_length=150, help_text="Campaign title e.g. B2B Launch Special")
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or Flat amount")
    min_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Minimum order cart value to qualify")
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Max discount cap for percentage promos")
    usage_limit = models.PositiveIntegerField(default=100, help_text="Total times this coupon can be redeemed")
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promotion & Coupon'
        verbose_name_plural = 'Promotions & Coupons'

    def __str__(self):
        val = f"{self.discount_value}%" if self.discount_type == 'percentage' else f"₹{self.discount_value}"
        return f"{self.code} — {self.title} ({val} OFF)"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=120, help_text="Action title e.g. Order Status Changed, Product Price Updated")
    model_name = models.CharField(max_length=80, help_text="Model touched e.g. Order, Product, Category")
    object_id = models.CharField(max_length=80, blank=True)
    details = models.TextField(help_text="Detailed summary of changes made")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        user_name = self.user.username if self.user else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {user_name} -> {self.action} ({self.model_name})"

    @classmethod
    def log(cls, user, action, model_name, object_id='', details='', request=None):
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

        return cls.objects.create(
            user=user if (user and user.is_authenticated) else None,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            details=details,
            ip_address=ip
        )
