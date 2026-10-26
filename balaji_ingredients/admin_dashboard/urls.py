from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # ── Authentication ─────────────────────────────────────────────────────────
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),

    # ── Dashboard Overview ──────────────────────────────────────────────────────
    path('', views.dashboard_overview, name='overview'),

    # ── Health Check (Phase 6 testing endpoint) ─────────────────────────────────
    path('health/', views.dashboard_health, name='health'),

    # ── Product Management ──────────────────────────────────────────────────────
    path('products/', views.products_list, name='products'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:product_id>/toggle-status/', views.product_toggle_status, name='product_toggle_status'),
    path('products/<int:product_id>/adjust-stock/', views.product_adjust_stock, name='product_adjust_stock'),

    # ── Category Management ─────────────────────────────────────────────────────
    path('categories/', views.categories_list, name='categories'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('categories/<int:category_id>/toggle-status/', views.category_toggle_status, name='category_toggle_status'),

    # ── Order Management ────────────────────────────────────────────────────────
    path('orders/', views.orders_list, name='orders'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/update-status/', views.order_update_status, name='order_update_status'),
    path('orders/<str:order_number>/verify-payment/', views.order_verify_payment, name='order_verify_payment'),
    path('orders/<str:order_number>/cancel/', views.order_cancel, name='order_cancel'),          # Phase 5
    path('orders/<str:order_number>/invoice/', views.order_invoice_view, name='order_invoice'),

    # ── Customer Management ─────────────────────────────────────────────────────
    path('customers/', views.customers_list, name='customers'),
    path('customers/<int:user_id>/', views.customer_detail, name='customer_detail'),             # Phase 5
    path('customers/<int:user_id>/toggle-status/', views.customer_toggle_status, name='customer_toggle_status'),
    path('customers/<int:user_id>/send-reset/', views.customer_send_reset, name='customer_send_reset'),  # Phase 5

    # ── Inventory Management ────────────────────────────────────────────────────
    path('inventory/', views.inventory_overview, name='inventory'),
    path('inventory/adjust/', views.inventory_adjust, name='inventory_adjust'),

    # ── Feedback & Inquiries ────────────────────────────────────────────────────
    path('feedback/', views.feedback_list, name='feedback'),
    path('feedback/<int:feedback_id>/mark-reviewed/', views.feedback_mark_reviewed, name='feedback_mark_reviewed'),
    path('feedback/contact/<int:message_id>/mark-read/', views.contact_mark_read, name='contact_mark_read'),

    # ── Support Tickets (Phase 5) ───────────────────────────────────────────────
    path('support/', views.support_tickets_list, name='support'),
    path('support/<int:ticket_id>/update/', views.support_ticket_update, name='support_ticket_update'),

    # ── Payments & Transactions ─────────────────────────────────────────────────
    path('payments/', views.payments_overview, name='payments'),
    path('payments/config/', views.payments_config_update, name='payments_config_update'),

    # ── Promotions & Offers ─────────────────────────────────────────────────────
    path('promotions/', views.promotions_list, name='promotions'),
    path('promotions/add/', views.promotion_add, name='promotion_add'),
    path('promotions/<int:promo_id>/toggle/', views.promotion_toggle, name='promotion_toggle'),
    path('promotions/<int:promo_id>/delete/', views.promotion_delete, name='promotion_delete'),

    # ── Settings & CMS ─────────────────────────────────────────────────────────
    path('settings/', views.settings_view, name='settings'),

    # ── Reports & Exports ───────────────────────────────────────────────────────
    path('reports/', views.reports_view, name='reports'),
    path('reports/export/<str:export_type>/', views.reports_export_csv, name='reports_export_csv'),

    # ── Staff & Role Management (Phase 5) ───────────────────────────────────────
    path('staff/', views.staff_management, name='staff'),
    path('staff/add/', views.staff_add, name='staff_add'),
    path('staff/<int:user_id>/toggle-superuser/', views.staff_toggle_superuser, name='staff_toggle_superuser'),

    # ── Audit Logs ──────────────────────────────────────────────────────────────
    path('audit-logs/', views.audit_logs_view, name='audit_logs'),
]
