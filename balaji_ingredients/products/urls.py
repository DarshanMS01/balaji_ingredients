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
    path('<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
]

