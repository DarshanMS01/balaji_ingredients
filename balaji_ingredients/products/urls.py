"""
products/urls.py
URL routing for product catalog and RFQ endpoints.
"""

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.catalog_list, name='catalog'),
    path('buy/<int:product_id>/', views.buy_product_view, name='buy_product'),
    path('quote/', views.quote_request_view, name='quote_request'),
    path('api/payment-config/', views.payment_config_api, name='payment_config_api'),

    # Session Cart & Checkout (added for Add to Cart / Buy Now flow)
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add_view, name='cart_add'),
    path('cart/update/', views.cart_update_view, name='cart_update'),
    path('api/booking/', views.booking_action_api, name='booking_action_api'),
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-confirmation/<str:order_number>/', views.order_confirmation_view, name='order_confirmation'),
    path('payment/<str:order_number>/', views.order_payment_view, name='order_payment'),
    path('api/order-status/<str:order_number>/', views.order_status_api, name='order_status_api'),
    path('api/order-method/<str:order_number>/', views.order_update_method_api, name='order_update_method_api'),
    path('api/order-utr/<str:order_number>/', views.order_submit_utr_api, name='order_submit_utr_api'),
    path('api/payment-create/<str:order_number>/', views.payment_create_api, name='payment_create_api'),
    path('api/payment-verify/<str:order_number>/', views.payment_verify_api, name='payment_verify_api'),
    path('api/payment-webhook/', views.payment_webhook_view, name='payment_webhook_view'),

    path('<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
]

