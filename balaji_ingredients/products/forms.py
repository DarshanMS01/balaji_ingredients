"""
products/forms.py
Forms for submitting RFQ (QuoteRequest).
"""

from django import forms
from .models import QuoteRequest, Product


class QuoteRequestForm(forms.ModelForm):
    product_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = QuoteRequest
        fields = [
            'full_name',
            'company_name',
            'email',
            'phone',
            'gstin',
            'quantity_volume',
            'packaging_preference',
            'destination_city',
            'destination_pincode',
            'delivery_timeline',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'e.g. Ramesh Kumar', 'class': 'form-input'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g. Apex Food Processors Pvt Ltd', 'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'placeholder': 'procurement@company.com', 'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210', 'class': 'form-input'}),
            'gstin': forms.TextInput(attrs={'placeholder': '29AAAAA0000A1Z5 (Optional)', 'class': 'form-input'}),
            'quantity_volume': forms.TextInput(attrs={'placeholder': 'e.g. 10 Metric Tons (200 bags of 50kg)', 'class': 'form-input'}),
            'packaging_preference': forms.Select(
                choices=[
                    ('50kg PP Bags with Liner', '50kg PP Bags with LDPE Liner (Standard)'),
                    ('25kg PP Bags with Liner', '25kg PP Bags with LDPE Liner'),
                    ('1000kg FIBC Jumbo Tote Bags', '1000kg FIBC Jumbo Bulk Bags'),
                    ('Custom Private Label Packaging', 'Custom Private Label Packaging'),
                    ('Bulk Tanker / Loose Dispatch', 'Bulk / Loose Dispatch'),
                ],
                attrs={'class': 'form-select'}
            ),
            'destination_city': forms.TextInput(attrs={'placeholder': 'e.g. Bengaluru, Karnataka', 'class': 'form-input'}),
            'destination_pincode': forms.TextInput(attrs={'placeholder': '560001', 'class': 'form-input'}),
            'delivery_timeline': forms.TextInput(attrs={'placeholder': 'e.g. Within 10 days / Monthly recurring', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Specify any exact grading criteria, target pricing, or certification needs...', 'class': 'form-textarea'}),
        }
