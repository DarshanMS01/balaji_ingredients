"""
products/admin.py
Admin management for Category, Product, ProductSpecification, and QuoteRequest.
"""

from django.contrib import admin
from .models import Category, Product, ProductSpecification, QuoteRequest


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 2
    fields = ('parameter_name', 'parameter_value', 'test_method', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit_price', 'unit_name', 'grade', 'purity_percentage', 'moisture_content', 'is_featured', 'is_active', 'order')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('name', 'subtitle', 'description', 'grade')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('unit_price', 'is_featured', 'is_active', 'order')
    inlines = [ProductSpecificationInline]


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'product_name', 'quantity_volume', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'packaging_preference')
    search_fields = ('company_name', 'full_name', 'email', 'phone', 'product_name', 'gstin')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
