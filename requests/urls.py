from django.urls import path
from . import views
from . import message_views

app_name = 'requests'

urlpatterns = [
    # Client request views
    path('client/', views.client_requests_view, name='client_requests'),
    path('client/create/<int:service_id>/', views.create_request_view, name='create_request'),
    path('client/create/<str:service_type>/', views.create_request_by_type_view, name='create_request_by_type'),
    path('client/detail/<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('client/edit/<int:request_id>/', views.edit_request_view, name='edit_request'),
    path('client/cancel/<int:request_id>/', views.cancel_request_view, name='cancel_request'),
    
    # Appointment views
    path('appointments/', views.client_appointments_view, name='client_appointments'),
    path('appointments/create/', views.create_appointment_view, name='create_appointment'),
    path('appointments/detail/<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment_view, name='cancel_appointment'),
    
    # Expert views
    path('expert/', views.expert_requests_view, name='expert_requests'),
    path('expert/appointments/', views.expert_appointments_view, name='expert_appointments'),
    
    # Document views
    path('documents/', views.documents_view, name='documents'),
    path('documents/upload/', views.upload_document_view, name='upload_document'),
    path('documents/delete/<int:document_id>/', views.delete_document_view, name='delete_document'),
    
    # Messaging views
    path('messages/', views.messages_view, name='messages'),
    path('client/send_message/<int:recipient_id>/', message_views.client_send_message, name='client_send_message'),
    path('client/check_messages/', message_views.client_check_messages, name='client_check_messages'),
    path('expert/send_message/<int:client_id>/', message_views.expert_send_message, name='expert_send_message'),
    path('expert/check_messages/', message_views.expert_check_messages, name='expert_check_messages'),
    path('messages/send/', views.send_message_view, name='send_message'),
    
    # Notification views
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read_view, name='mark_notification_read'),
    
    # API endpoints
    path('api/client/requests/', views.api_client_requests, name='api_client_requests'),
    path('api/request/<int:request_id>/', views.api_request_detail, name='api_request_detail'),
    path('api/appointments/', views.api_client_appointments, name='api_appointments'),
    path('api/expert/requests/', views.api_expert_requests, name='api_expert_requests'),
    path('api/documents/upload/', views.api_upload_document, name='api_upload_document'),
    path('api/messages/', views.api_messages, name='api_messages'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),
]