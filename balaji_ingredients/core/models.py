"""
core/models.py
SiteStats — Business Snapshot numbers editable from Django Admin.
ContactMessage — Stores messages from the contact page.
"""

from django.db import models


class SiteStat(models.Model):
    """A single configurable statistic shown in the Statistics section."""
    label = models.CharField(max_length=120, help_text="e.g. Years / Product Experience")
    value = models.CharField(max_length=30, help_text="e.g. 25+ or 500+")
    description = models.CharField(max_length=255, blank=True, help_text="Supporting label or detail")
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order (ascending)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Site Statistic'
        verbose_name_plural = 'Site Statistics'

    def __str__(self):
        return f"{self.value} — {self.label}"


class SiteSettings(models.Model):
    """Global configuration for Balaji Ingredients manageable via Django Admin."""
    company_name = models.CharField(max_length=150, default='Balaji Ingredients')
    tagline = models.CharField(max_length=250, default="Let's craft what's next, together.")
    hero_headline = models.CharField(max_length=250, default="Let's craft what's next, together.")
    hero_subtitle = models.TextField(
        default="Premium food ingredients, carefully sourced, processed and delivered with consistency you can trust."
    )
    about_title = models.CharField(
        max_length=250,
        default="Precision Food Ingredients for Value-Added Formulations"
    )
    about_text = models.TextField(
        default="From traditional grains and pulses to carefully processed spice ingredients, Balaji Ingredients works with trusted sourcing networks and controlled processing practices to provide consistent ingredients for commercial applications."
    )
    phone = models.CharField(max_length=50, default="+91 98450 11223")
    email = models.EmailField(default="yadavdarshanms@gmail.com")
    office_address = models.TextField(
        default="APMC Yard & Industrial Processing Facility, Kalaburagi / Bengaluru, Karnataka, India"
    )
    business_hours = models.CharField(max_length=120, default="Mon - Sat: 9:00 AM – 7:00 PM IST")
    linkedin_url = models.URLField(blank=True, default="https://linkedin.com")
    instagram_url = models.URLField(blank=True, default="https://instagram.com")
    facebook_url = models.URLField(blank=True, default="https://facebook.com")

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return f"{self.company_name} Configuration"

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj



class ContactMessage(models.Model):
    """Stores messages submitted via the Contact page."""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
    ]

    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=300, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"{self.name} — {self.email} ({self.created_at.strftime('%d %b %Y')})"
