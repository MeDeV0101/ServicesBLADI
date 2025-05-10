from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import Client, Utilisateur
from services.models import Service, ServiceCategory
from .models import ServiceRequest, Document, RendezVous, Notification, Message

def get_service_icon(service):
    """Helper function to get appropriate icon for a service"""
    if service.service_type and service.service_type.category and service.service_type.category.icon:
        return service.service_type.category.icon
    
    # Default icons based on service type if available
    service_type_name = ''
    if service.service_type:
        service_type_name = service.service_type.name.lower()
    
    if 'tourisme' in service_type_name or 'tourism' in service_type_name:
        return 'airplane'
    elif 'administrative' in service_type_name or 'admin' in service_type_name:
        return 'file-earmark-text'
    elif 'immobilier' in service_type_name or 'real estate' in service_type_name:
        return 'house-door'
    elif 'fiscal' in service_type_name or 'tax' in service_type_name:
        return 'calculator'
    elif 'investissement' in service_type_name or 'investment' in service_type_name:
        return 'graph-up'
    
    return 'file-earmark-text'  # Default icon

@login_required
def client_dashboard_view(request):
    """
    View function for the client dashboard.
    
    This view acts as the central hub for clients to view their service requests,
    documents, upcoming appointments, and notifications. It provides:
    - Counts of active and completed service requests
    - Count of available documents
    - Recent notifications with unread notification count
    - List of upcoming appointments
    - Available services that can be requested
    - Recent documents uploaded by or for the client
    - Recent service requests submitted by the client
    
    Args:
        request: The HTTP request object
        
    Returns:
        Rendered dashboard template with context data or redirects to home if client profile not found
    """
    print(f"Starting client_dashboard_view for user {request.user.email}")
    
    try:
        # Get client profile
        client_profile = Client.objects.get(user=request.user)
        print(f"Found client profile for {client_profile}")
        
        # Count of active service requests
        active_requests = ServiceRequest.objects.filter(
            client=request.user,
            status__in=['new', 'in_progress', 'pending_info']
        ).count()
        print(f"Active requests count: {active_requests}")
        
        # Count of completed service requests
        completed_requests = ServiceRequest.objects.filter(
            client=request.user,
            status='completed'
        ).count()
        print(f"Completed requests count: {completed_requests}")
        
        # Count of documents
        documents_count = Document.objects.filter(
            Q(service_request__client=request.user) |
            Q(rendez_vous__client=request.user) |
            Q(uploaded_by=request.user)
        ).distinct().count()
        print(f"Documents count: {documents_count}")
        
        # Get recent notifications
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        print(f"Retrieved {len(notifications)} notifications")
        
        # Count unread notifications
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        print(f"Unread notifications count: {unread_notifications_count}")
        
        # Get upcoming appointments
        upcoming_appointments = RendezVous.objects.filter(
            client=request.user,
            date_time__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).order_by('date_time')[:3]
        print(f"Retrieved {len(upcoming_appointments)} upcoming appointments")
        
        # Get available services
        available_services = Service.objects.filter(is_active=True).select_related('service_type__category')
        print(f"Retrieved {len(available_services)} available services")
        
        # Enrich services with icons
        services_with_icons = []
        for service in available_services:
            service.icon = get_service_icon(service)
            services_with_icons.append(service)
        
        # Get recent documents
        recent_documents = Document.objects.filter(
            Q(service_request__client=request.user) |
            Q(rendez_vous__client=request.user) |
            Q(uploaded_by=request.user)
        ).distinct().order_by('-upload_date')[:3]
        print(f"Retrieved {len(recent_documents)} recent documents")
        
        # Get recent service requests
        recent_requests = ServiceRequest.objects.filter(
            client=request.user
        ).order_by('-created_at')[:3]
        print(f"Retrieved {len(recent_requests)} recent requests")
        
        # Prepare context for template
        context = {
            'active_requests': active_requests,
            'completed_requests': completed_requests,
            'documents_count': documents_count,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'upcoming_appointments': upcoming_appointments,
            'available_services': services_with_icons,
            'recent_documents': recent_documents,
            'recent_requests': recent_requests,
            'resources_count': 8,  # Placeholder value - replace with actual count when Resource model is available
            'client': client_profile,
            'user': request.user
        }
        
        print("Rendering dashboard with context")
        return render(request, 'client/dashboard.html', context)
        
    except Client.DoesNotExist:
        # If client profile doesn't exist, redirect to home
        print(f"Client profile not found for user {request.user.email}, redirecting to home")
        return redirect('home')
    except Exception as e:
        # Log any other exceptions
        print(f"Error in client_dashboard_view: {str(e)}")
        return render(request, 'client/dashboard.html', {'error': str(e)})
