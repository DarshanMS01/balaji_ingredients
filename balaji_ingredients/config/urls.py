from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from portal import views as portal_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Direct Login page routes (serving luxury split-card login)
    path('login/', portal_views.login_page_view, name='login'),
    path('login.html', portal_views.login_page_view, name='login_html'),
    path('signup/', portal_views.login_page_view, name='signup'),
    path('logout/', portal_views.logout_view, name='logout'),
    
    # Direct Homepage routes
    path('', portal_views.home_page_view, name='home'),
    path('index.html', portal_views.home_page_view, name='index_html'),
    
    # Direct Dashboard routes
    path('dashboard/', portal_views.dashboard_page_view, name='dashboard'),
    path('dashboard.html', portal_views.dashboard_page_view, name='dashboard_html'),

    # Customer Feedback routes
    path('feedback/', portal_views.feedback_page_view, name='feedback'),
    path('feedback.html', portal_views.feedback_page_view, name='feedback_html'),
    path('feedback', portal_views.feedback_page_view, name='feedback_no_slash'),

    # Official Google OAuth 2.0 Flow
    path('auth/google/', portal_views.google_oauth_redirect, name='google_login'),
    path('auth/google/callback/', portal_views.google_oauth_callback, name='google_callback'),

    # API endpoints for authentication & user status
    path('api/auth/login/', portal_views.api_login, name='api_login'),
    path('api/auth/logout/', portal_views.api_logout, name='api_logout'),
    path('api/auth/me/', portal_views.api_me, name='api_me'),
    path('api/auth/register/', portal_views.api_register, name='api_register'),
    path('api/auth/google/', portal_views.api_google_login, name='api_google_login'),
    path('api/auth/forgot-password/', portal_views.api_forgot_password, name='api_forgot_password'),
    path('api/auth/verify-otp/', portal_views.api_verify_otp, name='api_verify_otp'),
    path('api/auth/reset-password/', portal_views.api_reset_password, name='api_reset_password'),

    # Feedback & Wholesale Enquiry APIs
    path('api/feedback/', portal_views.api_submit_feedback, name='api_feedback'),
    path('api/wholesale-enquiry/', portal_views.api_submit_wholesale_enquiry, name='api_wholesale_enquiry'),
    
    # Health check for platform monitoring
    path('health', portal_views.health_check, name='health'),
    path('health/', portal_views.health_check, name='health_slash'),

    # Product and Static HTML pages (e.g. ragi.html, chilli.html, pepper.html, cardamom.html, balaji.html)
    path('<str:page_name>.html', portal_views.static_html_view, name='static_html'),

    # Public Core Website sections
    path('core/', include('core.urls')),

    # Public Product Catalog, Product Detail, Cart & Checkout (previously unmounted)
    path('products/', include('products.urls')),

    # B2B Client Portal (dashboard, orders, quotes, profile, support)
    path('portal/', include('portal.urls')),
]

# Serve media, images, and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(r'^images/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR.parent / 'images')}),
        re_path(r'^static/images/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR / 'static' / 'images')}),
        re_path(r'^static/css/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR / 'static' / 'css')}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR / 'static')}),
    ]
