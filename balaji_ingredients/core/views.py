"""
core/views.py — Public-facing page views for Level 1.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SiteStat
from .forms import ContactForm


def home(request):
    """Homepage with all 10 sections."""
    stats = SiteStat.objects.filter(is_active=True)
    return render(request, 'index.html', {'stats': stats})


def about(request):
    return render(request, 'core/about.html', {'page_title': 'About Us'})


def quality(request):
    return render(request, 'core/quality.html', {'page_title': 'Quality'})


def infrastructure(request):
    return render(request, 'core/infrastructure.html', {'page_title': 'Infrastructure'})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Thank you for reaching out. We will get back to you shortly.'
            )
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form, 'page_title': 'Contact Us'})
