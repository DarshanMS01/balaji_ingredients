from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from portal import views as portal_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Direct Login page route (using exact image)
    path('login/', portal_views.login_view, name='login'),
    path('signup/', portal_views.login_view, name='signup'),
    
    # Official Google OAuth 2.0 Flow
    path('auth/google/', portal_views.google_oauth_redirect, name='google_login'),
    path('auth/google/callback/', portal_views.google_oauth_callback, name='google_callback'),

    # API endpoints
    path('api/auth/login/', portal_views.api_login, name='api_login'),
    path('api/auth/register/', portal_views.api_register, name='api_register'),
    path('api/auth/google/', portal_views.api_google_login, name='api_google_login'),
    path('api/auth/forgot-password/', portal_views.api_forgot_password, name='api_forgot_password'),
    path('api/auth/verify-otp/', portal_views.api_verify_otp, name='api_verify_otp'),
    path('api/auth/reset-password/', portal_views.api_reset_password, name='api_reset_password'),
    
    # Public Core Website (Homepage with all 11 sections)
    path('', include('core.urls')),
]

# Serve media and images in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(r'^images/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR.parent / 'images')}),
        re_path(r'^static/images/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR / 'static' / 'images')}),
    ]
