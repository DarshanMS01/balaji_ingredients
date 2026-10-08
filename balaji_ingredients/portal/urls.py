"""
portal/urls.py
Routing for Client Portal authentication, dashboard, orders, quotes, documents, profile, notifications, and support.
"""

from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    # Dashboard & Root
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_direct'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/google/', views.google_oauth_redirect, name='google_login'),
    path('auth/google/callback/', views.google_oauth_callback, name='google_callback'),
    
    # Core Portal Modules
    path('products/', views.products_view, name='products'),
    path('products/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('orders/', views.orders_view, name='orders'),
    path('quotes/', views.quotes_view, name='quotes'),
    path('quotes/submit/', views.submit_quote_api, name='submit_quote_api'),
    path('documents/', views.documents_view, name='documents'),
    path('profile/', views.profile_view, name='profile'),
    path('customers/', views.customers_view, name='customers'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('support/', views.support_view, name='support'),
]
