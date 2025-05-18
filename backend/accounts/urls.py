from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/expert/', views.register_expert_view, name='register_expert'),
    
    # Password management
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Dashboards
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    
    # Profile views
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    
    # Client specific views
    path('client/profile/', views.client_profile_view, name='client_profile'),
    path('client/documents/', views.client_documents_view, name='client_documents'),
    
    # Expert specific views
    path('expert/profile/', views.expert_profile_view, name='expert_profile'),
    
    # Admin specific views - with secure URL pattern
    path('management/secure8765/login/', views.admin_login_view, name='admin_login_view'),
    path('management/secure8765/create/', views.create_admin_user, name='create_admin_view'),
    path('expert/availability/', views.expert_availability_view, name='expert_availability'),
    path('expert/services/', views.expert_services_view, name='expert_services'),
    
    # Admin specific views
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/user/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('admin/create_user/', views.admin_create_user_view, name='admin_create_user'),
    
    # API endpoints
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/update_profile/', views.api_update_profile, name='api_update_profile'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate'),
]