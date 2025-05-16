from django.urls import path
from . import views
from . import client_views
from . import expert_views

app_name = 'resources'

urlpatterns = [
    # Resource views
    path('', views.resource_list_view, name='resource_list'),
    path('detail/<int:resource_id>/', views.resource_detail_view, name='resource_detail'),
    path('category/<str:category>/', views.resource_category_view, name='resource_category'),
    path('download/<int:resource_file_id>/', views.download_resource_view, name='download_resource'),
    
    # Client resource views
    path('client/', client_views.client_resources_view, name='client_resources'),
    path('client/download/<int:resource_file_id>/', client_views.client_download_resource_view, name='client_download_resource'),
    
    # Embassy and consulate views
    path('embassy/', views.embassy_list_view, name='embassy_list'),
    path('embassy/<str:country>/', views.embassy_country_view, name='embassy_country'),
    path('embassy/<str:country>/<str:city>/', views.embassy_detail_view, name='embassy_detail'),
    
    # FAQ views
    path('faq/', views.faq_view, name='faq'),
    path('faq/<str:category>/', views.faq_category_view, name='faq_category'),
    
    # API endpoints
    path('api/resources/', views.api_resource_list, name='api_resource_list'),
    path('api/resources/<int:resource_id>/', views.api_resource_detail, name='api_resource_detail'),
    path('api/embassy/', views.api_embassy_list, name='api_embassy_list'),
    path('api/embassy/<str:country>/', views.api_embassy_country, name='api_embassy_country'),
    path('api/faq/', views.api_faq_list, name='api_faq_list'),
    
    # Expert resource views
    path('expert/add/', expert_views.add_resource, name='expert_add_resource'),
    path('expert/edit/<int:resource_id>/', expert_views.edit_resource, name='edit_resource'),
    path('expert/delete/<int:resource_id>/', expert_views.delete_resource, name='delete_resource'),
]