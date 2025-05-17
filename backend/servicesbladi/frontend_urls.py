from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _

from services.views import (
    tourism_services_view, 
    administrative_services_view, 
    investment_services_view,
    real_estate_services_view, 
    fiscal_services_view,
    contact_view
)

from accounts.views import register_view, custom_login_view as login_view, profile_view, dashboard_redirect_view
from resources.views import resource_list_view as resources_view, resource_detail_view
from resources.client_views import client_resources_view

# Import views from the custom_requests app for frontend URLs
from custom_requests.dashboard_views import client_dashboard_view, expert_dashboard_view, admin_dashboard_view
from custom_requests.views import documents_view, client_requests_view, client_appointments_view, expert_requests_view, expert_appointments_view
from custom_requests.message_views import client_messages_view, expert_messages_view
from custom_requests.expert_views import expert_documents_view, expert_appointments_view as expert_appointments_view_new, expert_messages_view as expert_messages_view_new, expert_resources_view, expert_requests_view, expert_request_detail, expert_send_message, expert_upload_document, expert_update_request_status, expert_schedule_appointment, expert_update_appointment, expert_take_request

# Import admin views for frontend URLs
from custom_requests.admin_views import (
    admin_requests_view, admin_documents_view, admin_appointments_view,
    admin_resources_view, admin_users_view, admin_add_user,
    admin_toggle_user_status, admin_delete_user, admin_edit_user,
    admin_verify_document, admin_reject_document, admin_delete_document,
    admin_complete_appointment, admin_cancel_appointment, admin_reschedule_appointment,
    admin_add_resource, admin_edit_resource, admin_delete_resource,
    admin_toggle_resource_visibility, admin_messages_view, admin_mark_message_read,
    admin_profile_view, admin_edit_profile_view, admin_assign_expert, admin_update_request_status,
    admin_request_detail, admin_send_message, admin_user_detail
)

# Import admin bulk action views
from custom_requests.admin_bulk_actions import (
    admin_bulk_toggle_users_status, admin_bulk_delete_users,
    admin_bulk_verify_documents, admin_bulk_reject_documents
)

from custom_requests.models import ServiceRequest, Message, Notification
from accounts.models import Utilisateur

urlpatterns = [
    # Main pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('about/', TemplateView.as_view(template_name='about-us.html'), name='about'),
    path('contact/', contact_view, name='contact'),
    path('formulaire/', TemplateView.as_view(template_name='formulaire.html'), name='formulaire'),
    
    # Authentication related pages - these are handled by accounts.urls but redirected for template compatibility
    path('login/', TemplateView.as_view(template_name='login.html'), name='login_page'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register_page'),
    
    # Service pages linked to actual views in services app
    path('tourisme/', tourism_services_view, name='tourisme'),
    path('administrative/', administrative_services_view, name='administrative'),
    path('investissement/', investment_services_view, name='investment'),
    path('immobilier/', real_estate_services_view, name='immobilier'),
    path('fiscale/', fiscal_services_view, name='fiscale'),
    
    # Dashboard pages - these should be login protected
    # Client dashboard
    path('client/dashboard/', client_dashboard_view, name='client_dashboard'),
    path('client/demandes/', client_requests_view, name='client_demandes'),
    path('client/documents/', documents_view, name='client_documents'),
    path('client/messages/', client_messages_view, name='client_messages'),
    path('client/rendezvous/', client_appointments_view, name='client_rendezvous'),
    path('client/ressources/', client_resources_view, name='client_ressources'),
    
    # Expert dashboard
    path('expert/dashboard/', expert_dashboard_view, name='expert_dashboard'),
    path('expert/demandes/', expert_requests_view, name='expert_demandes'),
    path('expert/demandes/<int:request_id>/', expert_request_detail, name='expert_request_detail'),
    path('expert/demandes/take/<int:request_id>/', expert_take_request, name='expert_take_request'),
    path('expert/documents/', documents_view, name='expert_documents'),
    path('expert/messages/', expert_messages_view, name='expert_messages'),
    path('expert/rendezvous/', expert_appointments_view, name='expert_rendezvous'),
    path('expert/ressources/', expert_resources_view, name='expert_ressources'),
    path('expert/send-message/<int:client_id>/', expert_send_message, name='expert_send_message'),
    path('expert/upload-document/', expert_upload_document, name='expert_upload_document'),
    path('expert/update-request-status/<int:request_id>/', expert_update_request_status, name='expert_update_request_status'),
    path('expert/schedule-appointment/', expert_schedule_appointment, name='expert_schedule_appointment'),
    path('expert/update-appointment/', expert_update_appointment, name='expert_update_appointment'),
    
    # Admin dashboard - all using dynamic views
    path('admin/dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin/demandes/', admin_requests_view, name='admin_demandes'),
    path('admin/demandes/<int:request_id>/', admin_request_detail, name='admin_request_detail'),
    path('admin/documents/', admin_documents_view, name='admin_documents'),
    path('admin/rendezvous/', admin_appointments_view, name='admin_rendezvous'),
    path('admin/ressources/', admin_resources_view, name='admin_ressources'),
    path('admin/users/', admin_users_view, name='admin_users'),
    path('admin/users/<int:user_id>/', admin_user_detail, name='admin_user_detail'),
    path('admin/users/add/', admin_add_user, name='admin_add_user'),
    path('admin/users/bulk-toggle-status/', admin_bulk_toggle_users_status, name='admin_bulk_toggle_users_status'),
    path('admin/users/bulk-delete/', admin_bulk_delete_users, name='admin_bulk_delete_users'),
    path('admin/users/<int:user_id>/toggle-status/', admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin/users/<int:user_id>/delete/', admin_delete_user, name='admin_delete_user'),
    path('admin/users/<int:user_id>/edit/', admin_edit_user, name='admin_edit_user'),
    path('admin/documents/bulk-verify/', admin_bulk_verify_documents, name='admin_bulk_verify_documents'),
    path('admin/documents/bulk-reject/', admin_bulk_reject_documents, name='admin_bulk_reject_documents'),
    path('admin/documents/<int:document_id>/verify/', admin_verify_document, name='admin_verify_document'),
    path('admin/documents/<int:document_id>/reject/', admin_reject_document, name='admin_reject_document'),
    path('admin/documents/<int:document_id>/delete/', admin_delete_document, name='admin_delete_document'),
    path('admin/rendezvous/<int:appointment_id>/complete/', admin_complete_appointment, name='admin_complete_appointment'),
    path('admin/rendezvous/<int:appointment_id>/cancel/', admin_cancel_appointment, name='admin_cancel_appointment'),
    path('admin/rendezvous/<int:appointment_id>/reschedule/', admin_reschedule_appointment, name='admin_reschedule_appointment'),
    path('admin/ressources/add/', admin_add_resource, name='admin_add_resource'),
    path('admin/ressources/<int:resource_id>/edit/', admin_edit_resource, name='admin_edit_resource'),
    path('admin/ressources/<int:resource_id>/delete/', admin_delete_resource, name='admin_delete_resource'),
    path('admin/ressources/<int:resource_id>/toggle-visibility/', admin_toggle_resource_visibility, name='admin_toggle_resource_visibility'),
    path('admin/messages/', admin_messages_view, name='admin_messages'),
    path('admin/messages/<int:message_id>/mark-read/', admin_mark_message_read, name='admin_mark_message_read'),
    path('admin/profile/', admin_profile_view, name='admin_profile'),
    path('admin/profile/edit/', admin_edit_profile_view, name='admin_edit_profile'),
    path('admin/demandes/<int:request_id>/assign-expert/', admin_assign_expert, name='admin_assign_expert'),
    path('admin/demandes/<int:request_id>/update-status/', admin_update_request_status, name='admin_update_request_status'),
    path('admin/send-message/', admin_send_message, name='admin_send_message'),
]