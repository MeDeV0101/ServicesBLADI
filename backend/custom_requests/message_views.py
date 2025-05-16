from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Utilisateur, Client, Expert
from .models import Message, Notification, ServiceRequest

@login_required
def client_messages_view(request):
    """Display client's messages and handle conversations"""
    # Get the active contact if provided
    active_contact_id = request.GET.get('contact')
    active_contact = None
    messages_list = []
    
    # Get all messages for this user
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # Group messages by conversation
    conversations = {}
    for message in all_messages:
        # Determine the other party in the conversation
        other_party = message.recipient if message.sender == request.user else message.sender
        
        # Create a unique key for this conversation
        conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
        
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'user': other_party,
                'latest_message': message,
                'unread_count': 1 if message.recipient == request.user and not message.is_read else 0,
                'last_message': message.content[:50] + '...' if len(message.content) > 50 else message.content,
                'last_message_time': message.sent_at
            }
        else:
            # Update latest message if this one is newer
            if message.sent_at > conversations[conversation_key]['latest_message'].sent_at:
                conversations[conversation_key]['latest_message'] = message
                conversations[conversation_key]['last_message'] = message.content[:50] + '...' if len(message.content) > 50 else message.content
                conversations[conversation_key]['last_message_time'] = message.sent_at
            
            # Update unread count
            if message.recipient == request.user and not message.is_read:
                conversations[conversation_key]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message date
    contacts = sorted(
        conversations.values(),
        key=lambda x: x['latest_message'].sent_at,
        reverse=True
    )
    
    # If a contact is selected, get conversation with that contact
    if active_contact_id:
        active_contact = get_object_or_404(Utilisateur, id=active_contact_id)
        
        # Get conversation messages
        messages_list = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient=active_contact)) |
            (Q(sender=active_contact) & Q(recipient=request.user))
        ).order_by('sent_at')
        
        # Mark messages as read
        unread_messages = messages_list.filter(recipient=request.user, is_read=False)
        unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Count total unread messages
    unread_messages_count = sum([conv['unread_count'] for conv in conversations.values()])
    
    context = {
        'contacts': contacts,
        'messages': messages_list,
        'active_contact': active_contact,
        'unread_messages_count': unread_messages_count
    }
    
    return render(request, 'client/messages.html', context)

@login_required
def client_send_message(request, recipient_id):
    """Handle sending a new message from client"""
    if request.method != 'POST':
        return redirect('client_messages')
    
    recipient = get_object_or_404(Utilisateur, id=recipient_id)
    content = request.POST.get('message', '').strip()
    
    if not content:
        return redirect('client_messages')
    
    # Create message
    message = Message.objects.create(
        sender=request.user,
        recipient=recipient,
        content=content
    )
    
    # Create notification for recipient
    Notification.objects.create(
        user=recipient,
        type='message',
        title=_('New Message'),
        content=_(f'You have a new message from {request.user.name} {request.user.first_name}.'),
        related_message=message
    )
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sent_at': message.sent_at.isoformat()
            }
        })
    
    # Otherwise redirect back to the conversation
    return redirect(f'client_messages?contact={recipient_id}')

@login_required
def client_check_messages(request):
    """Check for new messages in the current conversation"""
    contact_id = request.GET.get('contact')
    if not contact_id:
        return JsonResponse({'success': False})
    
    contact = get_object_or_404(Utilisateur, id=contact_id)
    
    # Check for new unread messages from this contact
    new_messages = Message.objects.filter(
        sender=contact,
        recipient=request.user,
        is_read=False
    ).exists()
    
    return JsonResponse({
        'success': True,
        'new_messages': new_messages
    })

@login_required
def expert_messages_view(request):
    """Display expert's messages with clients"""
    # Similar logic to client_messages_view but for experts
    # Get the active client if provided
    active_client_id = request.GET.get('client')
    active_client = None
    messages_list = []
    
    # Get all messages for this expert
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # Group messages by conversation (similar to client_messages_view)
    conversations = {}
    for message in all_messages:
        other_party = message.recipient if message.sender == request.user else message.sender
        conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
        
        if other_party.account_type != 'client':
            continue  # Only show conversations with clients
        
        # Similar logic to client_messages_view...
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'id': other_party.id,
                'name': f"{other_party.name} {other_party.first_name}",
                'email': other_party.email,
                'latest_message': message.content[:50] + '...' if len(message.content) > 50 else message.content,
                'unread_count': 1 if message.recipient == request.user and not message.is_read else 0,
                'time': message.sent_at,
                'is_online': False  # This could be updated with a real online status system
            }
        else:
            if message.recipient == request.user and not message.is_read:
                conversations[conversation_key]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message time
    clients = sorted(
        conversations.values(),
        key=lambda x: x['time'],
        reverse=True
    )
    
    # If a client is selected, get conversation with that client
    if active_client_id:
        active_client = get_object_or_404(Utilisateur, id=active_client_id)
        
        # Get conversation messages
        messages_list = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient=active_client)) |
            (Q(sender=active_client) & Q(recipient=request.user))
        ).order_by('sent_at')
        
        # Mark messages as read
        unread_messages = messages_list.filter(recipient=request.user, is_read=False)
        unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Count total unread messages
    unread_messages_count = sum([client.get('unread_count', 0) for client in clients])
    
    context = {
        'clients': clients,
        'messages': messages_list,
        'active_client': active_client,
        'unread_messages_count': unread_messages_count
    }
    
    return render(request, 'expert/messages.html', context)

@login_required
def expert_send_message(request, client_id):
    """Handle sending a new message from expert to client"""
    # Similar implementation to client_send_message
    if request.method != 'POST':
        return redirect('expert_messages')
    
    client = get_object_or_404(Utilisateur, id=client_id, account_type='client')
    content = request.POST.get('message', '').strip()
    
    if not content:
        return redirect('expert_messages')
    
    # Create message
    message = Message.objects.create(
        sender=request.user,
        recipient=client,
        content=content
    )
    
    # Create notification for client
    Notification.objects.create(
        user=client,
        type='message',
        title=_('New Message'),
        content=_(f'You have a new message from your expert {request.user.name} {request.user.first_name}.'),
        related_message=message
    )
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sent_at': message.sent_at.isoformat()
            }
        })
    
    # Otherwise redirect back to the conversation
    return redirect(f'expert_messages?client={client_id}')

@login_required
def expert_check_messages(request):
    """Check for new messages from a client"""
    # Similar implementation to client_check_messages
    client_id = request.GET.get('client')
    if not client_id:
        return JsonResponse({'success': False})
    
    client = get_object_or_404(Utilisateur, id=client_id, account_type='client')
    
    # Check for new unread messages from this client
    new_messages = Message.objects.filter(
        sender=client,
        recipient=request.user,
        is_read=False
    ).exists()
    
    return JsonResponse({
        'success': True,
        'new_messages': new_messages
    })
