from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
import mimetypes

from accounts.models import Utilisateur, Client, Expert
from services.models import Service
from .models import ServiceRequest, RendezVous, Document, Message, Notification

# Client request management views
@login_required
def client_requests_view(request):
    """Display client's service requests"""
    try:
        client = Client.objects.get(user=request.user)
        requests = ServiceRequest.objects.filter(client=client).order_by('-created_at')
        
        context = {
            'requests': requests,
        }
        
        return render(request, 'client/demandes.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def create_request_view(request, service_id):
    """Create a new service request"""
    try:
        client = Client.objects.get(user=request.user)
        service = get_object_or_404(Service, id=service_id, is_active=True)
        
        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            priority = request.POST.get('priority', 'medium')
            
            # Create the request
            demande = ServiceRequest.objects.create(
                client=client,
                service=service,
                title=title,
                description=description,
                priority=priority,
                status='new'
            )
            
            # Upload documents if provided
            for file_key in request.FILES:
                file = request.FILES[file_key]
                document = Document.objects.create(
                    demande=demande,
                    uploaded_by=request.user,
                    type='other',
                    name=file.name,
                    file=file,
                    mime_type=file.content_type,
                    file_size=file.size // 1024  # Convert to KB
                )
            
            # Create a notification for admins
            for admin_user in Utilisateur.objects.filter(account_type='admin', is_active=True):
                Notification.objects.create(
                    user=admin_user,
                    type='request_update',
                    title=_('New Service Request'),
                    content=_(f'A new service request "{title}" has been created by {client.user.name} {client.user.first_name}.'),
                    related_demande=demande
                )
            
            return redirect('requests:client_requests')
            
        context = {
            'service': service,
        }
        
        return render(request, 'client/create_request.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def request_detail_view(request, request_id):
    """Display details of a specific request"""
    demande = get_object_or_404(ServiceRequest, id=request_id)
    
    # Check if user has permission to view this request
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            if demande.client != client:
                return redirect('home')
        except Client.DoesNotExist:
            return redirect('home')
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            if demande.assigned_expert != expert:
                return redirect('home')
        except Expert.DoesNotExist:
            return redirect('home')
    elif request.user.account_type != 'admin':
        return redirect('home')
    
    # Get documents and messages related to this request
    documents = Document.objects.filter(demande=demande).order_by('-upload_date')
    messages = Message.objects.filter(demande=demande).order_by('sent_at')
    appointments = RendezVous.objects.filter(demande=demande).order_by('date_time')
    
    # Handle new message submission
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            # Create a new message
            if request.user.account_type == 'client':
                # From client to expert or admin
                recipient = demande.assigned_expert.user if demande.assigned_expert else Utilisateur.objects.filter(account_type='admin').first()
            else:
                # From expert/admin to client
                recipient = demande.client.user
                
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                demande=demande
            )
            
            # Create notification for recipient
            Notification.objects.create(
                user=recipient,
                type='message',
                title=_('New Message'),
                content=_(f'You have a new message from {request.user.name} {request.user.first_name} regarding request "{demande.title}".'),
                related_demande=demande,
                related_message=message
            )
    
    context = {
        'demande': demande,
        'documents': documents,
        'messages': messages,
        'appointments': appointments,
    }
    
    return render(request, 'client/request_detail.html', context)

@login_required
def edit_request_view(request, request_id):
    """Edit an existing request"""
    try:
        client = Client.objects.get(user=request.user)
        demande = get_object_or_404(ServiceRequest, id=request_id, client=client)
        
        # Only allow editing if request is new or pending information
        if demande.status not in ['new', 'pending_info']:
            messages.error(request, _('This request cannot be edited in its current status.'))
            return redirect('requests:request_detail', request_id=request_id)
        
        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            
            # Update the request
            demande.title = title
            demande.description = description
            demande.save()
            
            # Notify assigned expert if any
            if demande.assigned_expert:
                Notification.objects.create(
                    user=demande.assigned_expert.user,
                    type='request_update',
                    title=_('Request Updated'),
                    content=_(f'Request "{demande.title}" has been updated by {client.user.name} {client.user.first_name}.'),
                    related_demande=demande
                )
            
            return redirect('requests:request_detail', request_id=request_id)
            
        context = {
            'demande': demande,
        }
        
        return render(request, 'client/edit_request.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def cancel_request_view(request, request_id):
    """Cancel a request"""
    try:
        client = Client.objects.get(user=request.user)
        demande = get_object_or_404(ServiceRequest, id=request_id, client=client)
        
        # Only allow cancellation if request is not already completed or cancelled
        if demande.status in ['completed', 'cancelled']:
            messages.error(request, _('This request cannot be cancelled in its current status.'))
            return redirect('requests:request_detail', request_id=request_id)
        
        if request.method == 'POST':
            reason = request.POST.get('reason', '')
            
            # Update the request
            demande.status = 'cancelled'
            demande.save()
            
            # Notify assigned expert if any
            if demande.assigned_expert:
                Notification.objects.create(
                    user=demande.assigned_expert.user,
                    type='request_update',
                    title=_('Request Cancelled'),
                    content=_(f'Request "{demande.title}" has been cancelled by {client.user.name} {client.user.first_name}. Reason: {reason}'),
                    related_demande=demande
                )
            
            return redirect('requests:client_requests')
            
        context = {
            'demande': demande,
        }
        
        return render(request, 'client/cancel_request.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

# Appointment views
@login_required
def client_appointments_view(request):
    """Display client's appointments"""
    try:
        client = Client.objects.get(user=request.user)
        appointments = RendezVous.objects.filter(client=client).order_by('date_time')
        
        context = {
            'appointments': appointments,
        }
        
        return render(request, 'client/rendezvous.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def create_appointment_view(request, expert_id):
    """Create a new appointment with an expert"""
    try:
        client = Client.objects.get(user=request.user)
        expert = get_object_or_404(Expert, id=expert_id)
        
        if request.method == 'POST':
            date_time_str = request.POST.get('date_time')
            service_id = request.POST.get('service_id')
            consultation_type = request.POST.get('consultation_type')
            notes = request.POST.get('notes', '')
            demande_id = request.POST.get('demande_id')
            
            try:
                # Parse date and time
                date_time = timezone.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
                date_time = timezone.make_aware(date_time)
                
                # Get service if provided
                service = None
                if service_id:
                    service = get_object_or_404(Service, id=service_id, is_active=True)
                
                # Get associated request if provided
                demande = None
                if demande_id:
                    demande = get_object_or_404(ServiceRequest, id=demande_id, client=client)
                
                # Create the appointment
                appointment = RendezVous.objects.create(
                    client=client,
                    expert=expert,
                    service=service,
                    date_time=date_time,
                    consultation_type=consultation_type,
                    notes=notes,
                    demande=demande,
                    status='scheduled'
                )
                
                # Notify the expert
                Notification.objects.create(
                    user=expert.user,
                    type='appointment',
                    title=_('New Appointment Request'),
                    content=_(f'A new appointment has been scheduled by {client.user.name} {client.user.first_name} for {date_time_str}.'),
                    related_rendez_vous=appointment
                )
                
                return redirect('requests:client_appointments')
                
            except ValueError:
                messages.error(request, _('Invalid date or time format.'))
        
        # Get available services
        services = Service.objects.filter(is_active=True)
        
        # Get client's requests that can be associated with this appointment
        demandes = ServiceRequest.objects.filter(client=client).exclude(status__in=['completed', 'cancelled'])
        
        context = {
            'expert': expert,
            'services': services,
            'demandes': demandes,
        }
        
        return render(request, 'client/create_appointment.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def appointment_detail_view(request, appointment_id):
    """Display details of a specific appointment"""
    appointment = get_object_or_404(RendezVous, id=appointment_id)
    
    # Check if user has permission to view this appointment
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            if appointment.client != client:
                return redirect('home')
        except Client.DoesNotExist:
            return redirect('home')
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            if appointment.expert != expert:
                return redirect('home')
        except Expert.DoesNotExist:
            return redirect('home')
    elif request.user.account_type != 'admin':
        return redirect('home')
    
    # Get documents related to this appointment
    documents = Document.objects.filter(rendez_vous=appointment).order_by('-upload_date')
    
    context = {
        'appointment': appointment,
        'documents': documents,
    }
    
    return render(request, 'client/appointment_detail.html', context)

@login_required
def cancel_appointment_view(request, appointment_id):
    """Cancel an appointment"""
    try:
        if request.user.account_type == 'client':
            client = Client.objects.get(user=request.user)
            appointment = get_object_or_404(RendezVous, id=appointment_id, client=client)
        elif request.user.account_type == 'expert':
            expert = Expert.objects.get(user=request.user)
            appointment = get_object_or_404(RendezVous, id=appointment_id, expert=expert)
        else:
            return redirect('home')
        
        # Only allow cancellation if appointment is not already completed or cancelled
        if appointment.status in ['completed', 'cancelled']:
            messages.error(request, _('This appointment cannot be cancelled in its current status.'))
            return redirect('requests:appointment_detail', appointment_id=appointment_id)
        
        if request.method == 'POST':
            reason = request.POST.get('reason', '')
            
            # Update the appointment
            appointment.status = 'cancelled'
            appointment.save()
            
            # Determine who cancelled and who needs to be notified
            if request.user.account_type == 'client':
                # Client cancelled, notify expert
                notification_recipient = appointment.expert.user
                canceller_name = f"{client.user.name} {client.user.first_name}"
            else:
                # Expert cancelled, notify client
                notification_recipient = appointment.client.user
                canceller_name = f"{expert.user.name} {expert.user.first_name}"
            
            # Create notification
            Notification.objects.create(
                user=notification_recipient,
                type='appointment',
                title=_('Appointment Cancelled'),
                content=_(f'Appointment on {appointment.date_time.strftime("%Y-%m-%d %H:%M")} has been cancelled by {canceller_name}. Reason: {reason}'),
                related_rendez_vous=appointment
            )
            
            return redirect('requests:client_appointments' if request.user.account_type == 'client' else 'requests:expert_appointments')
            
        context = {
            'appointment': appointment,
        }
        
        return render(request, 'client/cancel_appointment.html' if request.user.account_type == 'client' else 'expert/cancel_appointment.html', context)
    
    except (Client.DoesNotExist, Expert.DoesNotExist):
        return redirect('home')

# Expert views
@login_required
def expert_requests_view(request):
    """Display requests assigned to expert"""
    try:
        expert = Expert.objects.get(user=request.user)
        requests = ServiceRequest.objects.filter(assigned_expert=expert).order_by('-created_at')
        
        context = {
            'requests': requests,
        }
        
        return render(request, 'expert/demandes.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointments_view(request):
    """Display expert's appointments"""
    try:
        expert = Expert.objects.get(user=request.user)
        appointments = RendezVous.objects.filter(expert=expert).order_by('date_time')
        
        context = {
            'appointments': appointments,
        }
        
        return render(request, 'expert/rendezvous.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

# Document views
@login_required
def documents_view(request):
    """Display user's documents"""
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            # Get documents from client's requests
            documents = Document.objects.filter(
                Q(demande__client=client) |
                Q(rendez_vous__client=client) |
                Q(uploaded_by=request.user)
            ).distinct().order_by('-upload_date')
        except Client.DoesNotExist:
            documents = Document.objects.filter(uploaded_by=request.user).order_by('-upload_date')
    
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            # Get documents from expert's assigned requests
            documents = Document.objects.filter(
                Q(demande__assigned_expert=expert) |
                Q(rendez_vous__expert=expert) |
                Q(uploaded_by=request.user)
            ).distinct().order_by('-upload_date')
        except Expert.DoesNotExist:
            documents = Document.objects.filter(uploaded_by=request.user).order_by('-upload_date')
    
    elif request.user.account_type == 'admin':
        # Admins can see all documents
        documents = Document.objects.all().order_by('-upload_date')
    
    else:
        documents = []
    
    context = {
        'documents': documents,
    }
    
    if request.user.account_type == 'client':
        return render(request, 'client/documents.html', context)
    elif request.user.account_type == 'expert':
        return render(request, 'expert/documents.html', context)
    elif request.user.account_type == 'admin':
        return render(request, 'admin/documents.html', context)
    else:
        return redirect('home')

@login_required
def upload_document_view(request):
    """Upload a document"""
    if request.method == 'POST':
        name = request.POST.get('name')
        document_type = request.POST.get('type', 'other')
        demande_id = request.POST.get('demande_id')
        rendez_vous_id = request.POST.get('rendez_vous_id')
        is_official = request.POST.get('is_official') == 'on'
        reference_number = request.POST.get('reference_number', '')
        
        if 'file' in request.FILES:
            file = request.FILES['file']
            
            # Get related demande and rendez_vous if provided
            demande = None
            rendez_vous = None
            
            if demande_id:
                demande = get_object_or_404(ServiceRequest, id=demande_id)
            
            if rendez_vous_id:
                rendez_vous = get_object_or_404(RendezVous, id=rendez_vous_id)
            
            # Create document
            document = Document.objects.create(
                demande=demande,
                rendez_vous=rendez_vous,
                uploaded_by=request.user,
                type=document_type,
                name=name or file.name,
                file=file,
                mime_type=file.content_type,
                file_size=file.size // 1024,  # Convert to KB
                is_official=is_official,
                reference_number=reference_number
            )
            
            # Create notifications
            if demande:
                if request.user.account_type == 'client':
                    # Notify assigned expert if any
                    if demande.assigned_expert:
                        Notification.objects.create(
                            user=demande.assigned_expert.user,
                            type='document',
                            title=_('New Document Uploaded'),
                            content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for request "{demande.title}".'),
                            related_demande=demande
                        )
                else:
                    # Notify client
                    Notification.objects.create(
                        user=demande.client.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your request "{demande.title}".'),
                        related_demande=demande
                    )
            
            if rendez_vous:
                if request.user.account_type == 'client':
                    # Notify expert
                    Notification.objects.create(
                        user=rendez_vous.expert.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                        related_rendez_vous=rendez_vous
                    )
                else:
                    # Notify client
                    Notification.objects.create(
                        user=rendez_vous.client.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                        related_rendez_vous=rendez_vous
                    )
            
            return redirect('requests:documents')
    
    # Get requests and appointments for association
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(client=client)
            appointments = RendezVous.objects.filter(client=client)
        except Client.DoesNotExist:
            demandes = []
            appointments = []
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(assigned_expert=expert)
            appointments = RendezVous.objects.filter(expert=expert)
        except Expert.DoesNotExist:
            demandes = []
            appointments = []
    elif request.user.account_type == 'admin':
        demandes = ServiceRequest.objects.all()
        appointments = RendezVous.objects.all()
    else:
        demandes = []
        appointments = []
    
    context = {
        'demandes': demandes,
        'appointments': appointments,
    }
    
    return render(request, 'upload_document.html', context)

# Messaging views
@login_required
def messages_view(request):
    """Display user's messages"""
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # Group messages by conversation
    conversations = {}
    for message in messages:
        # Determine the other party in the conversation
        other_party = message.recipient if message.sender == request.user else message.sender
        
        # Create a unique key for this conversation
        conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
        
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'other_party': other_party,
                'latest_message': message,
                'unread_count': 1 if message.recipient == request.user and not message.is_read else 0
            }
        else:
            # Update latest message if this one is newer
            if message.sent_at > conversations[conversation_key]['latest_message'].sent_at:
                conversations[conversation_key]['latest_message'] = message
            
            # Update unread count
            if message.recipient == request.user and not message.is_read:
                conversations[conversation_key]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message date
    conversations_list = sorted(
        conversations.values(),
        key=lambda x: x['latest_message'].sent_at,
        reverse=True
    )
    
    context = {
        'conversations': conversations_list,
    }
    
    if request.user.account_type == 'client':
        return render(request, 'client/messages.html', context)
    elif request.user.account_type == 'expert':
        return render(request, 'expert/messages.html', context)
    elif request.user.account_type == 'admin':
        return render(request, 'admin/messages.html', context)
    else:
        return redirect('home')

@login_required
def send_message_view(request):
    """Send a new message"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        demande_id = request.POST.get('demande_id')
        
        recipient = get_object_or_404(Utilisateur, id=recipient_id)
        
        # Get related request if provided
        demande = None
        if demande_id:
            demande = get_object_or_404(ServiceRequest, id=demande_id)
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content,
            demande=demande
        )
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('New Message'),
            content=_(f'You have a new message from {request.user.name} {request.user.first_name}.'),
            related_message=message,
            related_demande=demande
        )
        
        return redirect('requests:messages')
    
    # Get potential recipients based on user type
    recipients = []
    
    if request.user.account_type == 'client':
        # Clients can message experts they have appointments with and admins
        try:
            client = Client.objects.get(user=request.user)
            expert_users = Utilisateur.objects.filter(
                expert_profile__appointments__client=client
            ).distinct()
            admin_users = Utilisateur.objects.filter(account_type='admin', is_active=True)
            recipients = list(expert_users) + list(admin_users)
        except Client.DoesNotExist:
            pass
    
    elif request.user.account_type == 'expert':
        # Experts can message clients they have appointments with and admins
        try:
            expert = Expert.objects.get(user=request.user)
            client_users = Utilisateur.objects.filter(
                client_profile__appointments__expert=expert
            ).distinct()
            admin_users = Utilisateur.objects.filter(account_type='admin', is_active=True)
            recipients = list(client_users) + list(admin_users)
        except Expert.DoesNotExist:
            pass
    
    elif request.user.account_type == 'admin':
        # Admins can message all clients and experts
        client_users = Utilisateur.objects.filter(account_type='client', is_active=True)
        expert_users = Utilisateur.objects.filter(account_type='expert', is_active=True)
        recipients = list(client_users) + list(expert_users)
    
    # Get requests the user is involved in
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(client=client)
        except Client.DoesNotExist:
            demandes = []
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(assigned_expert=expert)
        except Expert.DoesNotExist:
            demandes = []
    elif request.user.account_type == 'admin':
        demandes = ServiceRequest.objects.all()
    else:
        demandes = []
    
    context = {
        'recipients': recipients,
        'demandes': demandes,
    }
    
    return render(request, 'send_message.html', context)

# Notification views
@login_required
def notifications_view(request):
    """Display user's notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    if request.user.account_type == 'client':
        return render(request, 'client/notifications.html', context)
    elif request.user.account_type == 'expert':
        return render(request, 'expert/notifications.html', context)
    elif request.user.account_type == 'admin':
        return render(request, 'admin/notifications.html', context)
    else:
        return redirect('home')

@login_required
def mark_notification_read_view(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect to related content if available
    if notification.related_demande:
        return redirect('requests:request_detail', request_id=notification.related_demande.id)
    elif notification.related_rendez_vous:
        return redirect('requests:appointment_detail', appointment_id=notification.related_rendez_vous.id)
    elif notification.related_message:
        return redirect('requests:messages')
    else:
        return redirect('requests:notifications')

# API endpoints
@login_required
@csrf_exempt
def api_client_requests(request):
    """API endpoint for client requests"""
    try:
        client = Client.objects.get(user=request.user)
        requests_query = ServiceRequest.objects.filter(client=client).order_by('-created_at')
        
        # Apply status filter if provided
        status = request.GET.get('status')
        if status:
            requests_query = requests_query.filter(status=status)
        
        # Prepare response data
        requests_data = []
        for demande in requests_query:
            requests_data.append({
                'id': demande.id,
                'title': demande.title,
                'service': {
                    'id': demande.service.id,
                    'title': demande.service.title,
                    'category': demande.service.category
                },
                'status': demande.status,
                'priority': demande.priority,
                'created_at': demande.created_at.isoformat(),
                'expert': {
                    'id': demande.assigned_expert.id,
                    'name': f"{demande.assigned_expert.user.name} {demande.assigned_expert.user.first_name}",
                } if demande.assigned_expert else None
            })
        
        return JsonResponse({
            'success': True,
            'requests': requests_data
        })
    
    except Client.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Client profile not found.')
        }, status=404)

@login_required
@csrf_exempt
def api_request_detail(request, request_id):
    """API endpoint for request details"""
    try:
        demande = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check permission
        if request.user.account_type == 'client':
            client = Client.objects.get(user=request.user)
            if demande.client != client:
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to view this request.')
                }, status=403)
        elif request.user.account_type == 'expert':
            expert = Expert.objects.get(user=request.user)
            if demande.assigned_expert != expert:
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to view this request.')
                }, status=403)
        elif request.user.account_type != 'admin':
            return JsonResponse({
                'success': False,
                'message': _('You do not have permission to view this request.')
            }, status=403)
        
        # Get documents
        documents = []
        for doc in Document.objects.filter(demande=demande):
            documents.append({
                'id': doc.id,
                'name': doc.name,
                'type': doc.type,
                'uploaded_by': f"{doc.uploaded_by.name} {doc.uploaded_by.first_name}",
                'upload_date': doc.upload_date.isoformat(),
                'is_official': doc.is_official
            })
        
        # Get messages
        messages_data = []
        for msg in Message.objects.filter(demande=demande).order_by('sent_at'):
            messages_data.append({
                'id': msg.id,
                'sender': {
                    'id': msg.sender.id,
                    'name': f"{msg.sender.name} {msg.sender.first_name}",
                    'account_type': msg.sender.account_type
                },
                'content': msg.content,
                'sent_at': msg.sent_at.isoformat(),
                'is_read': msg.is_read
            })
        
        # Get appointments
        appointments = []
        for appt in RendezVous.objects.filter(demande=demande):
            appointments.append({
                'id': appt.id,
                'date_time': appt.date_time.isoformat(),
                'expert': {
                    'id': appt.expert.id,
                    'name': f"{appt.expert.user.name} {appt.expert.user.first_name}"
                },
                'consultation_type': appt.consultation_type,
                'status': appt.status
            })
        
        # Prepare response data
        request_data = {
            'id': demande.id,
            'title': demande.title,
            'description': demande.description,
            'service': {
                'id': demande.service.id,
                'title': demande.service.title,
                'category': demande.service.category
            },
            'client': {
                'id': demande.client.id,
                'name': f"{demande.client.user.name} {demande.client.user.first_name}"
            },
            'status': demande.status,
            'priority': demande.priority,
            'created_at': demande.created_at.isoformat(),
            'expert': {
                'id': demande.assigned_expert.id,
                'name': f"{demande.assigned_expert.user.name} {demande.assigned_expert.user.first_name}",
            } if demande.assigned_expert else None,
            'documents': documents,
            'messages': messages_data,
            'appointments': appointments
        }
        
        return JsonResponse({
            'success': True,
            'request': request_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=404)

@login_required
@csrf_exempt
def api_client_appointments(request):
    """API endpoint for client appointments"""
    try:
        if request.user.account_type == 'client':
            client = Client.objects.get(user=request.user)
            appointments_query = RendezVous.objects.filter(client=client).order_by('date_time')
        elif request.user.account_type == 'expert':
            expert = Expert.objects.get(user=request.user)
            appointments_query = RendezVous.objects.filter(expert=expert).order_by('date_time')
        elif request.user.account_type == 'admin':
            appointments_query = RendezVous.objects.all().order_by('date_time')
        else:
            return JsonResponse({
                'success': False,
                'message': _('Invalid user type.')
            }, status=403)
        
        # Apply status filter if provided
        status = request.GET.get('status')
        if status:
            appointments_query = appointments_query.filter(status=status)
        
        # Apply date filter if provided
        date_from = request.GET.get('date_from')
        if date_from:
            try:
                date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                date_from = timezone.make_aware(date_from)
                appointments_query = appointments_query.filter(date_time__gte=date_from)
            except ValueError:
                pass
        
        date_to = request.GET.get('date_to')
        if date_to:
            try:
                date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                date_to = timezone.make_aware(date_to)
                appointments_query = appointments_query.filter(date_time__lte=date_to)
            except ValueError:
                pass
        
        # Prepare response data
        appointments_data = []
        for appointment in appointments_query:
            appointments_data.append({
                'id': appointment.id,
                'date_time': appointment.date_time.isoformat(),
                'duration': appointment.duration,
                'client': {
                    'id': appointment.client.id,
                    'name': f"{appointment.client.user.name} {appointment.client.user.first_name}"
                },
                'expert': {
                    'id': appointment.expert.id,
                    'name': f"{appointment.expert.user.name} {appointment.expert.user.first_name}"
                },
                'service': {
                    'id': appointment.service.id,
                    'title': appointment.service.title,
                } if appointment.service else None,
                'consultation_type': appointment.consultation_type,
                'status': appointment.status,
                'request': {
                    'id': appointment.demande.id,
                    'title': appointment.demande.title
                } if appointment.demande else None
            })
        
        return JsonResponse({
            'success': True,
            'appointments': appointments_data
        })
    
    except (Client.DoesNotExist, Expert.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': _('Profile not found.')
        }, status=404)

@login_required
@csrf_exempt
def api_expert_requests(request):
    """API endpoint for expert requests"""
    try:
        expert = Expert.objects.get(user=request.user)
        requests_query = ServiceRequest.objects.filter(assigned_expert=expert).order_by('-created_at')
        
        # Apply status filter if provided
        status = request.GET.get('status')
        if status:
            requests_query = requests_query.filter(status=status)
        
        # Prepare response data
        requests_data = []
        for demande in requests_query:
            requests_data.append({
                'id': demande.id,
                'title': demande.title,
                'service': {
                    'id': demande.service.id,
                    'title': demande.service.title,
                    'category': demande.service.category
                },
                'client': {
                    'id': demande.client.id,
                    'name': f"{demande.client.user.name} {demande.client.user.first_name}"
                },
                'status': demande.status,
                'priority': demande.priority,
                'created_at': demande.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'requests': requests_data
        })
    
    except Expert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Expert profile not found.')
        }, status=404)

@login_required
@csrf_exempt
@require_POST
def api_upload_document(request):
    """API endpoint to upload a document"""
    try:
        data = request.POST
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({
                'success': False,
                'message': _('No file provided.')
            }, status=400)
        
        name = data.get('name', file.name)
        document_type = data.get('type', 'other')
        demande_id = data.get('demande_id')
        rendez_vous_id = data.get('rendez_vous_id')
        is_official = data.get('is_official') == 'true'
        reference_number = data.get('reference_number', '')
        
        # Get related demande and rendez_vous if provided
        demande = None
        rendez_vous = None
        
        if demande_id:
            demande = get_object_or_404(ServiceRequest, id=demande_id)
        
        if rendez_vous_id:
            rendez_vous = get_object_or_404(RendezVous, id=rendez_vous_id)
        
        # Create document
        document = Document.objects.create(
            demande=demande,
            rendez_vous=rendez_vous,
            uploaded_by=request.user,
            type=document_type,
            name=name,
            file=file,
            mime_type=file.content_type,
            file_size=file.size // 1024,  # Convert to KB
            is_official=is_official,
            reference_number=reference_number
        )
        
        # Create appropriate notifications
        if demande:
            if request.user.account_type == 'client':
                if demande.assigned_expert:
                    Notification.objects.create(
                        user=demande.assigned_expert.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for request "{demande.title}".'),
                        related_demande=demande
                    )
            else:
                Notification.objects.create(
                    user=demande.client.user,
                    type='document',
                    title=_('New Document Uploaded'),
                    content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your request "{demande.title}".'),
                    related_demande=demande
                )
        
        if rendez_vous:
            if request.user.account_type == 'client':
                Notification.objects.create(
                    user=rendez_vous.expert.user,
                    type='document',
                    title=_('New Document Uploaded'),
                    content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                    related_rendez_vous=rendez_vous
                )
            else:
                Notification.objects.create(
                    user=rendez_vous.client.user,
                    type='document',
                    title=_('New Document Uploaded'),
                    content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                    related_rendez_vous=rendez_vous
                )
        
        return JsonResponse({
            'success': True,
            'document': {
                'id': document.id,
                'name': document.name,
                'type': document.type,
                'file_url': document.file.url if document.file else None,
                'upload_date': document.upload_date.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@csrf_exempt
def api_messages(request):
    """API endpoint for user messages"""
    if request.method == 'GET':
        # Get messages with a specific user if provided
        other_user_id = request.GET.get('user_id')
        if other_user_id:
            try:
                other_user = Utilisateur.objects.get(id=other_user_id)
                messages_query = Message.objects.filter(
                    (Q(sender=request.user) & Q(recipient=other_user)) |
                    (Q(sender=other_user) & Q(recipient=request.user))
                ).order_by('sent_at')
                
                # Mark messages as read
                Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(
                    is_read=True,
                    read_at=timezone.now()
                )
                
                # Prepare response data
                messages_data = []
                for message in messages_query:
                    messages_data.append({
                        'id': message.id,
                        'sender': {
                            'id': message.sender.id,
                            'name': f"{message.sender.name} {message.sender.first_name}",
                            'account_type': message.sender.account_type
                        },
                        'content': message.content,
                        'sent_at': message.sent_at.isoformat(),
                        'is_read': message.is_read,
                        'is_mine': message.sender == request.user
                    })
                
                return JsonResponse({
                    'success': True,
                    'messages': messages_data,
                    'other_user': {
                        'id': other_user.id,
                        'name': f"{other_user.name} {other_user.first_name}",
                        'account_type': other_user.account_type
                    }
                })
                
            except Utilisateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': _('User not found.')
                }, status=404)
        
        # Otherwise, return conversation summary
        messages = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).order_by('-sent_at')
        
        # Group messages by conversation
        conversations = {}
        for message in messages:
            # Determine the other party in the conversation
            other_party = message.recipient if message.sender == request.user else message.sender
            
            # Create a unique key for this conversation
            conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
            
            if conversation_key not in conversations:
                conversations[conversation_key] = {
                    'user': {
                        'id': other_party.id,
                        'name': f"{other_party.name} {other_party.first_name}",
                        'account_type': other_party.account_type
                    },
                    'latest_message': {
                        'id': message.id,
                        'content': message.content,
                        'sent_at': message.sent_at.isoformat(),
                        'is_read': message.is_read,
                        'is_mine': message.sender == request.user
                    },
                    'unread_count': 1 if message.recipient == request.user and not message.is_read else 0
                }
            else:
                # Update latest message if this one is newer
                if message.sent_at > timezone.datetime.fromisoformat(conversations[conversation_key]['latest_message']['sent_at']):
                    conversations[conversation_key]['latest_message'] = {
                        'id': message.id,
                        'content': message.content,
                        'sent_at': message.sent_at.isoformat(),
                        'is_read': message.is_read,
                        'is_mine': message.sender == request.user
                    }
                
                # Update unread count
                if message.recipient == request.user and not message.is_read:
                    conversations[conversation_key]['unread_count'] += 1
        
        # Convert dictionary to list and sort by latest message date
        conversations_list = sorted(
            conversations.values(),
            key=lambda x: x['latest_message']['sent_at'],
            reverse=True
        )
        
        return JsonResponse({
            'success': True,
            'conversations': conversations_list
        })
    
    elif request.method == 'POST':
        # Send a new message
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        demande_id = data.get('demande_id')
        
        if not content or not recipient_id:
            return JsonResponse({
                'success': False,
                'message': _('Recipient and content are required.')
            }, status=400)
        
        try:
            recipient = Utilisateur.objects.get(id=recipient_id)
            
            # Get related request if provided
            demande = None
            if demande_id:
                demande = get_object_or_404(ServiceRequest, id=demande_id)
            
            # Create message
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                demande=demande
            )
            
            # Create notification for recipient
            Notification.objects.create(
                user=recipient,
                type='message',
                title=_('New Message'),
                content=_(f'You have a new message from {request.user.name} {request.user.first_name}.'),
                related_message=message,
                related_demande=demande
            )
            
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sent_at': message.sent_at.isoformat(),
                    'is_read': message.is_read
                }
            })
            
        except Utilisateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Recipient not found.')
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': _('Method not allowed.')
    }, status=405)

@login_required
@csrf_exempt
def api_notifications(request):
    """API endpoint for user notifications"""
    notifications_query = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Get only unread if specified
    unread_only = request.GET.get('unread_only') == 'true'
    if unread_only:
        notifications_query = notifications_query.filter(is_read=False)
    
    # Limit number of notifications if specified
    limit = request.GET.get('limit')
    if limit:
        try:
            limit = int(limit)
            notifications_query = notifications_query[:limit]
        except ValueError:
            pass
    
    # Prepare response data
    notifications_data = []
    for notification in notifications_query:
        notifications_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'content': notification.content,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'related_demande_id': notification.related_demande.id if notification.related_demande else None,
            'related_rendez_vous_id': notification.related_rendez_vous.id if notification.related_rendez_vous else None,
            'related_message_id': notification.related_message.id if notification.related_message else None
        })
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_data,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
    })
