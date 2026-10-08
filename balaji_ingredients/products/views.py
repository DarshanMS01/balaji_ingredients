"""
products/views.py
Views for Catalog, Category Detail, Product Detail, and RFQ submission.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Category, Product, QuoteRequest
from .forms import QuoteRequestForm


def catalog_list(request):
    """Product catalog with category filtering and keyword search."""
    categories = Category.objects.filter(is_active=True).prefetch_related('products')
    products = Product.objects.filter(is_active=True).select_related('category')

    selected_category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()

    if selected_category_slug:
        products = products.filter(category__slug=selected_category_slug)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(subtitle__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category_slug,
        'search_query': search_query,
        'page_title': 'Ingredient Catalog',
    }
    return render(request, 'products/catalog.html', context)


def category_detail(request, category_slug):
    """Category detail view with all products under this category."""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    products = category.products.filter(is_active=True)
    all_categories = Category.objects.filter(is_active=True)

    context = {
        'category': category,
        'products': products,
        'categories': all_categories,
        'page_title': category.name,
    }
    return render(request, 'products/catalog.html', context)


def product_detail(request, category_slug, product_slug):
    """Detailed view of an individual ingredient with specifications and RFQ modal."""
    product = get_object_or_404(
        Product,
        slug=product_slug,
        category__slug=category_slug,
        is_active=True
    )
    specifications = product.specifications.all()
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:3]

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            rfq = form.save(commit=False)
            rfq.product = product
            rfq.product_name = product.name
            rfq.category_name = product.category.name
            rfq.save()
            messages.success(
                request,
                f"Quotation request for {product.name} submitted successfully! "
                f"Reference #{rfq.id:04d}. Our sales team will send a formal quote within 4 business hours."
            )
            return redirect(product.get_absolute_url())
    else:
        form = QuoteRequestForm(initial={'product_id': product.id})

    context = {
        'product': product,
        'specifications': specifications,
        'related_products': related_products,
        'form': form,
        'page_title': product.name,
    }
    return render(request, 'products/product_detail.html', context)


def quote_request_view(request):
    """Standalone general RFQ page where clients can pick products and request quotes."""
    selected_product_id = request.GET.get('product')
    selected_product = None
    if selected_product_id:
        try:
            selected_product = Product.objects.get(id=selected_product_id, is_active=True)
        except Product.DoesNotExist:
            pass

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            rfq = form.save(commit=False)
            prod_id = request.POST.get('product_id')
            if prod_id:
                try:
                    product = Product.objects.get(id=prod_id)
                    rfq.product = product
                    rfq.product_name = product.name
                    rfq.category_name = product.category.name
                except Product.DoesNotExist:
                    pass
            rfq.save()
            messages.success(
                request,
                f"Thank you! Your quote request #{rfq.id:04d} has been received. "
                "Our commercial desk will review your requirement and deliver a formal quotation."
            )
            return redirect('products:quote_request')
    else:
        initial = {}
        if selected_product:
            initial['product_id'] = selected_product.id
        form = QuoteRequestForm(initial=initial)

    all_products = Product.objects.filter(is_active=True).select_related('category')
    context = {
        'form': form,
        'selected_product': selected_product,
        'all_products': all_products,
        'page_title': 'Request a Formal B2B Quotation',
    }
    return render(request, 'products/quote_request.html', context)


def buy_product_view(request, product_id):
    """Direct commercial purchase flow with server-side calculation and order generation."""
    from decimal import Decimal
    from django.contrib.auth.models import User
    from django.contrib.auth import login
    from django.http import JsonResponse
    from portal.models import Order, OrderItem, CompanyProfile

    product = get_object_or_404(Product, id=product_id, is_active=True)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        company_name = request.POST.get('company_name', '').strip() or full_name
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip() or request.POST.get('address', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        gstin = request.POST.get('gstin', '').strip()
        quality = request.POST.get('quality', 'Standard').strip()
        custom_quality_notes = request.POST.get('custom_quality_notes', '').strip()
        unit = request.POST.get('unit', 'kg').strip().upper()
        notes = request.POST.get('notes', '').strip()
        is_quote = request.POST.get('is_quote_request') in ['true', 'True', '1', 1]
        
        # Payment details
        payment_method = request.POST.get('payment_method', 'cod').strip().lower()
        if payment_method not in ['cod', 'upi']:
            payment_method = 'cod'
        
        upi_utr_number = request.POST.get('upi_utr', '').strip() or request.POST.get('upi_utr_number', '').strip()
        
        # Verification Pending for UPI, COD for Cash on Delivery
        if payment_method == 'upi':
            initial_payment_status = 'verification_pending'
        else:
            initial_payment_status = 'cod'

        try:
            raw_qty = Decimal(request.POST.get('quantity', '100'))
            if raw_qty <= 0:
                raw_qty = Decimal('100')
        except Exception:
            raw_qty = Decimal('100')

        # Multiplier conversion to KG
        multiplier = Decimal('1')
        if 'QUINTAL' in unit:
            multiplier = Decimal('100')
        elif 'TON' in unit:
            multiplier = Decimal('1000')

        quantity_kg = raw_qty * multiplier

        # SERVER-SIDE PRICE RECALCULATION (Do not trust client-sent totals)
        authoritative_unit_price = product.unit_price
        subtotal = (quantity_kg * authoritative_unit_price).quantize(Decimal('0.01'))
        tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))  # 5% GST
        delivery_charges = Decimal('0.00')  # Confirmed separately
        total_amount = subtotal + delivery_charges

        full_address_parts = [p for p in [address_line1, address_line2, city, state, f"PIN: {pincode}" if pincode else ''] if p]
        full_address = ", ".join(full_address_parts)

        # Associate or create user account for buyer
        if request.user.is_authenticated:
            user = request.user
        else:
            username = email.split('@')[0] if email else f"buyer_{phone}"
            user = User.objects.filter(email=email).first() if email else None
            if not user and username:
                user = User.objects.filter(username=username).first()
            if not user:
                import uuid
                rnd_user = f"user_{uuid.uuid4().hex[:6]}"
                user = User.objects.create_user(
                    username=rnd_user,
                    email=email or f"{rnd_user}@balaji-temp.com",
                    password=User.objects.make_random_password(),
                    first_name=full_name[:30]
                )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Company profile update/create
        profile, _ = CompanyProfile.objects.get_or_create(
            user=user,
            defaults={
                'company_name': company_name,
                'phone': phone or 'Not provided',
                'address_line1': address_line1 or 'Main St',
                'address_line2': address_line2,
                'city': city or 'City',
                'state': state or 'State',
                'pincode': pincode or '000000',
                'gstin': gstin,
            }
        )

        # Create Commercial Order with BI-2026-000123 format
        order = Order.objects.create(
            user=user,
            customer_name=full_name,
            company_name=company_name,
            email=email,
            phone=phone,
            delivery_address=full_address,
            city=city,
            state=state,
            pincode=pincode,
            gstin=gstin,
            quality=quality,
            custom_quality_notes=custom_quality_notes,
            is_quote_request=is_quote,
            payment_method=payment_method,
            payment_status=initial_payment_status,
            upi_utr_number=upi_utr_number if payment_method == 'upi' else '',
            status='pending',
            subtotal=subtotal,
            delivery_charges=delivery_charges,
            tax_amount=tax_amount,
            total_amount=total_amount,
            shipping_address=f"Recipient: {full_name} ({company_name})\nPhone: {phone}\nEmail: {email}\nShipping Address: {full_address}",
            customer_notes=notes,
            additional_requirements=notes,
        )

        # Create Order Item
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=quantity_kg,
            unit=f"{raw_qty} {unit} ({quantity_kg} KG)",
            packaging=product.packaging_options,
            unit_price=authoritative_unit_price,
            total_price=subtotal,
        )

        if is_ajax:
            return JsonResponse({
                'success': True,
                'order_id': order.order_number,
                'product': product.name,
                'quality': quality,
                'quantity': f"{raw_qty} {unit} ({quantity_kg} KG)",
                'price_per_kg': float(authoritative_unit_price),
                'subtotal': float(subtotal),
                'delivery_status': 'To be confirmed by Balaji Ingredients',
                'total_amount': float(total_amount),
                'payment_method': 'UPI' if payment_method == 'upi' else 'Cash on Delivery',
                'payment_status': 'Verification Pending' if payment_method == 'upi' else 'COD',
                'upi_utr': upi_utr_number,
                'message': 'Order submitted successfully.'
            })

        messages.success(
            request,
            f"Order #{order.order_number} for {raw_qty} {unit} of {product.name} placed successfully! Total: ₹{total_amount:,.2f}"
        )

        return redirect('portal:orders')

    # GET request render standalone buy page
    context = {
        'product': product,
        'page_title': f"Buy {product.name}",
    }
    return render(request, 'products/buy_product.html', context)


def payment_config_api(request):
    """API endpoint to get active dynamic UPI payment settings."""
    from django.http import JsonResponse
    from portal.models import PaymentConfig
    config = PaymentConfig.get_active_config()
    qr_url = config.qr_image.url if config.qr_image else config.qr_image_url
    return JsonResponse({
        'business_upi_id': config.business_upi_id,
        'payee_name': config.payee_name,
        'qr_image_url': qr_url,
    })


