from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Service category views
    path('', views.all_services_view, name='service_list'),
    path('category/<str:category>/', views.all_services_view, name='category'),
    
    # Individual service views
    path('detail/<int:service_id>/', views.all_services_view, name='service_detail'),
    path('request/<int:service_id>/', views.all_services_view, name='service_request'),
    
    # Service-specific views
    path('tourism/', views.tourism_services_view, name='tourism'),
    path('administrative/', views.administrative_services_view, name='administrative'),
    path('investment/', views.investment_services_view, name='investment'),
    path('real-estate/', views.real_estate_services_view, name='real_estate'),
    path('fiscal/', views.fiscal_services_view, name='fiscal'),
    
    # Contact
    path('contact/', views.contact_view, name='contact'),
]