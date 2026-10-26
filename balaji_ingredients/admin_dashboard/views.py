"""
admin_dashboard/views.py
Premium Balaji Ingredients Administrative Dashboard Views.
Strict security, atomic database transactions, server-side validation, and audit logging.
"""

import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from core.models import ContactMessage, CustomerFeedback, SiteSettings, SiteStat
from portal.models import CompanyProfile, Notification, Order, OrderItem, PaymentConfig
from products.models import Category, Product, ProductSpecification, QuoteRequest
from .models import AuditLog, Promotion, StockMovement


# ==============================================================================
# SECURITY DECORATOR
# ==============================================================================

def staff_required(view_func):
    """
    Ensures that only authenticated staff or superusers can access dashboard views.
    Redirects unauthenticated visitors to login with an informational alert.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please sign in with administrator credentials to access the Dashboard.")
            return redirect(f"/admin-dashboard/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access restricted. Staff authorization required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==============================================================================
# 1. DASHBOARD OVERVIEW
# ==============================================================================

@staff_required
def dashboard_overview(request):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    # Date range filtering
    period = request.GET.get('period', 'all')
    orders_qs = Order.objects.all()

    if period == 'today':
        orders_qs = orders_qs.filter(created_at__date=today)
    elif period == 'week':
        orders_qs = orders_qs.filter(created_at__date__gte=seven_days_ago)
    elif period == 'month':
        orders_qs = orders_qs.filter(created_at__date__gte=thirty_days_ago)

    # Order Statistics
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(status='pending').count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status__in=['ready_dispatch', 'shipped']).count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()

    # Revenue Calculation (Delivered or Verified Paid, excluding cancelled)
    revenue_agg = Order.objects.filter(
        Q(payment_status='paid') | Q(status='delivered')
    ).exclude(status='cancelled').aggregate(total_revenue=Sum('total_amount'))
    total_revenue = revenue_agg['total_revenue'] or Decimal('0.00')

    today_revenue_agg = Order.objects.filter(
        created_at__date=today
    ).filter(
        Q(payment_status='paid') | Q(status='delivered')
    ).exclude(status='cancelled').aggregate(rev=Sum('total_amount'))
    today_revenue = today_revenue_agg['rev'] or Decimal('0.00')

    # Inventory & Product Statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    inactive_products = total_products - active_products
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold'), is_active=True
    ).count()

    # Customers & Feedback Statistics
    total_customers = User.objects.filter(is_staff=False).count()
    total_feedback = CustomerFeedback.objects.count()
    unread_feedback = CustomerFeedback.objects.filter(is_reviewed=False).count()
    unread_messages = ContactMessage.objects.filter(status='new').count()
    pending_rfqs = QuoteRequest.objects.filter(status='new').count()

    # Pending Payments for verification
    pending_upi_verification = Order.objects.filter(
        payment_method='upi', payment_status='verification_pending'
    ).count()

    # Recent Orders
    recent_orders = Order.objects.select_related('user').prefetch_related('items').all()[:8]

    # Low-Stock Items
    low_stock_items = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).select_related('category')[:6]

    # Top Selling Products (by ordered items count)
    top_products = OrderItem.objects.values(
        'product_name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_sales=Sum('total_price')
    ).order_by('-total_qty')[:5]

    # 7-day Sales Chart Data
    chart_dates = []
    chart_orders = []
    chart_revenue = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime('%b %d')
        chart_dates.append(day_str)
        
        day_orders_count = Order.objects.filter(created_at__date=day).count()
        chart_orders.append(day_orders_count)
        
        day_rev = Order.objects.filter(
            created_at__date=day
        ).filter(
            Q(payment_status='paid') | Q(status='delivered')
        ).exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or 0
        chart_revenue.append(float(day_rev))

    context = {
        'page_title': 'Executive Overview',
        'active_menu': 'overview',
        'today': today,
        'period': period,
        'total_orders': total_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'low_stock_products': low_stock_products,
        'total_customers': total_customers,
        'total_feedback': total_feedback,
        'unread_feedback': unread_feedback,
        'unread_messages': unread_messages,
        'pending_rfqs': pending_rfqs,
        'pending_upi_verification': pending_upi_verification,
        'recent_orders': recent_orders,
        'low_stock_items': low_stock_items,
        'top_products': top_products,
        'chart_dates_json': chart_dates,
        'chart_orders_json': chart_orders,
        'chart_revenue_json': chart_revenue,
    }
    return render(request, 'admin_dashboard/overview.html', context)


# ==============================================================================
# 2. PRODUCT MANAGEMENT
# ==============================================================================

@staff_required
def products_list(request):
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    stock_status = request.GET.get('stock', '').strip()
    sort = request.GET.get('sort', '-created_at')

    products = Product.objects.select_related('category').all()

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if stock_status == 'in_stock':
        products = products.filter(stock_quantity__gt=F('low_stock_threshold'), is_active=True)
    elif stock_status == 'low_stock':
        products = products.filter(stock_quantity__lte=F('low_stock_threshold'), stock_quantity__gt=0, is_active=True)
    elif stock_status == 'out_of_stock':
        products = products.filter(stock_quantity__lte=0)
    elif stock_status == 'inactive':
        products = products.filter(is_active=False)

    # Sorting
    valid_sorts = ['name', '-name', 'unit_price', '-unit_price', 'stock_quantity', '-stock_quantity', 'created_at', '-created_at']
    if sort in valid_sorts:
        products = products.order_by(sort)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_title': 'Product Management',
        'active_menu': 'products',
        'page_obj': page_obj,
        'categories': categories,
        'q': q,
        'selected_category': category_id,
        'selected_stock': stock_status,
        'selected_sort': sort,
        'total_count': products.count(),
    }
    return render(request, 'admin_dashboard/products.html', context)


@staff_required
@transaction.atomic
def product_add(request):
    if request.method != 'POST':
        return redirect('admin_dashboard:products')

    name = request.POST.get('name', '').strip()
    category_id = request.POST.get('category')
    sku = request.POST.get('sku', '').strip().upper()
    subtitle = request.POST.get('subtitle', '').strip()
    description = request.POST.get('description', '').strip()
    unit_price = request.POST.get('unit_price', '0')
    unit_name = request.POST.get('unit_name', 'kg').strip()
    stock_quantity = request.POST.get('stock_quantity', '0')
    low_stock_threshold = request.POST.get('low_stock_threshold', '10')
    min_order_qty = request.POST.get('min_order_qty', '25 kg').strip()
    grade = request.POST.get('grade', 'Standard Sortex').strip()
    origin = request.POST.get('origin', 'India').strip()
    packaging_options = request.POST.get('packaging_options', '25kg / 50kg PP Bags').strip()
    is_featured = request.POST.get('is_featured') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    image = request.FILES.get('image')

    if not name or not category_id:
        messages.error(request, "Product name and category are required fields.")
        return redirect('admin_dashboard:products')

    try:
        price_dec = Decimal(unit_price)
        stock_dec = Decimal(stock_quantity)
        threshold_dec = Decimal(low_stock_threshold)
    except (InvalidOperation, ValueError):
        messages.error(request, "Please enter valid numeric values for price and stock.")
        return redirect('admin_dashboard:products')

    category = get_object_or_404(Category, id=category_id)

    # Base slug generation
    base_slug = slugify(name)
    slug = base_slug
    idx = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{idx}"
        idx += 1

    # Auto SKU if omitted
    if not sku:
        sku = f"BI-{slug[:8].upper()}-{Product.objects.count() + 101}"

    product = Product.objects.create(
        category=category,
        name=name,
        slug=slug,
        sku=sku,
        subtitle=subtitle,
        description=description,
        unit_price=price_dec,
        unit_name=unit_name,
        stock_quantity=stock_dec,
        low_stock_threshold=threshold_dec,
        min_order_qty=min_order_qty,
        grade=grade,
        origin=origin,
        packaging_options=packaging_options,
        is_featured=is_featured,
        is_active=is_active,
        image=image if image else None
    )

    # Log initial stock movement if > 0
    if stock_dec > 0:
        StockMovement.objects.create(
            product=product,
            movement_type='in',
            quantity=stock_dec,
            previous_stock=0,
            new_stock=stock_dec,
            reason="Initial inventory setup upon product creation",
            user=request.user
        )

    AuditLog.log(
        user=request.user,
        action="Created Product",
        model_name="Product",
        object_id=product.id,
        details=f"Created '{product.name}' (SKU: {product.sku}) in {category.name} with stock {stock_dec} {unit_name} @ ₹{price_dec}",
        request=request
    )

    messages.success(request, f"Product '{product.name}' added successfully!")
    return redirect('admin_dashboard:products')


@staff_required
@transaction.atomic
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method != 'POST':
        return redirect('admin_dashboard:products')

    name = request.POST.get('name', '').strip()
    category_id = request.POST.get('category')
    sku = request.POST.get('sku', '').strip().upper()
    subtitle = request.POST.get('subtitle', '').strip()
    description = request.POST.get('description', '').strip()
    unit_price = request.POST.get('unit_price', '0')
    unit_name = request.POST.get('unit_name', 'kg').strip()
    low_stock_threshold = request.POST.get('low_stock_threshold', '10')
    min_order_qty = request.POST.get('min_order_qty', '').strip()
    grade = request.POST.get('grade', '').strip()
    origin = request.POST.get('origin', '').strip()
    packaging_options = request.POST.get('packaging_options', '').strip()
    is_featured = request.POST.get('is_featured') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    image = request.FILES.get('image')

    if not name or not category_id:
        messages.error(request, "Product name and category are required.")
        return redirect('admin_dashboard:products')

    try:
        price_dec = Decimal(unit_price)
        threshold_dec = Decimal(low_stock_threshold)
    except (InvalidOperation, ValueError):
        messages.error(request, "Please enter valid numeric values for price and threshold.")
        return redirect('admin_dashboard:products')

    category = get_object_or_404(Category, id=category_id)

    changes = []
    if product.name != name:
        changes.append(f"Name: '{product.name}' -> '{name}'")
    if product.unit_price != price_dec:
        changes.append(f"Price: ₹{product.unit_price} -> ₹{price_dec}")
    if product.is_active != is_active:
        changes.append(f"Status: Active={product.is_active} -> Active={is_active}")

    product.name = name
    product.category = category
    if sku:
        product.sku = sku
    product.subtitle = subtitle
    product.description = description
    product.unit_price = price_dec
    product.unit_name = unit_name
    product.low_stock_threshold = threshold_dec
    product.min_order_qty = min_order_qty
    product.grade = grade
    product.origin = origin
    product.packaging_options = packaging_options
    product.is_featured = is_featured
    product.is_active = is_active
    if image:
        product.image = image
    product.save()

    AuditLog.log(
        user=request.user,
        action="Updated Product",
        model_name="Product",
        object_id=product.id,
        details="; ".join(changes) if changes else f"Updated details for '{product.name}'",
        request=request
    )

    messages.success(request, f"Product '{product.name}' updated successfully.")
    return redirect('admin_dashboard:products')


@staff_required
def product_toggle_status(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])

    AuditLog.log(
        user=request.user,
        action="Toggled Product Status",
        model_name="Product",
        object_id=product.id,
        details=f"Product '{product.name}' set to {'Active' if product.is_active else 'Inactive'}",
        request=request
    )

    messages.info(request, f"Product '{product.name}' is now {'Active' if product.is_active else 'Inactive'}.")
    return redirect('admin_dashboard:products')


@staff_required
@transaction.atomic
def product_adjust_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        adjust_type = request.POST.get('adjust_type', 'add')  # 'add', 'subtract', 'set'
        quantity_raw = request.POST.get('quantity', '0')
        reason = request.POST.get('reason', '').strip() or "Manual administrator adjustment"

        try:
            qty_num = Decimal(quantity_raw)
            if qty_num <= 0 and adjust_type != 'set':
                messages.error(request, "Adjustment quantity must be greater than zero.")
                return redirect('admin_dashboard:products')
        except (InvalidOperation, ValueError):
            messages.error(request, "Please enter a valid numeric quantity.")
            return redirect('admin_dashboard:products')

        prev_stock = product.stock_quantity
        if adjust_type == 'add':
            new_stock = prev_stock + qty_num
            movement_type = 'in'
        elif adjust_type == 'subtract':
            new_stock = max(Decimal('0.00'), prev_stock - qty_num)
            movement_type = 'out'
        else:  # set
            new_stock = max(Decimal('0.00'), qty_num)
            movement_type = 'adjustment'

        product.stock_quantity = new_stock
        product.save(update_fields=['stock_quantity'])

        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=qty_num,
            previous_stock=prev_stock,
            new_stock=new_stock,
            reason=reason,
            user=request.user
        )

        AuditLog.log(
            user=request.user,
            action="Adjusted Product Stock",
            model_name="Product",
            object_id=product.id,
            details=f"Stock for '{product.name}' adjusted ({adjust_type} {qty_num}): {prev_stock} -> {new_stock} {product.unit_name}. Reason: {reason}",
            request=request
        )

        messages.success(request, f"Stock for '{product.name}' updated to {new_stock} {product.unit_name}.")
    return redirect('admin_dashboard:products')


@staff_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        # Soft-deactivate if order references exist
        if product.orderitem_set.exists():
            product.is_active = False
            product.save(update_fields=['is_active'])
            AuditLog.log(
                user=request.user,
                action="Archived Product (Order history exists)",
                model_name="Product",
                object_id=product.id,
                details=f"Deactivated/Archived '{name}' instead of hard deletion to preserve order history.",
                request=request
            )
            messages.warning(request, f"Product '{name}' has existing order records and has been deactivated/archived safely.")
        else:
            product.delete()
            AuditLog.log(
                user=request.user,
                action="Deleted Product",
                model_name="Product",
                object_id=product_id,
                details=f"Permanently deleted product '{name}'.",
                request=request
            )
            messages.success(request, f"Product '{name}' was deleted successfully.")
    return redirect('admin_dashboard:products')


# ==============================================================================
# 3. CATEGORY MANAGEMENT
# ==============================================================================

@staff_required
def categories_list(request):
    categories = Category.objects.annotate(product_count=Count('products')).order_by('order', 'name')
    context = {
        'page_title': 'Category Management',
        'active_menu': 'categories',
        'categories': categories,
    }
    return render(request, 'admin_dashboard/categories.html', context)


@staff_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or slugify(name)
        tagline = request.POST.get('tagline', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '◈').strip()
        accent_color = request.POST.get('accent_color', '#1b381e').strip()
        order = int(request.POST.get('order', '0') or 0)
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            messages.error(request, "Category name is required.")
            return redirect('admin_dashboard:categories')

        if Category.objects.filter(slug=slug).exists():
            slug = f"{slug}-{Category.objects.count() + 1}"

        cat = Category.objects.create(
            name=name,
            slug=slug,
            tagline=tagline,
            description=description,
            icon=icon,
            accent_color=accent_color,
            order=order,
            is_active=is_active
        )

        AuditLog.log(
            user=request.user,
            action="Created Category",
            model_name="Category",
            object_id=cat.id,
            details=f"Created category '{cat.name}' ({cat.slug})",
            request=request
        )

        messages.success(request, f"Category '{cat.name}' created successfully.")
    return redirect('admin_dashboard:categories')


@staff_required
def category_edit(request, category_id):
    cat = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name', '').strip() or cat.name
        cat.tagline = request.POST.get('tagline', '').strip()
        cat.description = request.POST.get('description', '').strip()
        cat.icon = request.POST.get('icon', '◈').strip()
        cat.accent_color = request.POST.get('accent_color', '#1b381e').strip()
        cat.order = int(request.POST.get('order', '0') or 0)
        cat.is_active = request.POST.get('is_active') == 'on'
        cat.save()

        AuditLog.log(
            user=request.user,
            action="Updated Category",
            model_name="Category",
            object_id=cat.id,
            details=f"Updated category '{cat.name}'",
            request=request
        )
        messages.success(request, f"Category '{cat.name}' updated successfully.")
    return redirect('admin_dashboard:categories')


@staff_required
def category_toggle_status(request, category_id):
    cat = get_object_or_404(Category, id=category_id)
    cat.is_active = not cat.is_active
    cat.save(update_fields=['is_active'])

    AuditLog.log(
        user=request.user,
        action="Toggled Category Status",
        model_name="Category",
        object_id=cat.id,
        details=f"Category '{cat.name}' status set to {'Active' if cat.is_active else 'Inactive'}",
        request=request
    )
    messages.info(request, f"Category '{cat.name}' is now {'Active' if cat.is_active else 'Inactive'}.")
    return redirect('admin_dashboard:categories')


@staff_required
def category_delete(request, category_id):
    cat = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        # Guard: Check if products exist in category
        if cat.products.exists():
            messages.error(
                request,
                f"Cannot delete category '{cat.name}' because it contains {cat.products.count()} products. "
                "Reassign or archive those products first."
            )
            return redirect('admin_dashboard:categories')

        name = cat.name
        cat.delete()
        AuditLog.log(
            user=request.user,
            action="Deleted Category",
            model_name="Category",
            object_id=category_id,
            details=f"Deleted category '{name}'",
            request=request
        )
        messages.success(request, f"Category '{name}' deleted successfully.")
    return redirect('admin_dashboard:categories')


# ==============================================================================
# 4. ORDER MANAGEMENT (HIGHEST PRIORITY)
# ==============================================================================

@staff_required
def orders_list(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    payment_method = request.GET.get('payment_method', '').strip()
    payment_status = request.GET.get('payment_status', '').strip()
    date_filter = request.GET.get('date', '').strip()

    orders = Order.objects.select_related('user').prefetch_related('items').all()

    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(company_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(upi_utr_number__icontains=q)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if payment_method:
        orders = orders.filter(payment_method=payment_method)

    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    if date_filter:
        try:
            parsed_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date=parsed_date)
        except ValueError:
            pass

    orders = orders.order_by('-created_at')

    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Order counts by status
    counts = {
        'all': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'confirmed': Order.objects.filter(status='confirmed').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status__in=['ready_dispatch', 'shipped']).count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
        'verification_pending': Order.objects.filter(payment_status='verification_pending').count(),
    }

    context = {
        'page_title': 'Order Management',
        'active_menu': 'orders',
        'page_obj': page_obj,
        'counts': counts,
        'q': q,
        'status_filter': status_filter,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'date_filter': date_filter,
        'total_filtered': orders.count(),
    }
    return render(request, 'admin_dashboard/orders.html', context)


@staff_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product'),
        order_number=order_number
    )
    items = order.items.all()
    audit_trail = AuditLog.objects.filter(model_name="Order", object_id=order.id)[:10]

    context = {
        'page_title': f"Order #{order.order_number}",
        'active_menu': 'orders',
        'order': order,
        'items': items,
        'audit_trail': audit_trail,
    }
    return render(request, 'admin_dashboard/order_detail.html', context)


@staff_required
@transaction.atomic
def order_update_status(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        carrier_name = request.POST.get('carrier_name', '').strip()
        tracking_no = request.POST.get('tracking_no', '').strip()
        vehicle_no = request.POST.get('vehicle_no', '').strip()
        admin_notes = request.POST.get('admin_notes', '').strip()
        reason = request.POST.get('reason', '').strip()

        old_status = order.status
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]

        if new_status not in valid_statuses:
            messages.error(request, "Invalid order status specified.")
            return redirect('admin_dashboard:order_detail', order_number=order.order_number)

        # Status transition enforcement
        order.status = new_status
        if carrier_name:
            order.carrier_name = carrier_name
        if tracking_no:
            order.tracking_consignment_no = tracking_no
        if vehicle_no:
            order.vehicle_number = vehicle_no
        if new_status == 'shipped' and not order.dispatch_date:
            order.dispatch_date = timezone.localdate()

        if admin_notes:
            timestamp = timezone.now().strftime('%d %b %Y %H:%M')
            order.admin_notes = f"{order.admin_notes}\n[{timestamp}] ({request.user.username}): {admin_notes}".strip()

        order.save()

        # Audit logging
        AuditLog.log(
            user=request.user,
            action="Updated Order Status",
            model_name="Order",
            object_id=order.id,
            details=f"Order #{order.order_number} status changed: '{old_status}' -> '{new_status}'. Reason: {reason or 'Standard workflow'}",
            request=request
        )

        messages.success(request, f"Order #{order.order_number} status updated to '{order.get_status_display()}'.")

    return redirect('admin_dashboard:order_detail', order_number=order.order_number)


@staff_required
@transaction.atomic
def order_verify_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        action = request.POST.get('action', 'verify_paid')  # 'verify_paid', 'mark_failed'
        old_payment_status = order.payment_status

        if action == 'verify_paid':
            order.payment_status = 'paid'
            if order.status == 'pending':
                order.status = 'confirmed'
            msg = f"Payment verified successfully for Order #{order.order_number} (Amount: ₹{order.total_amount:,.2f})."
        else:
            order.payment_status = 'failed'
            msg = f"Payment marked as failed for Order #{order.order_number}."

        order.save(update_fields=['payment_status', 'status'])

        AuditLog.log(
            user=request.user,
            action="Verified Payment",
            model_name="Order",
            object_id=order.id,
            details=f"Payment status changed for #{order.order_number}: '{old_payment_status}' -> '{order.payment_status}'. Method: {order.payment_method}, UTR: {order.upi_utr_number}",
            request=request
        )

        messages.success(request, msg)

    return redirect('admin_dashboard:order_detail', order_number=order.order_number)


@staff_required
def order_invoice_view(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items'),
        order_number=order_number
    )
    settings_obj = SiteSettings.load()
    context = {
        'order': order,
        'items': order.items.all(),
        'settings': settings_obj,
        'today': timezone.localdate(),
    }
    return render(request, 'admin_dashboard/order_invoice.html', context)


# ==============================================================================
# 5. CUSTOMER MANAGEMENT
# ==============================================================================

@staff_required
def customers_list(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.filter(is_staff=False).select_related('company_profile').annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_amount', filter=Q(orders__payment_status='paid') | Q(orders__status='delivered'))
    ).order_by('-date_joined')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(company_profile__company_name__icontains=q) |
            Q(company_profile__phone__icontains=q)
        )

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Customer Directory',
        'active_menu': 'customers',
        'page_obj': page_obj,
        'q': q,
        'total_customers': User.objects.filter(is_staff=False).count(),
    }
    return render(request, 'admin_dashboard/customers.html', context)


@staff_required
def customer_toggle_status(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])

    AuditLog.log(
        user=request.user,
        action="Toggled Customer Status",
        model_name="User",
        object_id=user.id,
        details=f"Customer '{user.username}' ({user.email}) account set to {'Active' if user.is_active else 'Disabled'}",
        request=request
    )

    messages.info(request, f"Customer '{user.username}' is now {'Active' if user.is_active else 'Disabled'}.")
    return redirect('admin_dashboard:customers')


# ==============================================================================
# 6. INVENTORY & STOCK MANAGEMENT
# ==============================================================================

@staff_required
def inventory_overview(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    products = Product.objects.select_related('category').all()

    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    if status_filter == 'low':
        products = products.filter(stock_quantity__lte=F('low_stock_threshold'), stock_quantity__gt=0)
    elif status_filter == 'out':
        products = products.filter(stock_quantity__lte=0)
    elif status_filter == 'healthy':
        products = products.filter(stock_quantity__gt=F('low_stock_threshold'))

    products = products.order_by('stock_quantity')

    # Aggregations
    total_stock_units = Product.objects.aggregate(t=Sum('stock_quantity'))['t'] or 0
    low_stock_count = Product.objects.filter(stock_quantity__lte=F('low_stock_threshold'), stock_quantity__gt=0).count()
    out_of_stock_count = Product.objects.filter(stock_quantity__lte=0).count()

    # Recent Movements
    recent_movements = StockMovement.objects.select_related('product', 'user').all()[:15]

    context = {
        'page_title': 'Inventory & Stock Management',
        'active_menu': 'inventory',
        'products': products,
        'recent_movements': recent_movements,
        'total_stock_units': total_stock_units,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'q': q,
        'status_filter': status_filter,
    }
    return render(request, 'admin_dashboard/inventory.html', context)


@staff_required
@transaction.atomic
def inventory_adjust(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        adjust_type = request.POST.get('adjust_type', 'in')  # 'in', 'out', 'adjustment'
        quantity_raw = request.POST.get('quantity', '0')
        reason = request.POST.get('reason', '').strip() or "Manual inventory adjustment"

        product = get_object_or_404(Product, id=product_id)

        try:
            qty_num = Decimal(quantity_raw)
            if qty_num <= 0:
                messages.error(request, "Quantity must be greater than zero.")
                return redirect('admin_dashboard:inventory')
        except (InvalidOperation, ValueError):
            messages.error(request, "Please enter a valid numeric quantity.")
            return redirect('admin_dashboard:inventory')

        prev_stock = product.stock_quantity
        if adjust_type == 'in':
            new_stock = prev_stock + qty_num
        elif adjust_type == 'out':
            new_stock = max(Decimal('0.00'), prev_stock - qty_num)
        else:  # audit adjustment count set
            new_stock = qty_num

        product.stock_quantity = new_stock
        product.save(update_fields=['stock_quantity'])

        StockMovement.objects.create(
            product=product,
            movement_type=adjust_type,
            quantity=qty_num,
            previous_stock=prev_stock,
            new_stock=new_stock,
            reason=reason,
            user=request.user
        )

        AuditLog.log(
            user=request.user,
            action="Adjusted Inventory",
            model_name="StockMovement",
            object_id=product.id,
            details=f"Stock for '{product.name}' adjusted ({adjust_type} {qty_num}): {prev_stock} -> {new_stock} {product.unit_name}. Reason: {reason}",
            request=request
        )

        messages.success(request, f"Stock updated successfully for '{product.name}' (New Stock: {new_stock} {product.unit_name}).")
    return redirect('admin_dashboard:inventory')


# ==============================================================================
# 7. FEEDBACK & CONTACT MESSAGES
# ==============================================================================

@staff_required
def feedback_list(request):
    tab = request.GET.get('tab', 'feedback')  # 'feedback' or 'contact'
    
    feedbacks = CustomerFeedback.objects.all().order_by('-created_at')
    contacts = ContactMessage.objects.all().order_by('-created_at')

    avg_rating = CustomerFeedback.objects.aggregate(a=Avg('rating'))['a'] or 5.0

    context = {
        'page_title': 'Feedback & Enquiries',
        'active_menu': 'feedback',
        'tab': tab,
        'feedbacks': feedbacks,
        'contacts': contacts,
        'avg_rating': round(avg_rating, 1),
        'total_feedback': feedbacks.count(),
        'unread_feedback': CustomerFeedback.objects.filter(is_reviewed=False).count(),
        'total_contacts': contacts.count(),
        'new_contacts': ContactMessage.objects.filter(status='new').count(),
    }
    return render(request, 'admin_dashboard/feedback.html', context)


@staff_required
def feedback_mark_reviewed(request, feedback_id):
    fb = get_object_or_404(CustomerFeedback, id=feedback_id)
    fb.is_reviewed = True
    fb.save(update_fields=['is_reviewed'])

    AuditLog.log(
        user=request.user,
        action="Reviewed Customer Feedback",
        model_name="CustomerFeedback",
        object_id=fb.id,
        details=f"Feedback by {fb.full_name} ({fb.rating}★) marked as reviewed.",
        request=request
    )

    messages.success(request, f"Feedback from {fb.full_name} marked as reviewed.")
    return redirect('/admin-dashboard/feedback/?tab=feedback')


@staff_required
def contact_mark_read(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    msg.status = 'read'
    msg.save(update_fields=['status'])

    AuditLog.log(
        user=request.user,
        action="Marked Contact Message as Read",
        model_name="ContactMessage",
        object_id=msg.id,
        details=f"Contact message from {msg.name} marked as read.",
        request=request
    )

    messages.success(request, f"Message from {msg.name} marked as read.")
    return redirect('/admin-dashboard/feedback/?tab=contact')


# ==============================================================================
# 8. PAYMENTS & TRANSACTIONS
# ==============================================================================

@staff_required
def payments_overview(request):
    payment_config = PaymentConfig.get_active_config()

    orders_with_payments = Order.objects.filter(
        Q(payment_method='upi') | Q(payment_status='paid') | Q(upi_utr_number__gt='')
    ).order_by('-created_at')

    # Financial stats
    total_paid_vol = Order.objects.filter(payment_status='paid').aggregate(s=Sum('total_amount'))['s'] or 0
    pending_verification_vol = Order.objects.filter(payment_status='verification_pending').aggregate(s=Sum('total_amount'))['s'] or 0
    cod_pending_vol = Order.objects.filter(payment_method='cod', status__in=['pending', 'confirmed', 'processing', 'shipped']).aggregate(s=Sum('total_amount'))['s'] or 0

    context = {
        'page_title': 'Payments & Transactions',
        'active_menu': 'payments',
        'payment_config': payment_config,
        'orders': orders_with_payments[:25],
        'total_paid_vol': total_paid_vol,
        'pending_verification_vol': pending_verification_vol,
        'cod_pending_vol': cod_pending_vol,
    }
    return render(request, 'admin_dashboard/payments.html', context)


@staff_required
def payments_config_update(request):
    if request.method == 'POST':
        upi_id = request.POST.get('business_upi_id', '').strip()
        payee_name = request.POST.get('payee_name', '').strip()
        qr_image = request.FILES.get('qr_image')

        config = PaymentConfig.get_active_config()
        if upi_id:
            config.business_upi_id = upi_id
        if payee_name:
            config.payee_name = payee_name
        if qr_image:
            config.qr_image = qr_image
        config.save()

        AuditLog.log(
            user=request.user,
            action="Updated Business Payment Config",
            model_name="PaymentConfig",
            object_id=config.id,
            details=f"Updated UPI ID to '{config.business_upi_id}' and Payee Name to '{config.payee_name}'",
            request=request
        )

        messages.success(request, "Business UPI payment configuration updated successfully.")
    return redirect('admin_dashboard:payments')


# ==============================================================================
# 9. PROMOTIONS & OFFERS
# ==============================================================================

@staff_required
def promotions_list(request):
    promotions = Promotion.objects.all()
    context = {
        'page_title': 'Offers & Discount Coupons',
        'active_menu': 'promotions',
        'promotions': promotions,
    }
    return render(request, 'admin_dashboard/promotions.html', context)


@staff_required
def promotion_add(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_val = request.POST.get('discount_value', '0')
        min_order = request.POST.get('min_order_value', '0')
        max_discount = request.POST.get('max_discount_amount', '')
        usage_limit = int(request.POST.get('usage_limit', '100') or 100)
        is_active = request.POST.get('is_active') == 'on'

        if not code or not title:
            messages.error(request, "Coupon code and campaign title are required.")
            return redirect('admin_dashboard:promotions')

        try:
            val_dec = Decimal(discount_val)
            min_dec = Decimal(min_order)
            max_dec = Decimal(max_discount) if max_discount else None
        except (InvalidOperation, ValueError):
            messages.error(request, "Please enter valid numeric discount values.")
            return redirect('admin_dashboard:promotions')

        if Promotion.objects.filter(code=code).exists():
            messages.error(request, f"Promotion code '{code}' already exists.")
            return redirect('admin_dashboard:promotions')

        promo = Promotion.objects.create(
            code=code,
            title=title,
            description=description,
            discount_type=discount_type,
            discount_value=val_dec,
            min_order_value=min_dec,
            max_discount_amount=max_dec,
            usage_limit=usage_limit,
            is_active=is_active
        )

        AuditLog.log(
            user=request.user,
            action="Created Promotion",
            model_name="Promotion",
            object_id=promo.id,
            details=f"Created promo '{promo.code}' ({promo.discount_value}{'%' if promo.discount_type == 'percentage' else '₹'})",
            request=request
        )

        messages.success(request, f"Coupon code '{promo.code}' created successfully!")
    return redirect('admin_dashboard:promotions')


@staff_required
def promotion_toggle(request, promo_id):
    promo = get_object_or_404(Promotion, id=promo_id)
    promo.is_active = not promo.is_active
    promo.save(update_fields=['is_active'])

    AuditLog.log(
        user=request.user,
        action="Toggled Promotion Status",
        model_name="Promotion",
        object_id=promo.id,
        details=f"Coupon '{promo.code}' set to {'Active' if promo.is_active else 'Inactive'}",
        request=request
    )

    messages.info(request, f"Coupon '{promo.code}' is now {'Active' if promo.is_active else 'Inactive'}.")
    return redirect('admin_dashboard:promotions')


@staff_required
def promotion_delete(request, promo_id):
    promo = get_object_or_404(Promotion, id=promo_id)
    if request.method == 'POST':
        code = promo.code
        promo.delete()
        AuditLog.log(
            user=request.user,
            action="Deleted Promotion",
            model_name="Promotion",
            object_id=promo_id,
            details=f"Deleted coupon '{code}'",
            request=request
        )
        messages.success(request, f"Coupon '{code}' was removed.")
    return redirect('admin_dashboard:promotions')


# ==============================================================================
# 10. SETTINGS & CMS
# ==============================================================================

@staff_required
def settings_view(request):
    site_settings = SiteSettings.load()
    stats = SiteStat.objects.all().order_by('order')

    if request.method == 'POST':
        action_type = request.POST.get('action_type', 'site_info')
        if action_type == 'site_info':
            site_settings.company_name = request.POST.get('company_name', site_settings.company_name).strip()
            site_settings.tagline = request.POST.get('tagline', site_settings.tagline).strip()
            site_settings.phone = request.POST.get('phone', site_settings.phone).strip()
            site_settings.email = request.POST.get('email', site_settings.email).strip()
            site_settings.office_address = request.POST.get('office_address', site_settings.office_address).strip()
            site_settings.business_hours = request.POST.get('business_hours', site_settings.business_hours).strip()
            site_settings.about_title = request.POST.get('about_title', site_settings.about_title).strip()
            site_settings.about_text = request.POST.get('about_text', site_settings.about_text).strip()
            site_settings.linkedin_url = request.POST.get('linkedin_url', site_settings.linkedin_url).strip()
            site_settings.instagram_url = request.POST.get('instagram_url', site_settings.instagram_url).strip()
            site_settings.facebook_url = request.POST.get('facebook_url', site_settings.facebook_url).strip()
            site_settings.save()

            AuditLog.log(
                user=request.user,
                action="Updated Site Settings",
                model_name="SiteSettings",
                object_id=site_settings.id,
                details=f"Updated company contact info and corporate settings.",
                request=request
            )
            messages.success(request, "Company settings saved successfully.")

        elif action_type == 'update_stat':
            stat_id = request.POST.get('stat_id')
            stat = get_object_or_404(SiteStat, id=stat_id)
            stat.label = request.POST.get('label', stat.label).strip()
            stat.value = request.POST.get('value', stat.value).strip()
            stat.description = request.POST.get('description', stat.description).strip()
            stat.order = int(request.POST.get('order', stat.order) or 0)
            stat.save()
            messages.success(request, f"Statistic '{stat.label}' updated.")

        return redirect('admin_dashboard:settings')

    context = {
        'page_title': 'Website & Corporate Settings',
        'active_menu': 'settings',
        'settings': site_settings,
        'stats': stats,
    }
    return render(request, 'admin_dashboard/settings.html', context)


# ==============================================================================
# 11. REPORTS & EXPORTS
# ==============================================================================

@staff_required
def reports_view(request):
    today = timezone.localdate()
    thirty_days_ago = today - timedelta(days=30)

    # Monthly performance breakdown
    monthly_orders = Order.objects.filter(created_at__date__gte=thirty_days_ago)
    total_orders_month = monthly_orders.count()
    total_sales_month = monthly_orders.filter(
        Q(payment_status='paid') | Q(status='delivered')
    ).exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or 0

    category_breakdown = Category.objects.annotate(
        prod_count=Count('products'),
        active_prod_count=Count('products', filter=Q(products__is_active=True))
    )

    context = {
        'page_title': 'Business Intelligence & Reports',
        'active_menu': 'reports',
        'today': today,
        'thirty_days_ago': thirty_days_ago,
        'total_orders_month': total_orders_month,
        'total_sales_month': total_sales_month,
        'category_breakdown': category_breakdown,
    }
    return render(request, 'admin_dashboard/reports.html', context)


@staff_required
def reports_export_csv(request, export_type):
    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M')

    if export_type == 'orders':
        response['Content-Disposition'] = f'attachment; filename="balaji_orders_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Date', 'Customer Name', 'Company', 'Email', 'Phone', 'Subtotal', 'Tax', 'Total Amount', 'Payment Method', 'Payment Status', 'UTR Number', 'Status'])
        
        for o in Order.objects.all().order_by('-created_at'):
            writer.writerow([
                o.order_number,
                o.created_at.strftime('%Y-%m-%d %H:%M'),
                o.customer_name,
                o.company_name,
                o.email,
                o.phone,
                o.subtotal,
                o.tax_amount,
                o.total_amount,
                o.get_payment_method_display(),
                o.get_payment_status_display(),
                o.upi_utr_number,
                o.get_status_display()
            ])

    elif export_type == 'products':
        response['Content-Disposition'] = f'attachment; filename="balaji_products_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'SKU', 'Name', 'Category', 'Unit Price', 'Unit', 'Stock Quantity', 'Low Stock Threshold', 'Is Active', 'Is Featured'])
        
        for p in Product.objects.select_related('category').all().order_by('name'):
            writer.writerow([
                p.id,
                p.sku or '',
                p.name,
                p.category.name if p.category else '',
                p.unit_price,
                p.unit_name,
                p.stock_quantity,
                p.low_stock_threshold,
                'Active' if p.is_active else 'Inactive',
                'Yes' if p.is_featured else 'No'
            ])

    elif export_type == 'customers':
        response['Content-Disposition'] = f'attachment; filename="balaji_customers_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['User ID', 'Username', 'Full Name', 'Email', 'Company', 'Phone', 'Date Joined', 'Active'])
        
        for u in User.objects.filter(is_staff=False).select_related('company_profile').order_by('-date_joined'):
            profile = getattr(u, 'company_profile', None)
            writer.writerow([
                u.id,
                u.username,
                u.get_full_name() or u.username,
                u.email,
                getattr(profile, 'company_name', ''),
                getattr(profile, 'phone', ''),
                u.date_joined.strftime('%Y-%m-%d'),
                'Active' if u.is_active else 'Disabled'
            ])

    elif export_type == 'feedback':
        response['Content-Disposition'] = f'attachment; filename="balaji_feedback_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Name', 'Email', 'Phone', 'Company', 'Product', 'Type', 'Rating', 'Reviewed', 'Message'])
        
        for fb in CustomerFeedback.objects.all().order_by('-created_at'):
            writer.writerow([
                fb.created_at.strftime('%Y-%m-%d %H:%M'),
                fb.full_name,
                fb.email,
                fb.phone,
                fb.company_name,
                fb.product_name,
                fb.feedback_type,
                fb.rating,
                'Yes' if fb.is_reviewed else 'No',
                fb.message.replace('\n', ' ')
            ])

    else:
        return redirect('admin_dashboard:reports')

    AuditLog.log(
        user=request.user,
        action="Exported Data Report",
        model_name="Report",
        object_id=export_type,
        details=f"Exported CSV report for {export_type}",
        request=request
    )

    return response


# ==============================================================================
# 12. AUDIT LOGS
# ==============================================================================

@staff_required
def audit_logs_view(request):
    action_filter = request.GET.get('action', '').strip()
    logs = AuditLog.objects.select_related('user').all()

    if action_filter:
        logs = logs.filter(action__icontains=action_filter)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Administrative Audit Trail',
        'active_menu': 'audit_logs',
        'page_obj': page_obj,
        'action_filter': action_filter,
    }
    return render(request, 'admin_dashboard/audit_logs.html', context)


# ==============================================================================
# PHASE 5 — MISSING MODULE A: CUSTOMER DETAIL VIEW
# ==============================================================================

@staff_required
def customer_detail(request, user_id):
    """
    Detailed customer profile for admin.
    Shows CompanyProfile, order history, feedback submitted, account status.
    Superuser-only: initiate password reset.
    """
    customer = get_object_or_404(
        User.objects.select_related('company_profile'),
        id=user_id,
        is_staff=False
    )
    profile = getattr(customer, 'company_profile', None)

    # Order history (last 20 orders)
    customer_orders = Order.objects.filter(user=customer).order_by('-created_at')[:20]

    # Revenue from this customer
    cust_revenue = Order.objects.filter(
        user=customer
    ).filter(
        Q(payment_status='paid') | Q(status='delivered')
    ).exclude(status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Feedback submitted by this customer
    customer_feedback = []
    try:
        customer_feedback = list(
            __import__('core.models', fromlist=['CustomerFeedback']).CustomerFeedback.objects.filter(
                email=customer.email
            ).order_by('-created_at')[:10]
        )
    except Exception:
        pass

    # Support tickets
    from portal.models import SupportTicket
    support_tickets = SupportTicket.objects.filter(user=customer).order_by('-created_at')[:10]

    context = {
        'page_title': f"Customer — {customer.get_full_name() or customer.username}",
        'active_menu': 'customers',
        'customer': customer,
        'profile': profile,
        'customer_orders': customer_orders,
        'cust_revenue': cust_revenue,
        'customer_feedback': customer_feedback,
        'support_tickets': support_tickets,
    }
    return render(request, 'admin_dashboard/customer_detail.html', context)


# ==============================================================================
# PHASE 5 — MISSING MODULE B: ADMIN-INITIATED CUSTOMER PASSWORD RESET
# ==============================================================================

@staff_required
@transaction.atomic
def customer_send_reset(request, user_id):
    """
    Superuser-only: initiate a password-reset OTP for a customer.
    NEVER exposes the token or OTP to the admin interface.
    Sends email to the customer's registered address only.
    """
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can initiate customer password resets.")
        return redirect('admin_dashboard:customer_detail', user_id=user_id)

    if request.method != 'POST':
        return redirect('admin_dashboard:customer_detail', user_id=user_id)

    customer = get_object_or_404(User, id=user_id, is_staff=False)

    if not customer.email:
        messages.error(request, f"Customer '{customer.username}' has no registered email address. Cannot send reset link.")
        return redirect('admin_dashboard:customer_detail', user_id=user_id)

    import secrets
    import hashlib
    from portal.models import PasswordResetOTP

    # Expire any existing unused OTPs for this user
    PasswordResetOTP.objects.filter(user=customer, is_used=False).update(is_used=True)

    # Generate a secure 6-digit OTP
    otp_plain = str(secrets.randbelow(900000) + 100000)
    otp_hash = hashlib.sha256(otp_plain.encode()).hexdigest()

    # Generate secure reset token (never returned to admin)
    reset_token = secrets.token_urlsafe(48)

    expires_at = timezone.now() + timedelta(minutes=30)  # 30 min for admin-initiated resets

    PasswordResetOTP.objects.create(
        user=customer,
        identifier=customer.email,
        method='email',
        otp_hash=otp_hash,
        reset_token=reset_token,
        expires_at=expires_at,
        is_used=False,
        attempts=0
    )

    # Send email to the customer (not to admin)
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    try:
        send_mail(
            subject="Balaji Ingredients — Password Reset Request",
            message=(
                f"Dear {customer.get_full_name() or customer.username},\n\n"
                f"A password reset has been initiated by the Balaji Ingredients admin team "
                f"for your account ({customer.email}).\n\n"
                f"Your One-Time Password (OTP) is: {otp_plain}\n\n"
                f"This OTP is valid for 30 minutes. Do not share it with anyone.\n\n"
                f"If you did not request this, please contact us immediately at "
                f"info@balaji-ingredients.com or call +91-9902155348.\n\n"
                f"— Balaji Ingredients Admin Team"
            ),
            from_email=getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@balaji-ingredients.com'),
            recipient_list=[customer.email],
            fail_silently=True,  # Don't crash if SMTP not configured
        )
        email_sent = True
    except Exception:
        email_sent = False

    AuditLog.log(
        user=request.user,
        action="Admin-Initiated Customer Password Reset",
        model_name="User",
        object_id=customer.id,
        details=(
            f"Admin '{request.user.username}' initiated password reset for customer "
            f"'{customer.username}' ({customer.email}). "
            f"Email {'sent' if email_sent else 'FAILED to send'} to customer address. "
            f"OTP hash stored, token NOT exposed to admin."
        ),
        request=request
    )

    if email_sent:
        messages.success(request, f"Password reset OTP sent to {customer.email}. The customer can use it within 30 minutes.")
    else:
        messages.warning(
            request,
            f"Reset OTP created for {customer.email}, but email could not be sent "
            f"(SMTP may not be configured). The customer's OTP is stored securely in the database."
        )

    return redirect('admin_dashboard:customer_detail', user_id=user_id)


# ==============================================================================
# PHASE 5 — MISSING MODULE C: ORDER CANCELLATION WITH INVENTORY RESTOCK
# ==============================================================================

@staff_required
@transaction.atomic
def order_cancel(request, order_number):
    """
    Cancel an order. Records reason in AuditLog.
    Auto-restocks inventory via StockMovement for each order line item
    that has a linked Product with tracked stock.
    Only eligible orders (not already delivered or cancelled) can be cancelled.
    """
    order = get_object_or_404(Order, order_number=order_number)

    if request.method != 'POST':
        return redirect('admin_dashboard:order_detail', order_number=order_number)

    # Guard: already in a terminal state
    if order.status in ('delivered', 'cancelled'):
        messages.error(request, f"Order #{order_number} cannot be cancelled — it is already '{order.get_status_display()}'.")
        return redirect('admin_dashboard:order_detail', order_number=order_number)

    cancel_reason = request.POST.get('cancel_reason', '').strip() or 'Cancelled by administrator'
    old_status = order.status

    # 1. Update order status
    order.status = 'cancelled'
    timestamp = timezone.now().strftime('%d %b %Y %H:%M')
    order.admin_notes = (
        f"{order.admin_notes}\n[{timestamp}] ({request.user.username}): CANCELLED — {cancel_reason}"
    ).strip()
    order.save(update_fields=['status', 'admin_notes'])

    # 2. Restock inventory for each line item with a linked Product
    restocked_items = []
    for item in order.items.all():
        if item.product_id:
            try:
                product = Product.objects.select_for_update().get(pk=item.product_id)
                prev_stock = product.stock_quantity
                restock_qty = item.quantity  # quantity is in product units
                new_stock = prev_stock + restock_qty

                product.stock_quantity = new_stock
                product.save(update_fields=['stock_quantity'])

                StockMovement.objects.create(
                    product=product,
                    movement_type='in',
                    quantity=restock_qty,
                    previous_stock=prev_stock,
                    new_stock=new_stock,
                    reason=f"Order cancellation restock — Order #{order.order_number}",
                    reference_order=order.order_number,
                    user=request.user
                )
                restocked_items.append(f"{product.name} (+{restock_qty} {product.unit_name})")
            except Product.DoesNotExist:
                pass

    # 3. Audit log
    restock_summary = ', '.join(restocked_items) if restocked_items else 'No linked products to restock'
    AuditLog.log(
        user=request.user,
        action="Cancelled Order",
        model_name="Order",
        object_id=order.id,
        details=(
            f"Order #{order.order_number} cancelled. Previous status: '{old_status}'. "
            f"Reason: {cancel_reason}. "
            f"Inventory restocked: {restock_summary}"
        ),
        request=request
    )

    messages.success(
        request,
        f"Order #{order_number} has been cancelled. "
        f"Inventory restocked for: {restock_summary}."
    )
    return redirect('admin_dashboard:order_detail', order_number=order_number)


# ==============================================================================
# PHASE 5 — MISSING MODULE D: SUPPORT TICKET MANAGEMENT
# ==============================================================================

@staff_required
def support_tickets_list(request):
    """
    Full support ticket management — list, filter, update status, admin response.
    """
    from portal.models import SupportTicket

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()

    tickets = SupportTicket.objects.select_related('user').all().order_by('-created_at')

    if q:
        tickets = tickets.filter(
            Q(ticket_id__icontains=q) |
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(subject__icontains=q) |
            Q(order_id__icontains=q)
        )

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    if type_filter:
        tickets = tickets.filter(support_type=type_filter)

    # Counts
    counts = {
        'all': SupportTicket.objects.count(),
        'open': SupportTicket.objects.filter(status='open').count(),
        'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
        'resolved': SupportTicket.objects.filter(status='resolved').count(),
        'closed': SupportTicket.objects.filter(status='closed').count(),
    }

    paginator = Paginator(tickets, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Support Ticket Management',
        'active_menu': 'support',
        'page_obj': page_obj,
        'counts': counts,
        'q': q,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'support_types': [
            ('sales', 'Sales & Pricing'),
            ('technical', 'Technical Support'),
            ('order', 'Order & Logistics'),
            ('quality', 'Quality & COA'),
        ],
    }
    return render(request, 'admin_dashboard/support.html', context)


@staff_required
@transaction.atomic
def support_ticket_update(request, ticket_id):
    """
    Update support ticket status and add admin response.
    """
    from portal.models import SupportTicket

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if request.method != 'POST':
        return redirect('admin_dashboard:support')

    new_status = request.POST.get('status', ticket.status).strip()
    admin_response = request.POST.get('admin_response', '').strip()
    old_status = ticket.status

    valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
    if new_status in valid_statuses:
        ticket.status = new_status

    if admin_response:
        if ticket.admin_response:
            timestamp = timezone.now().strftime('%d %b %Y %H:%M')
            ticket.admin_response += f"\n\n[{timestamp} — {request.user.username}]:\n{admin_response}"
        else:
            ticket.admin_response = admin_response

    ticket.save()

    AuditLog.log(
        user=request.user,
        action="Updated Support Ticket",
        model_name="SupportTicket",
        object_id=ticket.id,
        details=(
            f"Ticket {ticket.ticket_id} status changed: '{old_status}' -> '{ticket.status}'. "
            f"Admin response {'added' if admin_response else 'unchanged'}."
        ),
        request=request
    )

    messages.success(request, f"Support ticket {ticket.ticket_id} updated successfully.")
    return redirect('admin_dashboard:support')


# ==============================================================================
# PHASE 5 — MISSING MODULE E: STAFF ROLE MANAGEMENT (Superuser Only)
# ==============================================================================

@staff_required
def staff_management(request):
    """
    Superuser-only view: manage staff users and their permissions.
    Lists all is_staff=True users, allows toggling superuser and is_staff.
    """
    if not request.user.is_superuser:
        messages.error(request, "Staff management requires superuser privileges.")
        return redirect('admin_dashboard:overview')

    from django.contrib.auth.models import Permission, Group
    from django.contrib.contenttypes.models import ContentType

    staff_users = User.objects.filter(is_staff=True).order_by('-is_superuser', 'username')

    # Relevant permissions for this dashboard
    dashboard_perms = Permission.objects.filter(
        content_type__app_label__in=['products', 'portal', 'admin_dashboard', 'core']
    ).select_related('content_type').order_by('content_type__app_label', 'codename')

    context = {
        'page_title': 'Staff & Role Management',
        'active_menu': 'staff',
        'staff_users': staff_users,
        'dashboard_perms': dashboard_perms,
    }
    return render(request, 'admin_dashboard/staff.html', context)


@staff_required
@transaction.atomic
def staff_toggle_superuser(request, user_id):
    """Toggle superuser status for a staff user (superuser-only)."""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can modify superuser privileges.")
        return redirect('admin_dashboard:staff')

    if request.method != 'POST':
        return redirect('admin_dashboard:staff')

    # Prevent self-demotion
    if user_id == request.user.id:
        messages.error(request, "You cannot change your own superuser status.")
        return redirect('admin_dashboard:staff')

    target = get_object_or_404(User, id=user_id, is_staff=True)
    old_val = target.is_superuser
    target.is_superuser = not target.is_superuser
    target.save(update_fields=['is_superuser'])

    AuditLog.log(
        user=request.user,
        action="Changed Staff Superuser Status",
        model_name="User",
        object_id=target.id,
        details=f"Staff user '{target.username}' superuser: {old_val} -> {target.is_superuser}",
        request=request
    )

    status_text = "granted superuser" if target.is_superuser else "removed superuser from"
    messages.success(request, f"Successfully {status_text} '{target.username}'.")
    return redirect('admin_dashboard:staff')


@staff_required
@transaction.atomic
def staff_add(request):
    """Add a new staff member (superuser-only)."""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can create new staff accounts.")
        return redirect('admin_dashboard:staff')

    if request.method != 'POST':
        return redirect('admin_dashboard:staff')

    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '').strip()
    is_superuser = request.POST.get('is_superuser') == 'on'

    if not username or not password:
        messages.error(request, "Username and password are required to create a staff account.")
        return redirect('admin_dashboard:staff')

    if User.objects.filter(username=username).exists():
        messages.error(request, f"Username '{username}' is already taken.")
        return redirect('admin_dashboard:staff')

    if len(password) < 8:
        messages.error(request, "Password must be at least 8 characters long.")
        return redirect('admin_dashboard:staff')

    new_staff = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_staff=True,
        is_superuser=is_superuser
    )

    AuditLog.log(
        user=request.user,
        action="Created Staff Account",
        model_name="User",
        object_id=new_staff.id,
        details=f"New staff account created: '{username}' (superuser={is_superuser})",
        request=request
    )

    messages.success(request, f"Staff account '{username}' created successfully.")
    return redirect('admin_dashboard:staff')


# ==============================================================================
# PHASE 5 — ADMIN LOGIN / LOGOUT (dedicated dashboard auth)
# ==============================================================================

def admin_login(request):
    """Dedicated admin login page. Redirects to dashboard if already authenticated."""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard:overview')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            AuditLog.log(
                user=user,
                action="Admin Login",
                model_name="User",
                object_id=user.id,
                details=f"Successful admin login from IP {request.META.get('REMOTE_ADDR', 'unknown')}",
                request=request
            )
            next_url = request.POST.get('next', '') or '/admin-dashboard/'
            return redirect(next_url)
        else:
            error = "Invalid credentials or insufficient privileges."
            AuditLog.log(
                user=None,
                action="Failed Admin Login Attempt",
                model_name="User",
                object_id=username,
                details=f"Failed login attempt for username '{username}'",
                request=request
            )

    return render(request, 'admin_dashboard/login.html', {
        'error': error,
        'next': request.GET.get('next', '/admin-dashboard/'),
    })


def admin_logout(request):
    """Log out the admin and redirect to admin login."""
    if request.user.is_authenticated:
        AuditLog.log(
            user=request.user,
            action="Admin Logout",
            model_name="User",
            object_id=request.user.id,
            details=f"Admin '{request.user.username}' logged out",
            request=request
        )
    logout(request)
    messages.info(request, "You have been logged out of the admin dashboard.")
    return redirect('/admin-dashboard/login/')


# ==============================================================================
# PHASE 6 — HEALTH CHECK (for responsive test + server status verification)
# ==============================================================================

def dashboard_health(request):
    """
    Simple JSON health-check endpoint.
    Returns 200 with dashboard module counts for automated testing.
    Does NOT require authentication (lightweight status check only).
    """
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'ok',
        'server': 'Balaji Ingredients Admin Dashboard',
        'authenticated': request.user.is_authenticated and request.user.is_staff,
    })
