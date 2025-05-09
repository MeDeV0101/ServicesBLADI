from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from services.views import (
    tourism_services_view, 
    administrative_services_view, 
    investment_services_view,
    real_estate_services_view, 
    fiscal_services_view,
    contact_view
)

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
    path('client/dashboard/', login_required(TemplateView.as_view(template_name='client/dashboard.html')), name='client_dashboard'),
    path('client/demandes/', login_required(TemplateView.as_view(template_name='client/demandes.html')), name='client_demandes'),
    path('client/documents/', login_required(TemplateView.as_view(template_name='client/documents.html')), name='client_documents'),
    path('client/messages/', login_required(TemplateView.as_view(template_name='client/messages.html')), name='client_messages'),
    path('client/rendezvous/', login_required(TemplateView.as_view(template_name='client/rendezvous.html')), name='client_rendezvous'),
    path('client/ressources/', login_required(TemplateView.as_view(template_name='client/ressources.html')), name='client_ressources'),
    
    # Expert dashboard
    path('expert/dashboard/', login_required(TemplateView.as_view(template_name='expert/dashboard.html')), name='expert_dashboard'),
    path('expert/demandes/', login_required(TemplateView.as_view(template_name='expert/demandes.html')), name='expert_demandes'),
    path('expert/documents/', login_required(TemplateView.as_view(template_name='expert/documents.html')), name='expert_documents'),
    path('expert/rendezvous/', login_required(TemplateView.as_view(template_name='expert/rendezvous.html')), name='expert_rendezvous'),
    path('expert/ressources/', login_required(TemplateView.as_view(template_name='expert/ressources.html')), name='expert_ressources'),
    
    # Admin dashboard
    path('admin/dashboard/', login_required(TemplateView.as_view(template_name='admin/dashboard.html')), name='admin_dashboard'),
    path('admin/demandes/', login_required(TemplateView.as_view(template_name='admin/demandes.html')), name='admin_demandes'),
    path('admin/documents/', login_required(TemplateView.as_view(template_name='admin/documents.html')), name='admin_documents'),
    path('admin/rendezvous/', login_required(TemplateView.as_view(template_name='admin/rendezvous.html')), name='admin_rendezvous'),
    path('admin/ressources/', login_required(TemplateView.as_view(template_name='admin/ressources.html')), name='admin_ressources'),
    path('admin/users/', login_required(TemplateView.as_view(template_name='admin/users.html')), name='admin_users'),
    path('admin/messages/', login_required(TemplateView.as_view(template_name='admin/messages.html')), name='admin_messages'),
]