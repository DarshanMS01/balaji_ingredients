"""
products/models.py
Models for Category, Product, ProductSpecification, and QuoteRequest (RFQ).
"""

from django.db import models
from django.urls import reverse
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    icon = models.CharField(max_length=20, default='◈')
    accent_color = models.CharField(max_length=40, default='#2e7031')
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Ingredient Category'
        verbose_name_plural = 'Ingredient Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'category_slug': self.slug})

    @property
    def image_filename(self):
        return f'images/{self.slug}.jpg'


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    subtitle = models.CharField(max_length=250, blank=True)
    description = models.TextField()

    # Technical Specifications summary
    grade = models.CharField(max_length=100, default='Sortex Cleaned Grade A')
    purity_percentage = models.CharField(max_length=50, default='99.5% Min')
    moisture_content = models.CharField(max_length=50, default='< 11%')
    shelf_life = models.CharField(max_length=80, default='12 Months')
    origin = models.CharField(max_length=100, default='India')
    min_order_qty = models.CharField(max_length=100, default='1 Metric Ton (1000 kg)')
    packaging_options = models.CharField(
        max_length=255,
        default='25kg / 50kg PP Bags with LDPE liner, 1000kg FIBC Jumbo Bags'
    )

    # Pricing & Commercial details
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('8500.00'),
        help_text="Price per unit in INR (₹)"
    )
    unit_name = models.CharField(
        max_length=40,
        default='Quintal (100 kg)',
        help_text="Unit of measurement e.g. Quintal, Metric Ton, 50kg Bag"
    )

    applications = models.CharField(
        max_length=255,
        default='Food Manufacturing, Snacks, Bakery, Commercial Milling',
        blank=True,
        help_text="Key commercial use cases"
    )

    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_gradient = models.CharField(
        max_length=120,
        default='linear-gradient(135deg, #c8a96e 0%, #a07840 50%, #7a5c2c 100%)',
        help_text='CSS gradient fallback when image is not uploaded'
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_absolute_url(self):
        return reverse(
            'products:product_detail',
            kwargs={'category_slug': self.category.slug, 'product_slug': self.slug}
        )

    @property
    def formatted_price(self):
        return f"₹{self.unit_price:,.2f}"



class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    parameter_name = models.CharField(max_length=120, help_text="e.g. Protein Content, Foreign Matter")
    parameter_value = models.CharField(max_length=150, help_text="e.g. 22.0% Min, < 0.15%")
    test_method = models.CharField(max_length=100, blank=True, help_text="e.g. AOAC / IS:4333")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Technical Specification'
        verbose_name_plural = 'Technical Specifications'

    def __str__(self):
        return f"{self.parameter_name}: {self.parameter_value}"


class QuoteRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('quote_sent', 'Quotation Sent'),
        ('negotiation', 'Negotiation'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quote_requests'
    )
    product_name = models.CharField(max_length=150, blank=True)
    category_name = models.CharField(max_length=100, blank=True)

    full_name = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    gstin = models.CharField(max_length=30, blank=True, verbose_name="GSTIN / Tax ID")

    quantity_volume = models.CharField(
        max_length=100,
        help_text="e.g. 5 MT, 20 MT (1 Full Truckload), 100 Bags"
    )
    packaging_preference = models.CharField(
        max_length=120,
        default='50kg PP Bags with Liner',
        help_text="e.g. 25kg PP, 50kg PP, 1 MT Jumbo Tote Bag, Bulk"
    )
    destination_city = models.CharField(max_length=100, blank=True)
    destination_pincode = models.CharField(max_length=20, blank=True)
    delivery_timeline = models.CharField(max_length=100, blank=True, help_text="e.g. Within 7 days, Monthly contract")
    notes = models.TextField(blank=True, help_text="Specific grade requirements, target price, etc.")

    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='new')
    quoted_price_per_unit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Official price per MT or Kg quoted to client"
    )
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quote Request (RFQ)'
        verbose_name_plural = 'Quote Requests (RFQs)'

    def __str__(self):
        prod = self.product_name or (self.product.name if self.product else 'General Requirement')
        return f"RFQ #{self.id:04d} - {self.company_name} ({prod})"

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.category_name and self.product.category:
            self.category_name = self.product.category.name
        super().save(*args, **kwargs)
