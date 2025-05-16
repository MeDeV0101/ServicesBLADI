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
