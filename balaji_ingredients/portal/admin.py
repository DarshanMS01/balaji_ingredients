from django.contrib import admin
from django.contrib import messages
from .models import CompanyProfile, Order, OrderItem, PaymentConfig


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'product_name', 'quantity', 'unit', 'packaging', 'unit_price', 'total_price')


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'business_type', 'gstin', 'phone', 'city', 'state', 'is_verified')
    list_filter = ('business_type', 'is_verified', 'state')
    search_fields = ('company_name', 'gstin', 'pan_number', 'user__username', 'user__email', 'phone')
    list_editable = ('is_verified',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'customer_name',
        'company_name',
        'quality',
        'subtotal',
        'delivery_charges',
        'total_amount',
        'payment_method',
        'payment_status',
        'upi_utr_number',
        'status',
        'created_at'
    )
    list_filter = (
        'status',
        'payment_status',
        'payment_method',
        'quality',
        'is_quote_request',
        'created_at',
        'state'
    )
    search_fields = (
        'order_number',
        'customer_name',
        'company_name',
        'phone',
        'email',
        'upi_utr_number',
        'city',
        'tracking_consignment_no'
    )
    list_editable = ('status', 'payment_status', 'delivery_charges')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    actions = ['verify_payment', 'reject_payment']

    @admin.action(description='Verify Payment (Mark Paid & Confirm Order)')
    def verify_payment(self, request, queryset):
        count = queryset.update(payment_status='paid', status='confirmed')
        self.message_user(
            request,
            f"{count} order(s) successfully marked as Paid and Confirmed.",
            messages.SUCCESS
        )

    @admin.action(description='Reject Payment (Mark Payment Failed)')
    def reject_payment(self, request, queryset):
        count = queryset.update(payment_status='failed')
        self.message_user(
            request,
            f"{count} order(s) payment marked as Failed.",
            messages.WARNING
        )

    fieldsets = (
        ('Order Identification', {
            'fields': ('order_number', 'status', 'is_quote_request', 'created_at', 'updated_at')
        }),
        ('Customer & Company Information', {
            'fields': ('user', 'customer_name', 'company_name', 'email', 'phone', 'gstin')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_status', 'upi_utr_number', 'subtotal', 'delivery_charges', 'tax_amount', 'total_amount', 'advance_amount')
        }),
        ('Delivery & Destination Address', {
            'fields': ('delivery_address', 'city', 'state', 'pincode', 'shipping_address')
        }),
        ('Product Quality & Requirements', {
            'fields': ('quality', 'custom_quality_notes', 'additional_requirements', 'customer_notes')
        }),
        ('Logistics, Dispatch & Admin Notes', {
            'fields': ('carrier_name', 'tracking_consignment_no', 'vehicle_number', 'dispatch_date', 'expected_delivery_date', 'admin_notes')
        }),
    )


@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ('business_upi_id', 'payee_name', 'qr_image_url', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    fieldsets = (
        ('Business UPI Configuration', {
            'fields': ('business_upi_id', 'payee_name', 'is_active')
        }),
        ('QR Code Display', {
            'fields': ('qr_image', 'qr_image_url'),
            'description': 'Upload a custom UPI QR code image or specify a static image path.'
        }),
    )

