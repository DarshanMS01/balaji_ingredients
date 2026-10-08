"""
portal/forms.py
Registration, authentication, and profile forms for B2B clients.
"""

from django import forms
from django.contrib.auth.models import User
from .models import CompanyProfile


class CompanyRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username', 'class': 'form-input'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'corporate.email@company.com', 'class': 'form-input'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Create secure password', 'class': 'form-input'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'class': 'form-input'})
    )

    class Meta:
        model = CompanyProfile
        fields = [
            'company_name',
            'business_type',
            'gstin',
            'pan_number',
            'phone',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'pincode',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g. Apex Agro Processors Ltd', 'class': 'form-input'}),
            'business_type': forms.Select(attrs={'class': 'form-select'}),
            'gstin': forms.TextInput(attrs={'placeholder': 'e.g. 29AAAAA0000A1Z5', 'class': 'form-input'}),
            'pan_number': forms.TextInput(attrs={'placeholder': 'e.g. AAAAA0000A', 'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210', 'class': 'form-input'}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Factory / Office Address', 'class': 'form-input'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Industrial Area / Landmark', 'class': 'form-input'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-input'}),
            'state': forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-input'}),
            'pincode': forms.TextInput(attrs={'placeholder': 'Pincode', 'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            'company_name',
            'business_type',
            'gstin',
            'pan_number',
            'phone',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'pincode',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'business_type': forms.Select(attrs={'class': 'form-select'}),
            'gstin': forms.TextInput(attrs={'class': 'form-input'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-input'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'state': forms.TextInput(attrs={'class': 'form-input'}),
            'pincode': forms.TextInput(attrs={'class': 'form-input'}),
        }
