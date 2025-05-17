from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from custom_requests.models import ServiceRequest, Message

# Create your views here.

@login_required
def chat_view(request, request_id):
    """Vue pour afficher la page de chat entre un client et un expert"""
    
    # Récupérer la demande de service
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    # Vérifier les autorisations
    if request.user.account_type.lower() == 'client':
        # Le client doit être le propriétaire de la demande
        if service_request.client != request.user:
            messages.error(request, "Vous n'avez pas accès à cette conversation.")
            return redirect('client_dashboard')
        
        # Vérifier si l'expert a déjà envoyé un message
        has_expert_message = Message.objects.filter(
            sender=service_request.expert,
            recipient=request.user,
            service_request=service_request
        ).exists()
        
        if not has_expert_message:
            messages.warning(request, "L'expert n'a pas encore initié la conversation. Veuillez patienter.")
            return redirect('client_demandes')
    
    elif request.user.account_type.lower() == 'expert':
        # L'expert doit être assigné à la demande
        if service_request.expert != request.user:
            messages.error(request, "Vous n'êtes pas l'expert assigné à cette demande.")
            return redirect('expert_demandes')
    
    elif request.user.account_type.lower() == 'admin':
        # Les administrateurs ont accès à toutes les conversations
        pass
    
    else:
        # Autres types d'utilisateurs n'ont pas accès
        messages.error(request, "Vous n'avez pas les autorisations nécessaires pour accéder à cette page.")
        return redirect('home')
    
    # Récupérer les messages de cette conversation
    chat_messages = Message.objects.filter(
        service_request=service_request
    ).order_by('sent_at')
    
    # Marquer les messages non lus comme lus
    unread_messages = chat_messages.filter(recipient=request.user, is_read=False)
    for msg in unread_messages:
        msg.is_read = True
        msg.save()
    
    context = {
        'service_request': service_request,
        'chat_messages': chat_messages,
        'user_type': request.user.account_type.lower(),
        'request_id': request_id
    }
    
    if request.user.account_type.lower() == 'client':
        return render(request, 'messaging/client_chat.html', context)
    elif request.user.account_type.lower() == 'expert':
        return render(request, 'messaging/expert_chat.html', context)
    else:  # admin
        return render(request, 'messaging/admin_chat.html', context)
