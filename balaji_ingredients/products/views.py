"""
products/views.py
Views for Catalog, Category Detail, Product Detail, Session Cart, Checkout, and RFQ submission.
"""

import re
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Category, Product, QuoteRequest
from .forms import QuoteRequestForm


# ---------------------------------------------------------------------------
# Packaging size parsing, product image gallery, and session cart helpers
# ---------------------------------------------------------------------------

CART_SESSION_KEY = 'cart'
MAX_CART_LINE_QTY = 500  # sanity cap per cart line (packs)

# Reuses existing site images per product (no new assets invented).
# The FIRST entry is the exact photograph the home page "Signature Four"
# cards display, so the product detail page shows the same image.
PRODUCT_IMAGE_CANDIDATES = {
    'red-chilli-powder': ['images/chilli_product.jpg', 'images/chilli-powder.jpg'],
    'malabar-black-pepper': ['images/pepper_product.jpg'],
    'green-cardamom': ['images/cardamom_product.jpg'],
    'stone-ground-ragi-flour': ['images/ragi_product.jpg', 'images/ragi_flour.jpg'],
    'premium-sortex-toor-dal': ['images/dal-pulses.jpg'],
    'moong-dal-mogar': ['images/dal-pulses.jpg'],
    'unpolished-chana-dal': ['images/dal-pulses.jpg'],
    'sharbati-lokwan-wheat': ['images/cereals.jpg'],
    'sona-masoori-rice': ['images/cereals.jpg'],
}


def parse_packaging_sizes(packaging_text):
    """Extract discrete packaging weights in kg from the packaging description text."""
    sizes = []
    for match in re.finditer(r'(\d+(?:\.\d+)?)\s*kg', packaging_text or '', re.IGNORECASE):
        try:
            value = Decimal(match.group(1))
        except InvalidOperation:
            continue
        if value > 0 and value not in sizes:
            sizes.append(value)
    return sorted(sizes) or [Decimal('1')]


def _resolve_static_image(rel_path):
    """
    Return a URL for an image that actually exists on disk.
    The original root /images copy (the exact files the home page cards use)
    is preferred; the bundled static/images copy is only a fallback.
    """
    root_file = settings.BASE_DIR.parent / rel_path
    static_file = settings.BASE_DIR / 'static' / rel_path
    if root_file.exists():
        return f"/{rel_path}"
    if static_file.exists():
        return f"{settings.STATIC_URL}{rel_path}"
    return None


def build_product_gallery(product):
    """Build the main image + thumbnail list from existing assets only."""
    gallery = []
    if product.image:
        gallery.append({'url': product.image.url, 'alt': product.name})
    for rel_path in PRODUCT_IMAGE_CANDIDATES.get(product.slug, []):
        url = _resolve_static_image(rel_path)
        if url and url not in [img['url'] for img in gallery]:
            gallery.append({'url': url, 'alt': product.name})
    return gallery


def annotate_card_images(products):
    """
    Attach ``card_image_url`` (the same primary photograph the home page card
    uses) to every product, so catalogue and related-product cards reuse the
    real product photos instead of the missing category placeholder images.
    """
    for prod in products:
        gallery = build_product_gallery(prod)
        prod.card_image_url = gallery[0]['url'] if gallery else ''
    return products


def get_cart_items(request):
    cart = request.session.get(CART_SESSION_KEY, [])
    return cart if isinstance(cart, list) else []


def save_cart_items(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def build_cart_lines(cart):
    """
    Validate the session cart against the database and compute all prices
    server-side. Invalid / inactive / malformed lines are silently dropped.
    Returns (lines, subtotal, tax_amount, total).
    """
    lines = []
    subtotal = Decimal('0.00')
    for item in cart:
        try:
            product = Product.objects.select_related('category').get(
                id=int(item.get('product_id')),
                is_active=True
            )
            size = Decimal(str(item.get('size')))
            qty = int(item.get('qty'))
        except (Product.DoesNotExist, ValueError, TypeError, InvalidOperation):
            continue
        if size <= 0 or qty <= 0 or qty > MAX_CART_LINE_QTY:
            continue
        weight_kg = size * qty
        line_total = (weight_kg * product.unit_price).quantize(Decimal('0.01'))
        subtotal += line_total
        lines.append({
            'product': product,
            'size': size,
            'qty': qty,
            'weight_kg': weight_kg,
            'unit_price': product.unit_price,
            'line_total': line_total,
        })
    subtotal = subtotal.quantize(Decimal('0.01'))
    tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))  # 5% GST
    total_amount = subtotal + tax_amount
    return lines, subtotal, tax_amount, total_amount


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

    products = annotate_card_images(products)

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
    products = annotate_card_images(category.products.filter(is_active=True))
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
    related_products = annotate_card_images(Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:3])

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
        'packaging_sizes': parse_packaging_sizes(product.packaging_options),
        'gallery': build_product_gallery(product),
    }
    return render(request, 'products/product_detail.html', context)


def cart_add_view(request):
    """Add a product + packaging size + quantity to the session cart (server-validated)."""
    if request.method != 'POST':
        return redirect('products:catalog')

    product_id = request.POST.get('product_id')
    size_raw = request.POST.get('size', '').strip()
    qty_raw = request.POST.get('qty', '1').strip()
    go_checkout = request.POST.get('checkout') in ('1', 'true', 'True', 'on')

    product = get_object_or_404(Product, id=product_id, is_active=True)
    return_url = product.get_absolute_url()

    try:
        qty = int(qty_raw)
    except (TypeError, ValueError):
        qty = 0
    if qty < 1 or qty > MAX_CART_LINE_QTY:
        messages.error(
            request,
            f"Invalid quantity for {product.name}. Please choose between 1 and {MAX_CART_LINE_QTY} packs."
        )
        return redirect(return_url)

    allowed_sizes = parse_packaging_sizes(product.packaging_options)
    try:
        size = Decimal(size_raw) if size_raw else allowed_sizes[0]
    except InvalidOperation:
        size = None
    if size is None or size not in allowed_sizes:
        messages.error(request, f"Please select a valid packaging size for {product.name}.")
        return redirect(return_url)

    cart = get_cart_items(request)
    merged = False
    for item in cart:
        try:
            same_line = int(item.get('product_id')) == product.id and Decimal(str(item.get('size'))) == size
        except (ValueError, TypeError, InvalidOperation):
            continue
        if same_line:
            item['qty'] = min(int(item.get('qty', 0)) + qty, MAX_CART_LINE_QTY)
            merged = True
            break
    if not merged:
        cart.append({'product_id': product.id, 'size': str(size), 'qty': qty})
    save_cart_items(request, cart)

    messages.success(
        request,
        f"{qty} × {size} kg pack of {product.name} added to your cart "
        f"(approx. {size * qty} kg). Your cart is saved while you keep browsing."
    )
    if go_checkout:
        return redirect('products:checkout')
    return redirect('products:cart')


def cart_view(request):
    """Render the shopping cart with server-side validated lines and totals."""
    lines, subtotal, tax_amount, total_amount = build_cart_lines(get_cart_items(request))
    context = {
        'lines': lines,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'page_title': 'Your Cart',
    }
    return render(request, 'products/cart.html', context)


def cart_update_view(request):
    """Update the quantity of a cart line, or remove it entirely."""
    if request.method != 'POST':
        return redirect('products:cart')

    product_id = request.POST.get('product_id', '').strip()
    size_raw = request.POST.get('size', '').strip()
    action = request.POST.get('action', 'update')

    cart = get_cart_items(request)
    new_cart = []
    found = False
    for item in cart:
        same_line = str(item.get('product_id')) == product_id and str(item.get('size')) == size_raw
        if not same_line:
            new_cart.append(item)
            continue
        found = True
        if action == 'remove':
            continue  # drop the line
        try:
            qty = int(request.POST.get('qty', '0'))
        except (TypeError, ValueError):
            qty = -1
        if 1 <= qty <= MAX_CART_LINE_QTY:
            item['qty'] = qty
            new_cart.append(item)
        else:
            new_cart.append(item)  # invalid input: keep previous valid quantity
            messages.error(
                request,
                f"Invalid quantity. Please choose between 1 and {MAX_CART_LINE_QTY} packs."
            )

    save_cart_items(request, new_cart)
    if action == 'remove' and found:
        messages.info(request, 'Item removed from your cart.')
    return redirect('products:cart')


@login_required(login_url='/login/')
def checkout_view(request):
    """
    Checkout for the session cart. Requires login (redirects to the existing
    Django login page and returns the customer here afterwards).
    On POST, validates everything server-side and creates a real Order +
    OrderItems row in the database (no fake confirmation).
    """
    from portal.models import Order, OrderItem

    cart = get_cart_items(request)
    lines, subtotal, tax_amount, total_amount = build_cart_lines(cart)

    # Prefill from the buyer's existing company profile / account
    profile = getattr(request.user, 'company_profile', None)
    initial = {
        'full_name': request.user.get_full_name(),
        'company_name': getattr(profile, 'company_name', ''),
        'email': request.user.email,
        'phone': getattr(profile, 'phone', ''),
        'address_line1': getattr(profile, 'address_line1', ''),
        'address_line2': getattr(profile, 'address_line2', ''),
        'city': getattr(profile, 'city', ''),
        'state': getattr(profile, 'state', ''),
        'pincode': getattr(profile, 'pincode', ''),
        'gstin': getattr(profile, 'gstin', ''),
    }

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        company_name = request.POST.get('company_name', '').strip() or full_name
        email = request.POST.get('email', '').strip() or request.user.email
        phone = request.POST.get('phone', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        gstin = request.POST.get('gstin', '').strip()
        notes = request.POST.get('notes', '').strip()
        payment_method = request.POST.get('payment_method', 'cod').strip().lower()
        if payment_method not in ('cod', 'upi'):
            payment_method = 'cod'
        upi_utr = request.POST.get('upi_utr', '').strip()

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not phone:
            errors.append('Phone number is required.')
        if not address_line1 or not city or not state or not pincode:
            errors.append('Complete delivery address (address, city, state and pincode) is required.')
        if not lines:
            errors.append('Your cart is empty. Please add a product before checking out.')
        if payment_method == 'upi' and not upi_utr:
            errors.append('UPI transaction reference (UTR number) is required for UPI payment.')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            full_address_parts = [
                p for p in [address_line1, address_line2, city, state, f"PIN: {pincode}"] if p
            ]
            full_address = ", ".join(full_address_parts)

            initial_payment_status = 'verification_pending' if payment_method == 'upi' else 'cod'

            order = Order.objects.create(
                user=request.user,
                customer_name=full_name,
                company_name=company_name,
                email=email,
                phone=phone,
                delivery_address=full_address,
                city=city,
                state=state,
                pincode=pincode,
                gstin=gstin,
                quality='Standard',
                is_quote_request=False,
                payment_method=payment_method,
                payment_status=initial_payment_status,
                upi_utr_number=upi_utr if payment_method == 'upi' else '',
                status='pending',
                subtotal=subtotal,
                delivery_charges=Decimal('0.00'),
                tax_amount=tax_amount,
                total_amount=total_amount,
                shipping_address=(
                    f"Recipient: {full_name} ({company_name})\nPhone: {phone}\n"
                    f"Email: {email}\nShipping Address: {full_address}"
                ),
                customer_notes=notes,
                additional_requirements=notes,
            )

            for line in lines:
                OrderItem.objects.create(
                    order=order,
                    product=line['product'],
                    product_name=line['product'].name,
                    quantity=line['weight_kg'],
                    unit=f"{line['qty']} x {line['size']}kg",
                    packaging=f"{line['size']}kg Pack",
                    unit_price=line['unit_price'],
                    total_price=line['line_total'],
                )

            save_cart_items(request, [])

            messages.success(
                request,
                f"Order #{order.order_number} placed successfully! Total ₹{total_amount:,.2f}. "
                "Our team will confirm dispatch schedule shortly."
            )
            return redirect('portal:orders')

        # Re-render with the customer's submitted values after a validation error
        initial.update({k: request.POST.get(k, initial.get(k, '')) for k in initial})
        initial['notes'] = notes
        initial['payment_method'] = payment_method
        initial['upi_utr'] = upi_utr

    context = {
        'lines': lines,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'initial': initial,
        'page_title': 'Checkout',
    }
    return render(request, 'products/checkout.html', context)


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


