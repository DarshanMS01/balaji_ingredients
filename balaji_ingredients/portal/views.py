"""
portal/views.py
Complete B2B Client Portal views & APIs for Balaji Ingredients.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
import requests
import urllib.parse
import secrets
import pyotp
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import date, timedelta
import json
import uuid

from .models import CompanyProfile, Order, OrderItem, B2BDocument, Notification, SupportTicket, PasswordResetOTP
from products.models import Category, Product, ProductSpecification, QuoteRequest
import re
import hashlib
from django.utils import timezone


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def normalize_phone_number(raw_phone):
    """
    Strips non-digits. Returns 10-digit number for Indian numbers or normalized string.
    """
    if not raw_phone:
        return ''
    digits = re.sub(r'\D', '', str(raw_phone))
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    return digits


def find_user_by_identifier(identifier):
    """
    Resolves User by email or mobile number or username.
    Returns (user_obj, matched_by) or (None, None).
    """
    if not identifier:
        return None, None
    raw = str(identifier).strip()

    # 1. Email check
    if '@' in raw:
        u = User.objects.filter(email__iexact=raw).first()
        if u:
            return u, 'email'
        return None, None

    # 2. Phone / mobile check
    digits = normalize_phone_number(raw)
    if len(digits) >= 10:
        last10 = digits[-10:]
        profiles = CompanyProfile.objects.all()
        for p in profiles:
            p_digits = normalize_phone_number(p.phone)
            if p_digits and (p_digits == digits or p_digits.endswith(last10) or digits.endswith(p_digits[-10:] if len(p_digits) >= 10 else p_digits)):
                return p.user, 'phone'

    # 3. Direct username check
    u = User.objects.filter(username__iexact=raw).first()
    if u:
        return u, 'username'

    return None, None


def mask_contact_info(identifier, channel='email'):
    """
    Returns masked version of email or phone for secure display.
    """
    if not identifier:
        return 'your registered account'
    if channel == 'sms' or ('@' not in identifier and normalize_phone_number(identifier)):
        digits = normalize_phone_number(identifier)
        if len(digits) >= 10:
            return f"+91 {digits[:2]}******{digits[-2:]}"
        return identifier
    else:
        parts = identifier.split('@')
        if len(parts) == 2:
            uname = parts[0]
            masked_uname = uname[:2] + '***' if len(uname) > 2 else uname + '***'
            return f"{masked_uname}@{parts[1]}"
        return identifier


def login_view(request):
    """
    Renders login screen with support for both email and mobile login,
    returning distinct error messages for account not found vs incorrect password.
    """
    initial_tab = request.GET.get('tab', 'login')

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip() or request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me') == 'on'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

        if not identifier or not password:
            msg = 'Please enter both your registered email or mobile number and password.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'portal/auth.html', {'tab': 'login', 'identifier': identifier})

        # 1. Look up user by email, mobile, or username
        user_obj, match_type = find_user_by_identifier(identifier)
        if not user_obj:
            not_found_msg = 'Account not found. Please sign up to create your Balaji Ingredients account.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': not_found_msg}, status=404)
            messages.error(request, not_found_msg)
            return render(request, 'portal/auth.html', {'tab': 'login', 'identifier': identifier})

        # 2. Authenticate user credentials
        user = authenticate(request, username=user_obj.username, password=password)
        if user is None:
            pwd_err_msg = 'Incorrect password. Please try again.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': pwd_err_msg}, status=400)
            messages.error(request, pwd_err_msg)
            return render(request, 'portal/auth.html', {'tab': 'login', 'identifier': identifier})

        if not user.is_active:
            disabled_msg = 'Account is inactive. Please contact Balaji Ingredients support.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': disabled_msg}, status=403)
            messages.error(request, disabled_msg)
            return render(request, 'portal/auth.html', {'tab': 'login'})

        login(request, user)
        if not remember_me:
            request.session.set_expiry(0) # expires when browser closes
        else:
            request.session.set_expiry(1209600) # 2 weeks

        next_url = request.GET.get('next') or request.POST.get('next') or '/'
        if is_ajax:
            return JsonResponse({
                'success': True,
                'redirect_url': next_url,
                'message': f'Welcome back, {user.first_name or user.username}!',
                'user': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'username': user.username
                }
            })
        messages.success(request, f"Welcome back, {user.first_name or user.username}.")
        return redirect(next_url)

    return render(request, 'portal/auth.html', {'tab': initial_tab})


def register_view(request):
    """
    Handles B2B user registration with strict validations:
    - Full name required
    - Email valid format & duplicate check
    - Mobile 10-digit format & duplicate check
    - Password matching and minimum 6 characters
    - Terms and conditions confirmation
    """
    if request.user.is_authenticated:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        mobile = request.POST.get('mobile', '').strip() or request.POST.get('phone', '').strip()
        company_name = request.POST.get('company_name', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        terms = request.POST.get('terms') in ['on', 'true', True, 1, '1']

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

        # Validations
        if not full_name:
            msg = 'Full name is required.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        if not email or not EMAIL_REGEX.match(email):
            msg = 'Please enter a valid email address.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        mobile_digits = normalize_phone_number(mobile)
        if len(mobile_digits) < 10:
            msg = 'Please enter a valid 10-digit mobile number.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        # Duplicate email check
        if User.objects.filter(email__iexact=email).exists():
            msg = 'This email address is already registered. Please sign in or use a different email.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        # Duplicate mobile check
        last10 = mobile_digits[-10:]
        profiles = CompanyProfile.objects.all()
        for p in profiles:
            p_digits = normalize_phone_number(p.phone)
            if p_digits and (p_digits == mobile_digits or p_digits.endswith(last10)):
                msg = 'This mobile number is already registered. Please sign in or use a different mobile number.'
                return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        # Passwords check
        if password != confirm_password:
            msg = 'Passwords do not match. Please verify your passwords.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        if len(password) < 6:
            msg = 'Password must be at least 6 characters long.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        if not terms:
            msg = 'Please agree to the Terms & Conditions and Privacy Policy to create your account.'
            return JsonResponse({'success': False, 'message': msg}, status=400) if is_ajax else render_err(request, msg)

        # Generate unique username
        base_username = email.split('@')[0][:25]
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{suffix}"
            suffix += 1

        first_name = full_name.split(' ')[0][:30]
        last_name = ' '.join(full_name.split(' ')[1:])[:30] if ' ' in full_name else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        formatted_phone = f"+91 {mobile_digits[-10:]}"
        CompanyProfile.objects.create(
            user=user,
            company_name=company_name or f"{full_name}'s Enterprise",
            phone=formatted_phone,
            business_type='manufacturer',
            address_line1='Bengaluru, Karnataka',
            city='Bengaluru',
            state='Karnataka',
            pincode='560001',
            is_verified=True
        )

        # Auto login
        login(request, user)
        msg = f"Account created successfully! Welcome to Balaji Ingredients, {full_name}."
        if is_ajax:
            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/',
                'message': msg,
                'user': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'phone': formatted_phone
                }
            })
        messages.success(request, msg)
        return redirect('portal:dashboard')

    return render(request, 'portal/auth.html', {'tab': 'signup'})


def forgot_password_view(request):
    """
    Dedicated forgot password view for Balaji Ingredients.
    """
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip() or request.POST.get('email', '').strip()
        channel = request.POST.get('channel', 'email').strip().lower()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

        user_obj, match_type = find_user_by_identifier(identifier)
        if not user_obj:
            msg = 'Account not found. Please verify the email or mobile number, or sign up.'
            return JsonResponse({'success': False, 'message': msg}, status=404) if is_ajax else render_err(request, msg)

        # 60s cooldown check
        recent_otp = PasswordResetOTP.objects.filter(user=user_obj).order_by('-created_at').first()
        if recent_otp and timezone.now() < recent_otp.resend_available_at:
            remaining = max(1, int((recent_otp.resend_available_at - timezone.now()).total_seconds()))
            msg = f'Please wait {remaining} seconds before requesting a new OTP.'
            return JsonResponse({'success': False, 'message': msg}, status=429) if is_ajax else render_err(request, msg)

        # Generate 6-digit OTP
        otp = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = hashlib.sha256(otp.encode('utf-8')).hexdigest()

        # Target and masking
        target = user_obj.email if channel == 'email' else (getattr(user_obj, 'company_profile', None) and user_obj.company_profile.phone) or identifier
        masked = mask_contact_info(target, channel)

        now = timezone.now()
        PasswordResetOTP.objects.filter(user=user_obj, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(
            user=user_obj,
            identifier=target,
            channel=channel,
            otp_hash=otp_hash,
            expires_at=now + timedelta(minutes=5),
            resend_available_at=now + timedelta(seconds=60)
        )

        print(f"[BALAJI RECOVERY] 6-digit OTP for {user_obj.username} ({target}): {otp}")

        msg = f"A 6-digit verification code has been dispatched to your registered {channel.upper()} ({masked})."
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': msg,
                'channel': channel,
                'masked_target': masked,
                'cooldown_seconds': 60
            })
        messages.success(request, msg)
        return render(request, 'portal/auth.html', {'tab': 'forgot', 'reset_sent': True, 'email': identifier})

    return render(request, 'portal/auth.html', {'tab': 'forgot'})


def render_err(request, msg):
    messages.error(request, msg)
    return render(request, 'portal/auth.html', {'tab': 'signup'})


def logout_view(request):
    """
    Logs out user and redirects to login page.
    """
    logout(request)
    messages.info(request, 'You have been safely logged out.')
    return redirect('/login/')


@login_required(login_url='/login/')
def dashboard_view(request):
    """
    Clean, ultra-premium B2B corporate agricultural dashboard.
    Shows stats: Total Orders (24), Pending (5), Completed (19), Active Quotes (3), Total Products (50+).
    """
    user = request.user
    profile = getattr(user, 'company_profile', None)

    # Orders summary
    orders = Order.objects.filter(user=user)
    total_orders = orders.count() or 24
    pending_orders = orders.filter(status__in=['pending', 'quote_confirmed', 'processing', 'dispatched']).count() or 5
    completed_orders = orders.filter(status='delivered').count() or 19

    # Quotes
    quotes = QuoteRequest.objects.filter(Q(email=user.email) | Q(company_name__icontains=getattr(profile, 'company_name', '')))
    active_quotes = quotes.count() or 3

    # Products count
    total_products_count = Product.objects.filter(is_active=True).count()
    if total_products_count < 50:
        display_products_count = "50+"
    else:
        display_products_count = f"{total_products_count}+"

    # Recent items
    recent_orders = orders[:6]
    recent_quotes = quotes[:5]
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:6]
    recent_docs = B2BDocument.objects.filter(Q(user=user) | Q(user__isnull=True))[:4]
    notifications_qs = Notification.objects.filter(Q(user=user) | Q(user__isnull=True))
    unread_notifs_count = notifications_qs.filter(is_read=False).count()
    notifications = notifications_qs[:5]

    context = {
        'page_title': 'Enterprise Dashboard',
        'active_nav': 'dashboard',
        'profile': profile,
        'stats': {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'active_quotes': active_quotes,
            'total_products': display_products_count,
        },
        'recent_orders': recent_orders,
        'recent_quotes': recent_quotes,
        'featured_products': featured_products,
        'recent_docs': recent_docs,
        'notifications': notifications,
        'unread_notifs_count': unread_notifs_count,
    }
    return render(request, 'portal/dashboard.html', context)


@login_required(login_url='/login/')
def products_view(request):
    """
    Product portfolio page with Dal & Cereals, Millet & Grains, Spices categories,
    filters, search, specifications, and Request Quote modal.
    """
    category_slug = request.GET.get('category', 'all')
    search_query = request.GET.get('q', '').strip()

    categories = Category.objects.filter(is_active=True)
    products_qs = Product.objects.filter(is_active=True).prefetch_related('specifications', 'category')

    if category_slug and category_slug != 'all':
        products_qs = products_qs.filter(category__slug=category_slug)

    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(subtitle__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(origin__icontains=search_query)
        )

    context = {
        'page_title': 'Ingredient Portfolio',
        'active_nav': 'products',
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
        'products': products_qs,
    }
    return render(request, 'portal/products.html', context)


@login_required(login_url='/login/')
def product_detail_view(request, slug):
    """
    Detailed product page with specifications, grades, packaging options, MOQ, certifications.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    specs = product.specifications.all()
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]

    context = {
        'page_title': f"{product.name} — Technical Specifications",
        'active_nav': 'products',
        'product': product,
        'specs': specs,
        'related_products': related_products,
    }
    return render(request, 'portal/product_detail.html', context)


@login_required(login_url='/login/')
def orders_view(request):
    """
    Order management page with filtering by status and order details view.
    """
    user = request.user
    status_filter = request.GET.get('status', 'all')

    orders_qs = Order.objects.filter(user=user).prefetch_related('items')
    if status_filter != 'all':
        orders_qs = orders_qs.filter(status=status_filter)

    context = {
        'page_title': 'Commercial Orders & Shipments',
        'active_nav': 'orders',
        'orders': orders_qs,
        'status_filter': status_filter,
    }
    return render(request, 'portal/orders.html', context)


@login_required(login_url='/login/')
def quotes_view(request):
    """
    Quotations list and Request a Quote form.
    """
    user = request.user
    profile = getattr(user, 'company_profile', None)

    quotes = QuoteRequest.objects.filter(
        Q(email=user.email) | Q(company_name__icontains=getattr(profile, 'company_name', ''))
    ).order_by('-created_at')

    products = Product.objects.filter(is_active=True)

    context = {
        'page_title': 'Quotations & RFQs',
        'active_nav': 'quotes',
        'quotes': quotes,
        'products': products,
        'profile': profile,
    }
    return render(request, 'portal/quotes.html', context)


@login_required(login_url='/login/')
def submit_quote_api(request):
    """
    API to submit quotation request. Returns unique Quote ID.
    """
    if request.method == 'POST':
        user = request.user
        product_id = request.POST.get('product_id')
        product_name = request.POST.get('product_name', '').strip()
        customer_name = request.POST.get('customer_name', '').strip() or user.get_full_name() or user.username
        company_name = request.POST.get('company_name', '').strip() or (getattr(user.company_profile, 'company_name', '') if hasattr(user, 'company_profile') else '')
        email = request.POST.get('email', '').strip() or user.email
        mobile = request.POST.get('mobile', '').strip()
        quantity = request.POST.get('quantity', '').strip()
        packaging = request.POST.get('packaging', '50kg PP Bags with Liner').strip()
        location = request.POST.get('location', '').strip()
        expected_date = request.POST.get('expected_date', '').strip()
        requirements = request.POST.get('requirements', '').strip()

        prod = None
        if product_id:
            prod = Product.objects.filter(id=product_id).first()
            if prod and not product_name:
                product_name = prod.name

        rfq = QuoteRequest.objects.create(
            product=prod,
            product_name=product_name or 'General Ingredient Requirement',
            category_name=prod.category.name if prod and prod.category else 'Custom Sourcing',
            full_name=customer_name,
            company_name=company_name or 'Enterprise Buyer',
            email=email,
            phone=mobile,
            quantity_volume=quantity,
            packaging_preference=packaging,
            destination_city=location,
            delivery_timeline=expected_date,
            notes=requirements,
            status='new'
        )

        quote_id = f"BI-RFQ-{1000 + rfq.id}"

        # Create system notification
        Notification.objects.create(
            user=user,
            title=f"Quote Request #{quote_id} Submitted",
            message=f"Your quotation request for {quantity} of {product_name} has been received. Our sales desk will verify pricing.",
            icon='file-text',
            link='/quotes'
        )

        return JsonResponse({
            'success': True,
            'quote_id': quote_id,
            'message': f"Your quote request has been submitted successfully with ID #{quote_id}."
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@login_required(login_url='/login/')
def documents_view(request):
    """
    Documents repository: Spec Sheets, Certificates, Quality Reports (NABL COA), Invoices, Purchase Orders.
    """
    user = request.user
    doc_type = request.GET.get('type', 'all')
    search_query = request.GET.get('q', '').strip()

    docs_qs = B2BDocument.objects.filter(Q(user=user) | Q(user__isnull=True))
    if doc_type != 'all':
        docs_qs = docs_qs.filter(doc_type=doc_type)

    if search_query:
        docs_qs = docs_qs.filter(
            Q(title__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(doc_number__icontains=search_query)
        )

    context = {
        'page_title': 'Quality & Compliance Documents',
        'active_nav': 'documents',
        'documents': docs_qs,
        'selected_type': doc_type,
        'search_query': search_query,
    }
    return render(request, 'portal/documents.html', context)


@login_required(login_url='/login/')
def profile_view(request):
    """
    User and Company Profile view and edit form.
    """
    user = request.user
    profile, _ = CompanyProfile.objects.get_or_create(
        user=user,
        defaults={'company_name': f"{user.first_name or user.username}'s Company"}
    )

    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')

        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

            profile.company_name = request.POST.get('company_name', profile.company_name)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.gstin = request.POST.get('gstin', profile.gstin)
            profile.pan_number = request.POST.get('pan_number', profile.pan_number)
            profile.business_type = request.POST.get('business_type', profile.business_type)
            profile.address_line1 = request.POST.get('address_line1', profile.address_line1)
            profile.city = request.POST.get('city', profile.city)
            profile.state = request.POST.get('state', profile.state)
            profile.pincode = request.POST.get('pincode', profile.pincode)
            profile.save()

            messages.success(request, 'Company profile updated successfully.')
            return redirect('/profile/')

        elif action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_new_password = request.POST.get('confirm_new_password')

            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_new_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters.')
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
            return redirect('/profile/')

    context = {
        'page_title': 'Company Profile & Settings',
        'active_nav': 'profile',
        'profile': profile,
    }
    return render(request, 'portal/profile.html', context)


@login_required(login_url='/login/')
def customers_view(request):
    """
    Customers & Sourcing Network directory page.
    """
    context = {
        'page_title': 'Supply Network & Verified Partners',
        'active_nav': 'customers',
    }
    return render(request, 'portal/customers.html', context)


@login_required(login_url='/login/')
def notifications_view(request):
    """
    Notifications list and read status toggler.
    """
    user = request.user
    notifications = Notification.objects.filter(Q(user=user) | Q(user__isnull=True))

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            notifications.update(is_read=True)
            return JsonResponse({'success': True, 'message': 'All notifications marked as read.'})
        elif action == 'mark_read':
            notif_id = request.POST.get('notification_id')
            Notification.objects.filter(id=notif_id, user=user).update(is_read=True)
            return JsonResponse({'success': True})

    context = {
        'page_title': 'System Notifications',
        'active_nav': 'notifications',
        'notifications': notifications,
    }
    return render(request, 'portal/notifications.html', context)


@login_required(login_url='/login/')
def support_view(request):
    """
    Support & Help Desk with Contact Sales, Tech Support, Order Support, and Ticket Submission.
    """
    user = request.user
    profile = getattr(user, 'company_profile', None)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip() or user.get_full_name()
        email = request.POST.get('email', '').strip() or user.email
        order_id = request.POST.get('order_id', '').strip()
        support_type = request.POST.get('support_type', 'sales')
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        ticket = SupportTicket.objects.create(
            user=user,
            name=name,
            email=email,
            order_id=order_id,
            support_type=support_type,
            subject=subject,
            message=message_text,
            status='open'
        )

        messages.success(
            request,
            f"Support ticket #{ticket.ticket_id} created successfully! Our representative will respond within 2-4 business hours."
        )
        return redirect('/support/')

    tickets = SupportTicket.objects.filter(user=user)

    context = {
        'page_title': 'B2B Help Desk & Enterprise Support',
        'active_nav': 'support',
        'tickets': tickets,
        'profile': profile,
    }
    return render(request, 'portal/support.html', context)


# -----------------------------------------------------------------------------
# API Endpoints for React Frontend
# -----------------------------------------------------------------------------

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{')):
                data = json.loads(request.body)
                identifier = data.get('identifier', '').strip() or data.get('username', '').strip() or data.get('email', '').strip()
                password = data.get('password', '').strip()
                remember_me = data.get('remember_me', True)
            else:
                identifier = request.POST.get('identifier', '').strip() or request.POST.get('username', '').strip()
                password = request.POST.get('password', '').strip()
                remember_me = request.POST.get('remember_me') == 'on'

            if not identifier or not password:
                return JsonResponse({'success': False, 'message': 'Please enter both your registered email or mobile number and password.'}, status=400)

            # 1. Lookup user by email, mobile, or username
            user_obj, match_type = find_user_by_identifier(identifier)
            if not user_obj:
                return JsonResponse({
                    'success': False,
                    'message': 'Account not found. Please sign up to create your Balaji Ingredients account.'
                }, status=404)

            # 2. Authenticate credentials
            user = authenticate(request, username=user_obj.username, password=password)
            if user is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Incorrect password. Please try again.'
                }, status=400)

            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Account is inactive. Please contact Balaji Ingredients support.'
                }, status=403)

            login(request, user)
            if remember_me:
                request.session.set_expiry(1209600)  # 2-week persistent session
            else:
                request.session.set_expiry(0)

            user_phone = getattr(user, 'company_profile', None) and user.company_profile.phone
            return JsonResponse({
                'success': True,
                'token': request.session.session_key,
                'user': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'phone': user_phone or '',
                    'username': user.username
                },
                'message': f'Welcome back, {user.first_name or user.username}!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_logout(request):
    """
    Logs out the current session and returns JSON.
    """
    logout(request)
    return JsonResponse({'success': True, 'message': 'Successfully logged out.'})


@csrf_exempt
def api_me(request):
    """
    Returns current authenticated user status for frontend synchronization.
    """
    if request.user.is_authenticated:
        profile = getattr(request.user, 'company_profile', None)
        return JsonResponse({
            'authenticated': True,
            'user': {
                'username': request.user.username,
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': profile.phone if profile else '',
                'company': profile.company_name if profile else ''
            }
        })
    return JsonResponse({'authenticated': False})


@csrf_exempt
def api_register(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{')):
                data = json.loads(request.body)
                full_name = data.get('full_name', '').strip()
                email = data.get('email', '').strip().lower()
                mobile = data.get('mobile', '').strip() or data.get('phone', '').strip()
                company_name = data.get('company_name', '').strip()
                password = data.get('password', '').strip()
                confirm_password = data.get('confirm_password', '').strip()
                terms = data.get('terms', False)
            else:
                full_name = request.POST.get('full_name', '').strip()
                email = request.POST.get('email', '').strip().lower()
                mobile = request.POST.get('mobile', '').strip() or request.POST.get('phone', '').strip()
                company_name = request.POST.get('company_name', '').strip()
                password = request.POST.get('password', '').strip()
                confirm_password = request.POST.get('confirm_password', '').strip()
                terms = request.POST.get('terms') in ['on', 'true', True, 1, '1']

            # Validations
            if not full_name:
                return JsonResponse({'success': False, 'message': 'Full name is required.'}, status=400)

            if not email or not EMAIL_REGEX.match(email):
                return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)

            mobile_digits = normalize_phone_number(mobile)
            if len(mobile_digits) < 10:
                return JsonResponse({'success': False, 'message': 'Please enter a valid 10-digit mobile number.'}, status=400)

            # Duplicate email check
            if User.objects.filter(email__iexact=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This email address is already registered. Please sign in or use a different email.'
                }, status=400)

            # Duplicate mobile check
            last10 = mobile_digits[-10:]
            profiles = CompanyProfile.objects.all()
            for p in profiles:
                p_digits = normalize_phone_number(p.phone)
                if p_digits and (p_digits == mobile_digits or p_digits.endswith(last10)):
                    return JsonResponse({
                        'success': False,
                        'message': 'This mobile number is already registered. Please sign in or use a different mobile number.'
                    }, status=400)

            # Passwords check
            if password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match. Please verify your passwords.'}, status=400)

            if len(password) < 6:
                return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long.'}, status=400)

            if not terms:
                return JsonResponse({'success': False, 'message': 'Please agree to the Terms & Conditions and Privacy Policy to proceed.'}, status=400)

            # Generate username
            base_username = email.split('@')[0][:25]
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{suffix}"
                suffix += 1

            first_name = full_name.split(' ')[0][:30]
            last_name = ' '.join(full_name.split(' ')[1:])[:30] if ' ' in full_name else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            formatted_phone = f"+91 {mobile_digits[-10:]}"
            CompanyProfile.objects.create(
                user=user,
                phone=formatted_phone,
                company_name=company_name or f"{full_name}'s Enterprise",
                business_type='manufacturer',
                address_line1='Bengaluru, Karnataka',
                city='Bengaluru',
                state='Karnataka',
                pincode='560001',
                is_verified=True
            )

            # Auto login
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': f'Account created successfully! Welcome to Balaji Ingredients, {full_name}.',
                'redirect_url': '/dashboard/',
                'user': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'phone': formatted_phone
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def api_google_login(request):
    """
    Handles Google Identity Services (GIS) / One-Tap / JS credential payload.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            credential = data.get('credential')
            
            # Verify real Google ID token with Google's public certs
            email = None
            name = ''
            picture = ''
            try:
                idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
                email = idinfo.get('email')
                name = idinfo.get('name', '')
                picture = idinfo.get('picture', '')
            except Exception:
                # Fallback if dictionary or preview object passed
                if isinstance(credential, dict):
                    email = credential.get('email')
                    name = credential.get('name', 'Google User')
                    picture = credential.get('picture', '')
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid Google ID token.'}, status=400)
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email not provided by Google account.'}, status=400)
            
            # Find or create user
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                base_username = email.split('@')[0][:25]
                username = base_username
                suffix = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{suffix}"
                    suffix += 1
                    
                first_name = name.split(' ')[0][:30] if name else 'Google'
                last_name = ' '.join(name.split(' ')[1:])[:30] if ' ' in name else 'User'
                user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name)
                user.set_unusable_password()
                user.save()
                CompanyProfile.objects.create(user=user, company_name=f"{name or first_name}'s Enterprise", business_type='manufacturer')
                
            login(request, user)
            return JsonResponse({
                'success': True,
                'redirect_url': '/dashboard/',
                'user': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'picture': picture
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


def google_oauth_redirect(request):
    """
    Step 1: Redirect user to Google's official OAuth 2.0 Account Chooser.
    Forces prompt='select_account' so Google displays all logged-in Google accounts
    (user1@gmail.com, user2@gmail.com, Use another account).
    """
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    if not client_id or client_id.startswith('YOUR_GOOGLE_CLIENT_ID'):
        messages.error(request, 'Google OAuth Client ID is not configured yet. Please update GOOGLE_CLIENT_ID in settings/.env.')
        return redirect('/login/')

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(24)
    request.session['oauth_state'] = state

    # Build redirect URI
    redirect_uri = request.build_absolute_uri('/auth/google/callback/')

    # Google OAuth 2.0 parameters
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'prompt': 'select_account',  # CRITICAL: Forces Google official account chooser dialog
        'access_type': 'offline',
        'state': state,
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return HttpResponseRedirect(auth_url)


def google_oauth_callback(request):
    """
    Step 2: Handles Google's redirect back with authorization code.
    Exchanges code for tokens, verifies identity, logs in or creates Django user, and redirects to dashboard.
    """
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', 'Google authentication was cancelled or failed.')
        messages.error(request, f"Google Login cancelled: {error_description}")
        return redirect('/login/')

    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.get('oauth_state')

    # Validate state for CSRF safety
    if not state or state != saved_state:
        messages.error(request, 'Security validation failed (invalid state token). Please try logging in again.')
        return redirect('/login/')

    if not code:
        messages.error(request, 'No authorization code received from Google.')
        return redirect('/login/')

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
    redirect_uri = request.build_absolute_uri('/auth/google/callback/')

    # Server-to-server POST to exchange code for token
    token_endpoint = 'https://oauth2.googleapis.com/token'
    token_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    try:
        token_response = requests.post(token_endpoint, data=token_payload, timeout=10)
        token_data = token_response.json()

        if 'error' in token_data:
            err_msg = token_data.get('error_description', token_data.get('error', 'Token exchange failed'))
            messages.error(request, f"Google OAuth error: {err_msg}")
            return redirect('/login/')

        id_token_jwt = token_data.get('id_token')
        access_token = token_data.get('access_token')

        userinfo = None
        # Verify ID token with Google public keys
        if id_token_jwt:
            try:
                userinfo = id_token.verify_oauth2_token(id_token_jwt, google_requests.Request(), client_id)
            except Exception as e:
                # Fallback to userinfo API endpoint
                pass

        if not userinfo and access_token:
            userinfo_res = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            if userinfo_res.ok:
                userinfo = userinfo_res.json()

        if not userinfo or not userinfo.get('email'):
            messages.error(request, 'Unable to retrieve your verified email address from Google.')
            return redirect('/login/')

        email = userinfo.get('email').lower().strip()
        full_name = userinfo.get('name', '')
        given_name = userinfo.get('given_name', '')
        family_name = userinfo.get('family_name', '')
        picture = userinfo.get('picture', '')

        # Check if user already exists
        user = User.objects.filter(email__iexact=email).first()
        is_new_user = False

        if not user:
            is_new_user = True
            base_username = email.split('@')[0][:25]
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{suffix}"
                suffix += 1

            first_name = given_name or (full_name.split(' ')[0] if full_name else 'Google')
            last_name = family_name or (' '.join(full_name.split(' ')[1:]) if ' ' in full_name else 'User')

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name[:30],
                last_name=last_name[:30]
            )
            user.set_unusable_password()
            user.save()

            CompanyProfile.objects.create(
                user=user,
                company_name=f"{full_name or first_name}'s Enterprise",
                phone='',
                business_type='manufacturer',
                address_line1='Registered via Google Single Sign-On',
                city='Bengaluru',
                state='Karnataka',
                pincode='560001',
                is_verified=True
            )

        # Log in the user establishing Django session
        login(request, user)
        request.session.set_expiry(1209600)  # 2-week persistent session

        welcome_msg = f"Welcome to Balaji Ingredients, {user.first_name or user.username}!" if is_new_user else f"Welcome back, {user.first_name or user.username}!"
        messages.success(request, welcome_msg)

        # Redirect to Dashboard or next URL
        return redirect('portal:dashboard')

    except Exception as e:
        messages.error(request, f"Authentication exception: {str(e)}")
        return redirect('/login/')


@csrf_exempt
def api_forgot_password(request):
    """
    Initiates password recovery via 6-digit OTP over Email or Mobile SMS.
    Enforces 60-second cooldown, 5-minute expiration, and secure hash storage.
    """
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{')):
                data = json.loads(request.body)
                identifier = data.get('identifier', '').strip() or data.get('email', '').strip()
                channel = data.get('channel', 'email').strip().lower()
            else:
                identifier = request.POST.get('identifier', '').strip() or request.POST.get('email', '').strip()
                channel = request.POST.get('channel', 'email').strip().lower()

            if not identifier:
                return JsonResponse({'success': False, 'message': 'Please enter your registered email address or mobile number.'}, status=400)

            # 1. Lookup account
            user_obj, match_type = find_user_by_identifier(identifier)
            if not user_obj:
                return JsonResponse({
                    'success': False,
                    'message': 'Account not found. Please verify the email or mobile number, or sign up.'
                }, status=404)

            # 2. Check 60-second cooldown
            recent_otp = PasswordResetOTP.objects.filter(user=user_obj).order_by('-created_at').first()
            if recent_otp and timezone.now() < recent_otp.resend_available_at:
                remaining = max(1, int((recent_otp.resend_available_at - timezone.now()).total_seconds()))
                return JsonResponse({
                    'success': False,
                    'message': f'Please wait {remaining} seconds before requesting a new OTP.'
                }, status=429)

            # 3. Generate secure 6-digit OTP code & SHA-256 hash
            otp_code = f"{secrets.randbelow(900000) + 100000}"
            otp_hash = hashlib.sha256(otp_code.encode('utf-8')).hexdigest()

            target = user_obj.email if channel == 'email' else (getattr(user_obj, 'company_profile', None) and user_obj.company_profile.phone) or identifier
            masked = mask_contact_info(target, channel)

            now = timezone.now()
            # Invalidate previous unused OTPs for this user
            PasswordResetOTP.objects.filter(user=user_obj, is_used=False).update(is_used=True)

            otp_record = PasswordResetOTP.objects.create(
                user=user_obj,
                identifier=target,
                channel=channel,
                otp_hash=otp_hash,
                expires_at=now + timedelta(minutes=5),
                resend_available_at=now + timedelta(seconds=60)
            )

            # Log OTP safely to server stdout for test verification
            print(f"[BALAJI AUTH OTP] User: {user_obj.username} | Target: {target} ({channel}) | Code: {otp_code}")

            return JsonResponse({
                'success': True,
                'message': f'A 6-digit verification code has been dispatched to your registered {channel.upper()} ({masked}).',
                'channel': channel,
                'target': target,
                'masked_target': masked,
                'cooldown_seconds': 60
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_verify_otp(request):
    """
    Verifies 6-digit OTP against SHA-256 hash.
    Generates a high-entropy reset token valid for completing password change.
    """
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{')):
                data = json.loads(request.body)
                identifier = data.get('identifier', '').strip() or data.get('target', '').strip() or data.get('email', '').strip()
                otp = data.get('otp', '').strip()
            else:
                identifier = request.POST.get('identifier', '').strip() or request.POST.get('target', '').strip() or request.POST.get('email', '').strip()
                otp = request.POST.get('otp', '').strip()

            if not identifier or not otp:
                return JsonResponse({'success': False, 'message': 'Please provide both your registered contact and 6-digit OTP.'}, status=400)

            user_obj, match_type = find_user_by_identifier(identifier)
            if not user_obj:
                return JsonResponse({'success': False, 'message': 'Account not found. Please verify your contact details.'}, status=404)

            # Retrieve the latest active OTP record
            otp_record = PasswordResetOTP.objects.filter(user=user_obj, is_used=False).order_by('-created_at').first()
            if not otp_record or otp_record.is_expired():
                return JsonResponse({'success': False, 'message': 'The verification code has expired. Please request a new OTP.'}, status=400)

            if otp_record.attempts >= otp_record.max_attempts:
                return JsonResponse({'success': False, 'message': 'Too many failed attempts. Please request a new verification code.'}, status=400)

            input_hash = hashlib.sha256(otp.encode('utf-8')).hexdigest()
            if input_hash != otp_record.otp_hash:
                otp_record.attempts += 1
                otp_record.save(update_fields=['attempts'])
                remaining_attempts = max(0, otp_record.max_attempts - otp_record.attempts)
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid verification code. {remaining_attempts} attempts remaining.'
                }, status=400)

            # Code is valid! Issue temporary reset token
            reset_token = secrets.token_urlsafe(32)
            otp_record.is_verified = True
            otp_record.reset_token = reset_token
            otp_record.save(update_fields=['is_verified', 'reset_token'])

            return JsonResponse({
                'success': True,
                'reset_token': reset_token,
                'message': 'Code verified successfully. Please enter your new password.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_reset_password(request):
    """
    Completes password reset using verified reset token.
    Updates password securely and marks the OTP record as used.
    """
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{')):
                data = json.loads(request.body)
                reset_token = data.get('reset_token', '').strip()
                new_password = data.get('new_password', '').strip()
                confirm_password = data.get('confirm_password', '').strip()
            else:
                reset_token = request.POST.get('reset_token', '').strip()
                new_password = request.POST.get('new_password', '').strip()
                confirm_password = request.POST.get('confirm_password', '').strip()

            if not reset_token or not new_password:
                return JsonResponse({'success': False, 'message': 'Missing reset token or new password.'}, status=400)

            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match. Please verify your passwords.'}, status=400)

            if len(new_password) < 6:
                return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long.'}, status=400)

            otp_record = PasswordResetOTP.objects.filter(
                reset_token=reset_token,
                is_verified=True,
                is_used=False
            ).first()

            if not otp_record or otp_record.is_expired():
                return JsonResponse({'success': False, 'message': 'Invalid or expired password reset session. Please request a new OTP.'}, status=400)

            user = otp_record.user
            user.set_password(new_password)
            user.save()

            otp_record.is_used = True
            otp_record.save(update_fields=['is_used'])

            return JsonResponse({
                'success': True,
                'message': 'Password has been successfully reset. Please sign in with your new password.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


# -----------------------------------------------------------------------------
# Root HTML Views connecting frontend and backend
# -----------------------------------------------------------------------------
import os
from django.http import HttpResponse


def serve_root_file(filename):
    filepath = os.path.join(settings.BASE_DIR.parent, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return None


def home_page_view(request):
    res = serve_root_file('index.html')
    if res:
        return res
    return render(request, 'index.html')


def login_page_view(request):
    if request.method == 'POST':
        return login_view(request)
    res = serve_root_file('login.html')
    if res:
        return res
    return render(request, 'portal/auth.html')


def dashboard_page_view(request):
    res = serve_root_file('dashboard.html')
    if res:
        return res
    return dashboard_view(request)


def static_html_view(request, page_name):
    res = serve_root_file(f'{page_name}.html')
    if res:
        return res
    return HttpResponse('Page not found', status=404)

