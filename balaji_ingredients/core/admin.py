"""
core/admin.py — Register core models in Django Admin.
"""

from django.contrib import admin
from .models import SiteStat, ContactMessage, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'phone', 'email']

    def has_add_permission(self, request):
        # Only allow 1 instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ['value', 'label', 'description', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'email', 'phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'company', 'message']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
