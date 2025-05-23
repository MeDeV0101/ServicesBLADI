from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _

from accounts.models import Utilisateur, Expert, Client
from custom_requests.models import ServiceRequest, Document, RendezVous, Message, Notification

@login_required
def expert_documents_view(request):
    """View function for expert document management."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get documents associated with this expert
        documents = Document.objects.filter(
            Q(service_request__expert=expert.user) |
            Q(rendez_vous__expert=expert.user) |
            Q(uploaded_by=request.user)
        ).distinct().order_by('-upload_date')
        
        context = {
            'documents': documents,
            'expert': expert
        }
        
        return render(request, 'expert/documents_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointments_view(request):
    """View function for expert appointments."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointments for this expert
        appointments = RendezVous.objects.filter(
            expert=expert.user
        ).order_by('date_time')
        
        context = {
            'appointments': appointments,
            'expert': expert
        }
        
        return render(request, 'expert/appointments_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_messages_view(request):
    """View function for expert messages."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get all clients who have had appointments or service requests with this expert
        clients = Client.objects.filter(
            Q(servicerequest__expert=expert.user) |
            Q(rendezvous__expert=expert.user)
        ).distinct()
        
        # Get active client if any
        active_client_id = request.GET.get('client')
        active_client = None
        messages = []
        
        if active_client_id:
            active_client = get_object_or_404(Client, id=active_client_id)
            
            # Get messages between expert and client
            messages = Message.objects.filter(
                (Q(sender=request.user) & Q(recipient=active_client.user)) |
                (Q(sender=active_client.user) & Q(recipient=request.user))
            ).order_by('sent_at')
            
            # Mark messages as read
            unread_messages = messages.filter(recipient=request.user, is_read=False)
            for message in unread_messages:
                message.is_read = True
                message.save()
        
        context = {
            'clients': clients,
            'active_client': active_client,
            'messages': messages,
            'expert': expert
        }
        
        return render(request, 'expert/messages_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_requests_view_new(request):
    """View function for expert requests."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get service requests assigned to this expert
        requests = ServiceRequest.objects.filter(
            expert=expert.user
        ).order_by('-created_at')
        
        context = {
            'requests': requests,
            'expert': expert
        }
        
        return render(request, 'expert/requests_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_resources_view(request):
    """View function for expert resources."""
    if request.user.account_type.lower() not in ['expert', 'admin']:
        return redirect('home')

    try:
        if request.user.account_type.lower() == 'expert':
            expert = Expert.objects.get(user=request.user)
        else:
            expert = None
        
        # Import here to avoid circular import
        from resources.models import Resource, ResourceFile, ResourceLink
        from django.contrib import messages
        import os
        
        # Get resources
        resources = Resource.objects.all().order_by('-id')
        
        # Get resource categories for filtering
        resource_categories = Resource.CATEGORIES
        
        # Handle resource addition
        if request.method == 'POST' and 'add_resource' in request.POST:
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            
            if title and description and category:
                resource = Resource.objects.create(
                    title=title,
                    description=description,
                    category=category,
                    created_by=request.user
                )
                
                # Handle files if any
                if request.FILES.getlist('files'):
                    for file in request.FILES.getlist('files'):
                        extension = os.path.splitext(file.name)[1][1:].lower()
                        format_type = 'pdf' if extension == 'pdf' else 'doc' if extension in ['doc', 'docx'] else 'xls' if extension in ['xls', 'xlsx'] else 'ppt' if extension in ['ppt', 'pptx'] else 'image' if extension in ['jpg', 'jpeg', 'png', 'gif'] else 'video' if extension in ['mp4', 'avi', 'mov'] else 'text'
                        
                        ResourceFile.objects.create(
                            resource=resource,
                            file=file,
                            format_type=format_type
                        )
                
                # Handle links if any
                link = request.POST.get('link')
                if link:
                    ResourceLink.objects.create(
                        resource=resource,
                        url=link,
                        title=title
                    )
                    
                messages.success(request, _('Resource added successfully.'))
                return redirect('expert_resources')
            else:
                messages.error(request, _('Please fill in all required fields.'))
        
        # Handle resource deletion
        elif request.method == 'POST' and 'delete_resource' in request.POST:
            resource_id = request.POST.get('resource_id')
            if resource_id:
                try:
                    resource = Resource.objects.get(id=resource_id)
                    resource.delete()
                    messages.success(request, _('Resource deleted successfully.'))
                except Resource.DoesNotExist:
                    messages.error(request, _('Resource not found.'))
                return redirect('expert_resources')
        
        # Handle resource editing
        elif request.method == 'POST' and 'edit_resource' in request.POST:
            resource_id = request.POST.get('resource_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            
            if resource_id and title and description and category:
                try:
                    resource = Resource.objects.get(id=resource_id)
                    resource.title = title
                    resource.description = description
                    resource.category = category
                    resource.save()
                    
                    # Handle new files if any
                    if request.FILES.getlist('files'):
                        for file in request.FILES.getlist('files'):
                            extension = os.path.splitext(file.name)[1][1:].lower()
                            format_type = 'pdf' if extension == 'pdf' else 'doc' if extension in ['doc', 'docx'] else 'xls' if extension in ['xls', 'xlsx'] else 'ppt' if extension in ['ppt', 'pptx'] else 'image' if extension in ['jpg', 'jpeg', 'png', 'gif'] else 'video' if extension in ['mp4', 'avi', 'mov'] else 'text'
                            
                            ResourceFile.objects.create(
                                resource=resource,
                                file=file,
                                format_type=format_type
                            )
                    
                    # Handle new link if any
                    link = request.POST.get('link')
                    if link:
                        ResourceLink.objects.get_or_create(
                            resource=resource,
                            defaults={
                                'url': link,
                                'title': title
                            }
                        )
                    
                    messages.success(request, _('Resource updated successfully.'))
                except Resource.DoesNotExist:
                    messages.error(request, _('Resource not found.'))
                return redirect('expert_resources')
            else:
                messages.error(request, _('Please fill in all required fields.'))
        
        context = {
            'resources': resources,
            'expert': expert,
            'resource_categories': resource_categories,
            'formats': Resource.FORMAT_TYPES
        }
        
        return render(request, 'expert/ressources_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')
<<<<<<< HEAD
=======
    except Exception as e:
        print(f"Error in expert_resources_view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, _(f'An error occurred: {str(e)}'))
        return redirect('home')

@login_required
def expert_request_detail(request, request_id):
    """View to display detailed information about a specific service request for expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    try:
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Print debug info
        print(f"Found service request: {service_request.id} - {service_request.title}")
        print(f"Expert assigned: {service_request.expert}")
        print(f"Current user: {request.user}")
        
        # Simple direct render - skip all other queries for troubleshooting
        context = {
            'service_request': service_request,
            'documents': [],
            'messages_list': [],
            'appointments': []
        }
        
        return render(request, 'expert/request_detail.html', context)
    
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur: {str(e)}")
        print(f"Error in expert_request_detail: {str(e)}")
        return redirect('expert_demandes')

@login_required
def expert_send_message(request):
    """Handle sending a message from expert to client or admin"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        service_request_id = request.POST.get('service_request_id')
        
        if not recipient_id or not content:
            from django.contrib import messages
            messages.error(request, "Le destinataire et le contenu sont obligatoires.")
            if service_request_id:
                return redirect('expert_request_detail', request_id=service_request_id)
            return redirect('expert_demandes')
        
        # Get the recipient
        recipient = get_object_or_404(Utilisateur, id=recipient_id)
        
        # Get the service request if available
        service_request = None
        if service_request_id:
            service_request = get_object_or_404(ServiceRequest, id=service_request_id)
            
            # Check if this expert is assigned to this request
            if service_request.expert != request.user:
                from django.contrib import messages
                messages.error(request, "Vous n'êtes pas autorisé à envoyer des messages pour cette demande.")
                return redirect('expert_demandes')
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content,
            service_request=service_request
        )
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('Nouveau message'),
            content=_(f'Vous avez reçu un nouveau message de {request.user.first_name} {request.user.name}.'),
            related_message=message,
            related_service_request=service_request
        )
        
        from django.contrib import messages
        messages.success(request, _('Message envoyé avec succès.'))
        
        # Redirect back to appropriate page
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur lors de l'envoi du message: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_upload_document(request):
    """Handle document upload from expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        name = request.POST.get('name')
        document_type = request.POST.get('type')
        service_request_id = request.POST.get('service_request_id')
        
        if not name or not document_type or not service_request_id or 'file' not in request.FILES:
            from django.contrib import messages
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('expert_request_detail', request_id=service_request_id)
        
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=service_request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            from django.contrib import messages
            messages.error(request, "Vous n'êtes pas autorisé à télécharger des documents pour cette demande.")
            return redirect('expert_demandes')
        
        # Get the file
        file = request.FILES['file']
        
        # Create the document
        document = Document.objects.create(
            name=name,
            type=document_type,
            service_request=service_request,
            uploaded_by=request.user,
            file=file
        )
        
        # Create notification for client
        Notification.objects.create(
            user=service_request.client,
            type='document',
            title=_('Nouveau document'),
            content=_(f'Un nouveau document "{name}" a été téléchargé pour votre demande "{service_request.title}".'),
            related_service_request=service_request
        )
        
        from django.contrib import messages
        messages.success(request, _('Document téléchargé avec succès.'))
        
        return redirect('expert_request_detail', request_id=service_request_id)
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur lors du téléchargement du document: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_update_request_status(request, request_id):
    """Update the status of a service request by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_request_detail', request_id=request_id)
    
    try:
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            from django.contrib import messages
            messages.error(request, "Vous n'êtes pas autorisé à mettre à jour cette demande.")
            return redirect('expert_demandes')
        
        # Get the new status
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        # Verify that the status is valid for experts
        valid_statuses = ['in_progress', 'pending_info', 'completed']
        if new_status not in valid_statuses:
            from django.contrib import messages
            messages.error(request, "Statut invalide.")
            return redirect('expert_request_detail', request_id=request_id)
        
        # Update the request status
        service_request.status = new_status
        service_request.save()
        
        # Add comment as message if provided
        if comment:
            Message.objects.create(
                sender=request.user,
                recipient=service_request.client,
                content=_('Statut mis à jour: ') + comment,
                service_request=service_request
            )
        
        # Create notification for client
        status_display = dict(ServiceRequest.STATUS_CHOICES).get(new_status, new_status)
        Notification.objects.create(
            user=service_request.client,
            type='request_update',
            title=_('Statut de demande mis à jour'),
            content=_(f'Le statut de votre demande "{service_request.title}" a été mis à jour à "{status_display}".'),
            related_service_request=service_request
        )
        
        from django.contrib import messages
        messages.success(request, _('Statut mis à jour avec succès.'))
        
        return redirect('expert_request_detail', request_id=request_id)
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur lors de la mise à jour du statut: {str(e)}")
        return redirect('expert_request_detail', request_id=request_id)

@login_required
def expert_schedule_appointment(request):
    """Handle scheduling of appointment by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        service_request_id = request.POST.get('service_request_id')
        date_time_str = request.POST.get('date_time')
        duration = request.POST.get('duration')
        appointment_type = request.POST.get('type')
        notes = request.POST.get('notes', '')
        
        if not service_request_id or not date_time_str or not duration or not appointment_type:
            from django.contrib import messages
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('expert_request_detail', request_id=service_request_id)
        
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=service_request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            from django.contrib import messages
            messages.error(request, "Vous n'êtes pas autorisé à planifier des rendez-vous pour cette demande.")
            return redirect('expert_demandes')
        
        # Convert date_time from string to datetime
        from datetime import datetime
        date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        
        # Create the appointment
        appointment = RendezVous.objects.create(
            client=service_request.client,
            expert=request.user,
            service_request=service_request,
            date_time=date_time,
            duration=duration,
            type=appointment_type,
            notes=notes,
            status='scheduled'
        )
        
        # Create notification for client
        Notification.objects.create(
            user=service_request.client,
            type='appointment',
            title=_('Nouveau rendez-vous'),
            content=_(f'Un rendez-vous a été planifié pour votre demande "{service_request.title}" le {date_time.strftime("%d/%m/%Y à %H:%M")}.'),
            related_service_request=service_request
        )
        
        from django.contrib import messages
        messages.success(request, _('Rendez-vous planifié avec succès.'))
        
        return redirect('expert_request_detail', request_id=service_request_id)
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur lors de la planification du rendez-vous: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_update_appointment(request):
    """Handle updating of appointment status by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        appointment_id = request.POST.get('appointment_id')
        status = request.POST.get('status')
        
        if not appointment_id or not status:
            from django.contrib import messages
            messages.error(request, "L'identifiant du rendez-vous et le statut sont obligatoires.")
            return redirect('expert_demandes')
        
        # Get the appointment
        appointment = get_object_or_404(RendezVous, id=appointment_id)
        
        # Check if this expert is assigned to this appointment
        if appointment.expert != request.user:
            from django.contrib import messages
            messages.error(request, "Vous n'êtes pas autorisé à mettre à jour ce rendez-vous.")
            return redirect('expert_demandes')
        
        # Check if status is valid
        if status not in ['completed', 'cancelled']:
            from django.contrib import messages
            messages.error(request, "Statut invalide.")
            return redirect('expert_request_detail', request_id=appointment.service_request.id)
        
        # Update the appointment status
        appointment.status = status
        appointment.save()
        
        # Create notification for client
        status_display = 'terminé' if status == 'completed' else 'annulé'
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Statut de rendez-vous mis à jour'),
            content=_(f'Votre rendez-vous du {appointment.date_time.strftime("%d/%m/%Y à %H:%M")} a été marqué comme {status_display}.'),
            related_service_request=appointment.service_request
        )
        
        from django.contrib import messages
        messages.success(request, _(f'Rendez-vous marqué comme {status_display} avec succès.'))
        
        return redirect('expert_request_detail', request_id=appointment.service_request.id)
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur lors de la mise à jour du rendez-vous: {str(e)}")
        return redirect('expert_demandes')
>>>>>>> parent of 5b7d8e5 (start setup messaging feature)
