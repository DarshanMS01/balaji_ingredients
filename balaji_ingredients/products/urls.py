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
    path('checkout/', views.checkout_view, name='checkout'),

    path('<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
]

