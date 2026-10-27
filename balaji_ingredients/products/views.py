"""
products/views.py
Views for Catalog, Category Detail, Product Detail, Session Cart, Checkout, and RFQ submission.
"""

import re
import json
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Category, Product, QuoteRequest
from .forms import QuoteRequestForm


# ---------------------------------------------------------------------------
# Technical specification data & Profiles for real ingredients
# ---------------------------------------------------------------------------

PRODUCT_TECHNICAL_PROFILES = {
    'red-chilli-powder': {
        'appearance': 'Fine, vibrant deep red powder with natural oil sheen',
        'particle_size': '60 - 80 Mesh (Silky Cold Stone Ground)',
        'origin_region': 'Byadgi (Karnataka) & Guntur (Andhra Pradesh), India',
        'purity': '99.5% Min Optical Sortex Cleaned Chillies',
        'moisture': '< 10.5% (Halogen Analysis)',
        'shelf_life': '12 Months in cool, dry storage',
        'packaging': '25kg & 50kg PP Bags with LDPE Liner, 1000kg FIBC Jumbo Bags',
        'certifications': 'FSSAI Aligned, APEDA Registered, Spices Board Tested',
        'applications': 'Commercial Spice Blends, Seasoning Manufacturers, Snacks & Namkeen, Ready Meals',
        'storage': 'Store in sealed bags in a cool, dry warehouse below 24°C away from direct sunlight.',
        'tds': [
            ('Moisture Content', '< 10.5% w/w', 'IS:1797-1985'),
            ('Total Ash', '< 8.0% w/w Max', 'IS:1797-1985'),
            ('Acid Insoluble Ash', '< 1.25% w/w Max', 'IS:1797-1985'),
            ('Non-Volatile Ether Extract', '> 12.0% w/w Min', 'IS:1797-1985'),
            ('Crude Fibre', '< 28.0% w/w Max', 'IS:1797-1985'),
            ('Sortex Optical Purity', '99.5% Min', 'Optical Sieve Separation'),
            ('Aflatoxin (B1+B2+G1+G2)', '< 10 ppb (Compliant)', 'AOAC 999.07 HPLC'),
            ('Pesticide Residue', 'Compliant with FSSAI & APEDA MRL', 'GC-MS / LC-MS NABL'),
        ]
    },
    'malabar-black-pepper': {
        'appearance': 'Uniform dark blackish-brown extra bold whole peppercorns',
        'particle_size': '4.25 mm+ Diameter (Garbled Extra Bold MGSEB)',
        'origin_region': 'Malabar Coast, Wayanad & Idukki Estates, Kerala, India',
        'purity': '99.5% Min Density Graded & Optical Sortex',
        'moisture': '< 11.0% (Air Oven Method)',
        'shelf_life': '24 Months in sealed packaging',
        'packaging': '25kg & 50kg Jute / Multi-wall Paper / PP Bags with Liner',
        'certifications': 'Spices Board India Certified, FSSAI Aligned, APEDA',
        'applications': 'Industrial Seasoning, Meat Processing, Extract Manufacturers, Gourmet Hospitality',
        'storage': 'Store in well-ventilated dry ambient storage off the floor on wooden pallets.',
        'tds': [
            ('Moisture Content', '< 11.0% w/w', 'IS:1797-1985'),
            ('Bulk Density (Liter Weight)', '> 550 g/L', 'Gravimetric'),
            ('Piperine Content', '4.5% - 6.0% w/w Min', 'HPLC Analysis'),
            ('Volatile Oil Content', '> 2.0% v/w Min', 'Steam Distillation'),
            ('Extraneous Matter', '< 0.5% w/w Max', 'Manual & Sieve Analysis'),
            ('Light Berries / Pinheads', '< 2.0% w/w Max', 'Flotation Method'),
            ('Mouldy / Damaged Berries', '< 1.0% w/w Max', 'Visual Inspection'),
            ('Pesticides & Heavy Metals', 'FSSAI & ASTA Compliant', 'ICP-MS / GC-MS'),
        ]
    },
    'green-cardamom': {
        'appearance': 'Plump, uniform deep parrot green pods with tight suture',
        'particle_size': '8 mm+ Extra Bold (Grade AAA Bold Pods)',
        'origin_region': 'Misty High Ranges of Idukki & Cardamom Hills, Kerala, India',
        'purity': '99.8% Hand-Graded & Cleaned',
        'moisture': '< 10.0% (Dean & Stark Method)',
        'shelf_life': '18 Months in light-blocking sealed container',
        'packaging': '5kg, 10kg, 25kg Airtight Food-grade Liners in Corrugated Master Cartons',
        'certifications': 'Spices Board India Benchmark, FSSAI Aligned, APEDA',
        'applications': 'Premium Confectionery, Traditional Sweets, Tea Blends, Bakery & Flavor Houses',
        'storage': 'Cool, dark, dry storage away from strong aromatic commodities.',
        'tds': [
            ('Pod Diameter', '8 mm+ and above', 'Calibrated Gauge Sieve'),
            ('Moisture Content', '< 10.0% w/w', 'IS:1797-1985'),
            ('Total Volatile Oil', '6.5% - 9.0% v/w Min', 'ISO 6571 Steam Distillation'),
            ('1,8-Cineole & Terpinyl Acetate', '> 70% of Volatile Fraction', 'GC-FID Profile'),
            ('Immature & Shrivelled Pods', '< 1.5% w/w Max', 'Visual Separation'),
            ('Empty Pods / Thrips Damage', '< 1.0% w/w Max', 'Visual & Sieve'),
            ('Extraneous Matter', '< 0.2% w/w Max', 'Manual Inspection'),
            ('Fumigation / Weevil Status', 'NIL (Vacuum / CO2 Treated)', 'Microscopic Verification'),
        ]
    },
    'stone-ground-ragi-flour': {
        'appearance': 'Natural earthy reddish-brown fine powder with nutty aroma',
        'particle_size': '80 Mesh Silky Smooth (Cold Stone Milled)',
        'origin_region': 'Old Mysore & Chitradurga Agronomic Belt, Karnataka, India',
        'purity': '99.5% Optical Sortex Cleaned Whole Finger Millet Grain',
        'moisture': '< 10.5% (Halogen Moisture Analyzer)',
        'shelf_life': '9 Months (Freshly Stone Milled to Order)',
        'packaging': '25kg & 50kg Food-grade PP Bags with LDPE Liner',
        'certifications': 'FSSAI License Aligned, Karnataka APMC Origin, NABL Tested',
        'applications': 'Bakery Premixes, Health Foods, Extruded Snacks, Porridge & Baby Food Industry',
        'storage': 'Store in cool dry conditions on pallets; protect from humidity and rodents.',
        'tds': [
            ('Particle Fineness', '> 95% passes through 80 Mesh Sieve', 'IS:1155 Sieve Test'),
            ('Moisture Content', '< 10.5% w/w Max', 'IS:4333 (Part II)'),
            ('Crude Protein', '7.0% - 8.2% w/w Min', 'Kjeldahl Method (N x 6.25)'),
            ('Total Calcium', '340 - 360 mg / 100g', 'Atomic Absorption Spectrometry'),
            ('Dietary Fibre', '15.0% - 18.0% w/w', 'AOAC Enzymatic-Gravimetric'),
            ('Total Ash', '< 2.8% w/w Max', 'IS:1155 Muffle Furnace'),
            ('Acid Insoluble Ash', '< 0.15% w/w Max', 'IS:1155 Protocol'),
            ('Gluten Content', 'Naturally Gluten-Free (< 20 ppm)', 'ELISA R5 Method'),
        ]
    }
}


# ---------------------------------------------------------------------------
# Packaging size parsing, product image gallery, and session cart helpers
# ---------------------------------------------------------------------------

SIGNATURE_SHOWCASE = {
    'red-chilli-powder': {
        'name': 'Red Chilli Powder',
        'blend_tag': 'BYADGI & GUNTUR BLEND',
        'description': 'Sun-dried Byadgi and Guntur chillies, stone-ground to preserve natural oils and colour. Ideal for authentic Indian cooking and bulk supply.',
        'badge1': 'Premium Grade',
        'badge2': 'Bulk Supply',
        'image_url': '/images/chilli_product.jpg',
        'grades': ['Premium Grade', 'Export Sortex Grade', 'Commercial Standard'],
    },
    'malabar-black-pepper': {
        'name': 'Malabar Black Pepper',
        'blend_tag': 'MALABAR COAST EXTRA BOLD',
        'description': 'Uniform dark extra-bold peppercorns, high-density garbled grade. Rich in natural piperine with robust aroma and pungency.',
        'badge1': 'MGSEB Bold Grade',
        'badge2': 'Bulk Supply',
        'image_url': '/images/pepper_product.jpg',
        'grades': ['MGSEB Bold (4.25mm+)', 'Garbled Special', 'Standard Commercial'],
    },
    'green-cardamom': {
        'name': 'Green Cardamom',
        'blend_tag': 'IDUKKI ESTATE GRADE AAA',
        'description': 'Plump, vibrant green 8mm+ extra-bold cardamom pods harvested from high-range Western Ghat estates with intense aromatic essential oils.',
        'badge1': 'Grade AAA Extra Bold',
        'badge2': 'Bulk Supply',
        'image_url': '/images/cardamom_product.jpg',
        'grades': ['Grade AAA (8mm+ Bold)', 'Grade AA (7-8mm)', 'Commercial Split'],
    },
    'stone-ground-ragi-flour': {
        'name': 'Stone-Ground Ragi Flour',
        'blend_tag': 'OLD MYSORE NATIVE GRAIN',
        'description': '100% whole finger millet grain, slow cold-milled on traditional stone disks to preserve essential calcium, dietary fibre, and natural micronutrients.',
        'badge1': '100% Cold Milled',
        'badge2': 'Bulk Supply',
        'image_url': '/images/ragi_product.jpg',
        'grades': ['80 Mesh Superfine', 'Coarse Bakery Mesh', 'Standard Commercial'],
    },
}

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
    """
    Detailed view of an individual ingredient with two-column layout,
    fixed/sticky product image, technical specifications TDS, and RFQ / Buy actions.
    """
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

    # Detailed technical profile & tailored TDS
    profile = PRODUCT_TECHNICAL_PROFILES.get(product.slug, {})
    tds_data = profile.get('tds')
    if not tds_data:
        tds_data = [
            ('Optical Sortex Purity', product.purity_percentage, 'Optical Sieve Separation'),
            ('Moisture Content', product.moisture_content, 'Halogen Moisture Analysis'),
            ('Shelf Life', product.shelf_life, 'Controlled Ambient Storage'),
            ('Origin / Agronomic Source', product.origin, 'Primary Agricultural Market'),
            ('Packaging Standard', product.packaging_options, 'Food-grade multiwall / PP packaging'),
            ('Food Safety Benchmark', 'FSSAI License & Lab Compliance', 'NABL Certified Testing'),
        ]

    faqs = [
        ("What is the minimum commercial order volume (MoQ)?",
         f"Standard packaging starts from single commercial bags ({product.packaging_options}) up to full truckload (10-20 Metric Ton) consignments. Contact our desk for custom bag sizes."),
        ("Can we request certified laboratory pre-shipment samples?",
         "Yes, certified 250g laboratory pre-shipment samples accompanied by a batch Certificate of Analysis (CoA) can be dispatched via express courier to verified enterprises."),
        ("Are tax invoices provided for GST input tax credit?",
         "Yes, all commercial consignments are billed with official GST tax invoices including company GSTIN, HSN codes, and weighbridge slips."),
        ("What is the dispatch schedule and delivery lead time?",
         "Commercial dispatches leave our Karnataka & regional milling facilities within 24 to 48 hours following order confirmation, supported by real-time tracking.")
    ]

    sku = f"BI-{product.category.slug[:3].upper()}-{product.id:04d}"
    packaging_sizes = parse_packaging_sizes(product.packaging_options)
    gallery = build_product_gallery(product)

    showcase_item = SIGNATURE_SHOWCASE.get(product.slug)
    if showcase_item:
        display_name = showcase_item['name']
        blend_tag = showcase_item['blend_tag']
        display_desc = showcase_item['description']
        badge1 = showcase_item['badge1']
        badge2 = showcase_item['badge2']
        main_image_url = showcase_item['image_url']
        grades = showcase_item['grades']
    else:
        display_name = product.name
        blend_tag = (product.origin or product.category.name).upper()
        display_desc = product.subtitle or product.description
        badge1 = product.grade or 'Premium Grade'
        badge2 = 'Bulk Supply'
        main_image_url = product.image.url if product.image else (gallery[0]['url'] if gallery else '/images/chilli_product.jpg')
        grades = [product.grade or 'Premium Grade', 'Commercial Standard']

    signature_thumbs = [
        {
            'slug': 'red-chilli-powder',
            'category_slug': 'chilli-spices',
            'name': 'Red Chilli Powder',
            'image_url': '/images/chilli_product.jpg',
            'is_active': (product.slug == 'red-chilli-powder'),
            'url': '/products/chilli-spices/red-chilli-powder/',
        },
        {
            'slug': 'malabar-black-pepper',
            'category_slug': 'chilli-spices',
            'name': 'Malabar Black Pepper',
            'image_url': '/images/pepper_product.jpg',
            'is_active': (product.slug == 'malabar-black-pepper'),
            'url': '/products/chilli-spices/malabar-black-pepper/',
        },
        {
            'slug': 'green-cardamom',
            'category_slug': 'chilli-spices',
            'name': 'Green Cardamom',
            'image_url': '/images/cardamom_product.jpg',
            'is_active': (product.slug == 'green-cardamom'),
            'url': '/products/chilli-spices/green-cardamom/',
        },
        {
            'slug': 'stone-ground-ragi-flour',
            'category_slug': 'ragi-millets',
            'name': 'Stone-Ground Ragi Flour',
            'image_url': '/images/ragi_product.jpg',
            'is_active': (product.slug == 'stone-ground-ragi-flour'),
            'url': '/products/ragi-millets/stone-ground-ragi-flour/',
        },
    ]

    context = {
        'product': product,
        'sku': sku,
        'display_name': display_name,
        'blend_tag': blend_tag,
        'display_desc': display_desc,
        'badge1': badge1,
        'badge2': badge2,
        'main_image_url': main_image_url,
        'available_grades': grades,
        'signature_thumbs': signature_thumbs,
        'unit_price': product.unit_price,
        'formatted_price': f"₹{int(product.unit_price):,} / kg" if product.unit_price else "Price to be confirmed",
        'specifications': specifications,
        'profile': profile,
        'tds_data': tds_data,
        'faqs': faqs,
        'related_products': related_products,
        'form': form,
        'page_title': display_name,
        'packaging_sizes': packaging_sizes,
        'gallery': gallery,
    }
    return render(request, 'products/product_detail.html', context)


@csrf_exempt
def booking_action_api(request):
    """
    Dedicated endpoint for the 'Reserve Your Ingredients' booking interface.
    Handles 'add_to_cart' and 'buy_now'.
    Validates on server, updates session cart, saves customer details for checkout,
    and returns JSON or redirect.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method is allowed.'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'require_login': True,
            'message': 'Please sign in to reserve ingredients or place orders.'
        }, status=401)

    is_json = request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{'))
    if is_json:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
    else:
        data = request.POST

    action = str(data.get('action', 'add_to_cart')).strip().lower()
    product_id = data.get('product_id')
    full_name = str(data.get('full_name', '')).strip()
    phone = str(data.get('phone', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    delivery_address = str(data.get('delivery_address', '')).strip()
    grade = str(data.get('grade', '')).strip() or 'Premium Grade'
    qty_raw = str(data.get('qty', '1')).strip()
    unit = str(data.get('unit', 'kg')).strip().lower()
    delivery_date = str(data.get('delivery_date', '')).strip()
    special_requirements = str(data.get('special_requirements', '')).strip()

    # 1. Product Validation
    try:
        product = Product.objects.get(id=int(product_id), is_active=True)
    except (Product.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Selected ingredient is invalid or unavailable.'}, status=404)

    # 2. Quantity & Unit Validation
    try:
        qty_num = Decimal(qty_raw)
        if qty_num <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Please enter a valid positive quantity.'}, status=400)

    if unit not in ('kg', 'quintal', 'tonne'):
        unit = 'kg'

    multiplier = Decimal('1')
    if unit == 'quintal':
        multiplier = Decimal('100')
    elif unit == 'tonne':
        multiplier = Decimal('1000')

    weight_kg = (qty_num * multiplier).quantize(Decimal('0.01'))

    # 3. Action Specific Validation
    if action == 'buy_now':
        if not full_name:
            return JsonResponse({'success': False, 'message': 'Full Name is required for Buy Now.'}, status=400)
        if not phone:
            return JsonResponse({'success': False, 'message': 'Mobile Number is required for Buy Now.'}, status=400)
        phone_clean = re.sub(r'[\s\-\+\(\)]', '', phone)
        if len(phone_clean) < 10 or not phone_clean.isdigit():
            return JsonResponse({'success': False, 'message': 'Please enter a valid 10-digit mobile number.'}, status=400)
        if not email:
            return JsonResponse({'success': False, 'message': 'Email address is required for Buy Now.'}, status=400)
        try:
            from django.core.validators import validate_email, ValidationError
            validate_email(email)
        except Exception:
            return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)
        if not delivery_address:
            return JsonResponse({'success': False, 'message': 'Complete Delivery Address is required for Buy Now.'}, status=400)

    # 4. Add to cart
    cart = get_cart_items(request)
    cart_qty = int(weight_kg) if weight_kg >= 1 else 1
    merged = False
    for item in cart:
        try:
            if int(item.get('product_id')) == product.id and str(item.get('size')) == '1':
                item['qty'] = min(int(item.get('qty', 0)) + cart_qty, 5000)
                merged = True
                break
        except Exception:
            continue
    if not merged:
        cart.append({'product_id': product.id, 'size': '1', 'qty': cart_qty})
    save_cart_items(request, cart)

    cart_count = sum(int(it.get('qty', 0)) for it in cart)

    # 5. Buy Now flow: create Order and redirect to online payment interface
    if action == 'buy_now':
        from portal.models import Order, OrderItem
        from django.utils import timezone

        subtotal = (weight_kg * product.unit_price).quantize(Decimal('0.01'))
        tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
        total_amount = subtotal + tax_amount

        order_seq = Order.objects.count() + 1
        today_str = timezone.now().strftime('%Y%m%d')
        order_number = f"BI-{today_str}-{order_seq:04d}"

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            order_number=order_number,
            customer_name=full_name,
            company_name=full_name,
            email=email,
            phone=phone,
            delivery_address=delivery_address,
            quality=grade,
            payment_method='upi',
            payment_status='verification_pending',
            status='pending',
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            customer_notes=special_requirements,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit=f"{qty_num} {unit}",
            quantity=weight_kg,
            packaging=f"{weight_kg}kg bulk pack",
            unit_price=product.unit_price,
            total_price=subtotal,
        )

        request.session['booking_checkout_data'] = {
            'order_number': order.order_number,
            'full_name': full_name,
            'phone': phone,
            'email': email,
            'delivery_address': delivery_address,
            'grade': grade,
            'qty': str(qty_num),
            'unit': unit,
            'delivery_date': delivery_date,
            'special_requirements': special_requirements,
        }
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'redirect_url': f'/products/payment/{order.order_number}/',
            'order_id': order.order_number,
            'total_amount': f"{total_amount:,.2f}",
            'message': f"Order #{order.order_number} created. Opening online payment interface...",
            'cart_count': cart_count,
        })

    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'message': f"{qty_num} {unit} of {product.name} ({grade}) added to your cart.",
        'product_name': product.name,
    })


@csrf_exempt
def cart_add_view(request):
    """
    Add a product + packaging size + quantity to the session cart.
    Accepts both standard form POST and asynchronous AJAX/JSON requests.
    Server-validates product ID, size, and quantity.
    """
    if request.method != 'POST':
        return redirect('products:catalog')

    # Parse inputs from JSON or Form POST
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
        product_id = data.get('product_id')
        size_raw = str(data.get('size', '')).strip()
        qty_raw = str(data.get('qty', '1')).strip()
        go_checkout = data.get('checkout') in ('1', 'true', 'True', True)
    else:
        product_id = request.POST.get('product_id')
        size_raw = request.POST.get('size', '').strip()
        qty_raw = request.POST.get('qty', '1').strip()
        go_checkout = request.POST.get('checkout') in ('1', 'true', 'True', 'on')

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.GET.get('format') == 'json' or
        request.POST.get('format') == 'json' or
        'application/json' in request.headers.get('Accept', '') or
        request.content_type == 'application/json'
    )

    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'require_login': True,
                'message': 'Please sign in to add products to your cart.'
            }, status=401)
        messages.warning(request, 'Please sign in to add products to your cart.')
        return redirect('core:home')

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except (Product.DoesNotExist, ValueError, TypeError):
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Product not found or unavailable.'}, status=404)
        messages.error(request, 'Product not found or currently unavailable.')
        return redirect('products:catalog')

    return_url = product.get_absolute_url()

    try:
        qty = int(qty_raw)
    except (TypeError, ValueError):
        qty = 1
    if qty < 1 or qty > MAX_CART_LINE_QTY:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': f"Please choose a quantity between 1 and {MAX_CART_LINE_QTY} packs."
            }, status=400)
        messages.error(
            request,
            f"Invalid quantity for {product.name}. Please choose between 1 and {MAX_CART_LINE_QTY} packs."
        )
        return redirect(return_url)

    allowed_sizes = parse_packaging_sizes(product.packaging_options)
    try:
        size = Decimal(size_raw) if size_raw else allowed_sizes[0]
    except InvalidOperation:
        size = allowed_sizes[0]
    if size not in allowed_sizes:
        size = allowed_sizes[0]

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

    cart_count = sum(int(it.get('qty', 0)) for it in cart)
    success_msg = f"{qty} × {size} kg pack of {product.name} added to your cart."

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'cart_count': cart_count,
            'product_id': product.id,
            'product_name': product.name,
            'size': str(size),
            'qty': qty,
        })

    messages.success(
        request,
        f"{qty} × {size} kg pack of {product.name} added to your cart "
        f"(approx. {size * qty} kg). Your cart is saved while you keep browsing."
    )
    if go_checkout:
        return redirect('products:checkout')
    return redirect('products:cart')


def cart_count_api(request):
    """API endpoint returning the active session cart count."""
    cart = get_cart_items(request)
    count = sum(int(it.get('qty', 0)) for it in cart) if isinstance(cart, list) else 0
    return JsonResponse({'cart_count': count})


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


def checkout_view(request):
    """
    Checkout for the session cart.
    Supports both logged-in users and guest commercial buyers.
    On POST, validates everything server-side and creates a real Order + OrderItem row.
    Redirects to the order confirmation page with the official order number.
    """
    from portal.models import Order, OrderItem

    if not request.user.is_authenticated:
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('Accept', '') or
            request.content_type == 'application/json'
        )
        if is_ajax:
            return JsonResponse({
                'success': False,
                'require_login': True,
                'message': 'Please sign in to proceed to checkout.'
            }, status=401)
        messages.info(request, 'Please sign in to complete checkout.')
        return redirect('products:cart')

    cart = get_cart_items(request)
    lines, subtotal, tax_amount, total_amount = build_cart_lines(cart)

    # Prefill from the buyer's existing profile if logged in
    profile = getattr(request.user, 'company_profile', None) if request.user.is_authenticated else None
    booking_data = request.session.get('booking_checkout_data') or {}
    initial = {
        'full_name': request.user.get_full_name() if request.user.is_authenticated else '',
        'company_name': getattr(profile, 'company_name', ''),
        'email': request.user.email if request.user.is_authenticated else '',
        'phone': getattr(profile, 'phone', ''),
        'address_line1': getattr(profile, 'address_line1', ''),
        'address_line2': getattr(profile, 'address_line2', ''),
        'city': getattr(profile, 'city', ''),
        'state': getattr(profile, 'state', ''),
        'pincode': getattr(profile, 'pincode', ''),
        'gstin': getattr(profile, 'gstin', ''),
        'payment_method': 'cod',
        'upi_utr': '',
        'notes': booking_data.get('special_requirements', ''),
    }
    if booking_data:
        if not initial['full_name'] and booking_data.get('full_name'):
            initial['full_name'] = booking_data['full_name']
        if not initial['email'] and booking_data.get('email'):
            initial['email'] = booking_data['email']
        if not initial['phone'] and booking_data.get('phone'):
            initial['phone'] = booking_data['phone']
        if not initial['address_line1'] and booking_data.get('delivery_address'):
            initial['address_line1'] = booking_data['delivery_address']

    if request.method == 'POST':
        if not request.user.is_authenticated:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'require_login': True,
                    'message': 'Please sign in to complete your purchase.'
                }, status=401)
            messages.info(request, 'Please sign in to complete your purchase.')
            return redirect('core:home')

        full_name = request.POST.get('full_name', '').strip()
        company_name = request.POST.get('company_name', '').strip() or full_name
        email = request.POST.get('email', '').strip() or (request.user.email if request.user.is_authenticated else '')
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
            errors.append('Contact / Full name is required.')
        if not phone:
            errors.append('Commercial phone number is required.')
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
            order_user = request.user if request.user.is_authenticated else None

            order = Order.objects.create(
                user=order_user,
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
            return redirect('products:order_confirmation', order_number=order.order_number)

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


def order_confirmation_view(request, order_number):
    """Render the official order confirmation page after successful order placement."""
    from portal.models import Order
    order = get_object_or_404(Order, order_number=order_number)
    items = order.items.select_related('product').all()
    context = {
        'order': order,
        'items': items,
        'page_title': f"Order Confirmed — #{order.order_number}",
    }
    return render(request, 'products/order_confirmation.html', context)


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




def order_payment_view(request, order_number):
    """
    Renders the dedicated Online Payment interface with automatic verification gateway integration,
    order ID, payable amount, and partial balance support.
    """
    from portal.models import Order
    from portal.services import get_payment_credentials

    order = get_object_or_404(Order, order_number=order_number)
    items = order.items.select_related('product').all()
    primary_item = items.first()
    product = primary_item.product if primary_item else None

    return_url = product.get_absolute_url() if product else '/'
    qr_image_url = '/images/phonepe_payment_qr.jpg'

    creds = get_payment_credentials()
    transactions = order.transactions.all().order_by('-created_at')

    context = {
        'order': order,
        'items': items,
        'primary_item': primary_item,
        'product': product,
        'return_url': return_url,
        'qr_image_url': qr_image_url,
        'page_title': f"Complete Payment — Order #{order.order_number}",
        'creds': creds,
        'transactions': transactions,
        'outstanding_balance': order.outstanding_balance,
        'verified_paid_amount': order.verified_paid_amount,
        'excess_amount': order.excess_amount,
    }
    return render(request, 'products/order_payment.html', context)


def order_status_api(request, order_number):
    """
    Returns real-time trusted payment status and decimal-safe balance calculations.
    """
    from portal.models import Order
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    txns_data = []
    for t in order.transactions.all().order_by('-created_at')[:5]:
        txns_data.append({
            'transaction_id': t.transaction_id,
            'provider': t.provider,
            'amount': float(t.amount),
            'status': t.status,
            'provider_payment_id': t.provider_payment_id or '',
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({
        'success': True,
        'order_number': order.order_number,
        'payment_status': order.payment_status,
        'status_display': order.get_payment_status_display(),
        'is_paid': (order.payment_status == 'paid'),
        'is_partial': (order.payment_status == 'partial'),
        'is_pending': (order.payment_status == 'verification_pending'),
        'order_workflow_status': order.status,
        'total_amount': float(order.total_amount),
        'verified_paid_amount': float(order.verified_paid_amount),
        'outstanding_balance': float(order.outstanding_balance),
        'excess_amount': float(order.excess_amount),
        'upi_utr_number': order.upi_utr_number or '',
        'transactions': txns_data,
    })


@csrf_exempt
def payment_create_api(request, order_number):
    """
    Initiates a verified server-side payment transaction for the given order.
    Calculates exact payable amount with Decimal.
    """
    from portal.models import Order
    from portal.services import create_payment_transaction, get_payment_credentials

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    if order.outstanding_balance <= Decimal('0.00'):
        return JsonResponse({
            'success': False,
            'message': 'This invoice has already been fully settled.',
            'is_paid': True
        }, status=400)

    # Optional partial amount requested
    is_json = request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{'))
    data = json.loads(request.body) if is_json else request.POST
    req_amount = data.get('amount')

    try:
        txn = create_payment_transaction(order, amount=req_amount)
    except ValueError as ve:
        return JsonResponse({'success': False, 'message': str(ve)}, status=400)

    creds = get_payment_credentials()

    return JsonResponse({
        'success': True,
        'order_number': order.order_number,
        'transaction_id': txn.transaction_id,
        'provider_order_id': txn.provider_order_id,
        'amount': float(txn.amount),
        'amount_paise': int(txn.amount * 100),
        'currency': txn.currency,
        'key_id': creds['key_id'],
        'customer_name': order.customer_name or (order.user.username if order.user else 'Customer'),
        'customer_email': order.email,
        'customer_phone': order.phone,
        'outstanding_balance': float(order.outstanding_balance),
    })


@csrf_exempt
def payment_verify_api(request, order_number):
    """
    Receives provider callback payload, verifies cryptographic signature,
    and updates order atomically.
    """
    from portal.services import verify_payment_callback

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)

    is_json = request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{'))
    data = json.loads(request.body) if is_json else request.POST

    provider_order_id = str(data.get('razorpay_order_id') or data.get('provider_order_id') or '').strip()
    provider_payment_id = str(data.get('razorpay_payment_id') or data.get('provider_payment_id') or '').strip()
    signature = str(data.get('razorpay_signature') or data.get('signature') or '').strip()
    verified_amount = data.get('amount')

    if not provider_order_id or not provider_payment_id or not signature:
        return JsonResponse({
            'success': False,
            'message': 'Missing payment verification tokens (provider_order_id, provider_payment_id, signature).'
        }, status=400)

    result = verify_payment_callback(
        order_number=order_number,
        provider_order_id=provider_order_id,
        provider_payment_id=provider_payment_id,
        signature=signature,
        verified_amount=verified_amount,
        raw_payload=data
    )

    status_code = result.get('status_code', 200 if result.get('success') else 400)
    return JsonResponse(result, status=status_code)


@csrf_exempt
def payment_webhook_view(request):
    """
    Asynchronous server-side webhook endpoint for merchant gateway.
    Verifies HMAC signature and idempotently reconciles payment.
    """
    from portal.services import handle_payment_webhook

    if request.method != 'POST':
        return HttpResponse('Method Not Allowed', status=405)

    signature_header = request.headers.get('X-Razorpay-Signature') or request.headers.get('x-razorpay-signature', '')
    result = handle_payment_webhook(request.body, signature_header)

    status_code = result.get('status_code', 200 if result.get('success') else 400)
    return JsonResponse(result, status=status_code)


@csrf_exempt
def order_submit_utr_api(request, order_number):
    """
    Allows the customer to submit an offline UPI UTR / Transaction reference.
    Explicitly marks status as pending manual desk review.
    Does NOT automatically confirm bank credit.
    """
    from portal.models import Order, PaymentTransaction
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method is allowed.'}, status=405)

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    is_json = request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{'))
    data = json.loads(request.body) if is_json else request.POST

    utr = str(data.get('utr', '')).strip()
    if not utr or len(utr) < 6:
        return JsonResponse({'success': False, 'message': 'Please enter a valid Transaction / UTR number (min 6 characters).'}, status=400)

    order.upi_utr_number = utr
    if order.payment_status != 'paid':
        order.payment_status = 'verification_pending'
    order.save(update_fields=['upi_utr_number', 'payment_status'])

    # Record PaymentTransaction for manual review
    PaymentTransaction.objects.get_or_create(
        order=order,
        transaction_id=f"UTR-{utr}",
        defaults={
            'provider': 'upi_manual',
            'amount': order.outstanding_balance,
            'status': 'pending',
            'notes': f"Manual UTR reference {utr} submitted by buyer; awaiting bank credit check by accounts."
        }
    )

    return JsonResponse({
        'success': True,
        'message': f"Reference {utr} recorded for manual verification. Automatic verification is not confirmed until approved by our accounts desk.",
        'upi_utr': utr,
        'payment_status': order.payment_status,
        'verified_paid_amount': float(order.verified_paid_amount),
        'outstanding_balance': float(order.outstanding_balance),
    })


@csrf_exempt
def order_update_method_api(request, order_number):
    """
    Updates the selected payment option (e.g. UPI, NetBanking, Card, COD)
    without creating duplicate orders.
    """
    from portal.models import Order
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method is allowed.'}, status=405)

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)

    is_json = request.content_type == 'application/json' or (request.body and request.body.strip().startswith(b'{'))
    data = json.loads(request.body) if is_json else request.POST

    method = str(data.get('method', 'UPI')).strip()
    order.payment_method = 'upi'
    order.admin_notes = f"Selected Payment Option: {method}"
    order.save(update_fields=['payment_method', 'admin_notes'])

    return JsonResponse({
        'success': True,
        'method': method,
        'order_number': order.order_number,
    })
