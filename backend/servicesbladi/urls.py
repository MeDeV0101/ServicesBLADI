"""
URL configuration for servicesbladi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect

# Import message_views from custom_requests app for direct URL mapping
from custom_requests.message_views import expert_check_messages

# Add a redirect for the secure admin login
def admin_login_redirect(request):
    return redirect('accounts:admin_login_view')

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Renamed Django admin URL to avoid conflicts
    
    # Admin URL explicit redirect
    path('management/secure8765/login/', admin_login_redirect),
    
    # Include URLs from each app
    path('accounts/', include('accounts.urls')),
    path('services/', include('services.urls')),
    path('requests/', include('custom_requests.urls')),
    path('resources/', include('resources.urls')),
    path('messaging/', include('messaging.urls')),
    
    # Frontend URLs (existing HTML templates integration)
    path('', include('servicesbladi.frontend_urls')),
    
    # Authentication views
    path('accounts/password_reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
        ), 
        name='password_reset'),
    path('accounts/password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ), 
        name='password_reset_confirm'),
    path('accounts/reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
    
    # Language change
    path('i18n/', include('django.conf.urls.i18n')),

    # Add direct URL mapping for expert_check_messages
    path('expert/messages/check/', expert_check_messages, name='expert_messages_check'),
]

# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site titles
admin.site.site_header = _('ServicesBLADI Administration')
admin.site.site_title = _('ServicesBLADI Admin Portal')
admin.site.index_title = _('Welcome to ServicesBLADI Admin Portal')
