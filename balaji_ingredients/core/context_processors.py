"""
core/context_processors.py
Injects global site configuration into every template context.
"""


from .models import SiteSettings


def global_context(request):
    try:
        settings_obj = SiteSettings.load()
        return {
            'SITE_NAME': settings_obj.company_name,
            'SITE_TAGLINE': settings_obj.tagline,
            'SITE_EMAIL': settings_obj.email,
            'SITE_PHONE': settings_obj.phone,
            'SITE_ADDRESS': settings_obj.office_address,
            'SITE_HOURS': settings_obj.business_hours,
            'site_settings': settings_obj,
        }
    except Exception:
        return {
            'SITE_NAME': 'Balaji Ingredients',
            'SITE_TAGLINE': "Let's craft what's next, together.",
            'SITE_EMAIL': 'yadavdarshanms@gmail.com',
            'SITE_PHONE': '+91 98450 11223',
            'SITE_ADDRESS': 'APMC Yard & Industrial Processing Facility, Kalaburagi / Bengaluru, Karnataka, India',
            'SITE_HOURS': 'Mon - Sat: 9:00 AM – 7:00 PM IST',
            'site_settings': None,
        }

