import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from custom_requests.models import Message, Notification, ServiceRequest
from accounts.models import Utilisateur

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour la messagerie en temps réel entre client et expert.
    Vérifie que l'expert a le droit de communiquer avec ce client
    (la demande doit être attribuée à l'expert).
    """

    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            # Rejeter la connexion si l'utilisateur n'est pas authentifié
            await self.close()
            return

        # Récupérer les paramètres de l'URL
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.room_group_name = f'chat_{self.request_id}'

        # Vérifier les permissions
        can_access = await self.can_access_chat()
        if not can_access:
            # Rejeter la connexion si l'utilisateur n'a pas les permissions
            await self.close()
            return

        # Rejoindre le groupe de chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connection accepted for {self.user.account_type} (ID: {self.user.id}) in room {self.room_group_name}")

    async def disconnect(self, close_code):
        # Quitter le groupe de chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for {self.user.account_type} (ID: {self.user.id}) from room {self.room_group_name}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        # Vérifier à nouveau les permissions
        can_access = await self.can_access_chat()
        if not can_access:
            print(f"Access denied for {self.user.account_type} (ID: {self.user.id}) to room {self.room_group_name}")
            return
        
        # Gérer les indicateurs de frappe
        if 'typing' in text_data_json:
            # Envoyer l'état de frappe au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'user_id': self.user.id,
                    'user_name': f"{self.user.first_name} {self.user.name}",
                    'is_typing': text_data_json['typing']
                }
            )
            return
        
        # Traiter les messages normaux
        if 'message' in text_data_json:
            message = text_data_json['message']
            
            # Ajouter des logs pour le débogage
            print(f"Message reçu de {self.user.account_type} (ID: {self.user.id}): {message[:30]}...")
            
            # Vérifier si c'est un client qui essaie d'initier la conversation
            if self.user.account_type.lower() == 'client':
                has_prior_message = await self.has_prior_message_from_expert()
                if not has_prior_message:
                    # Rejeter le message si le client essaie d'initier la conversation
                    print(f"Rejet du message du client {self.user.id}: pas de message préalable de l'expert")
                    await self.send(text_data=json.dumps({
                        'error': 'Vous ne pouvez pas initier une conversation avec un expert. '
                                 'Veuillez attendre que l\'expert vous contacte.'
                    }))
                    return

            # Enregistrer le message dans la base de données
            try:
                message_instance = await self.save_message(message)
                
                # Envoyer le message au groupe
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.user.id,
                        'sender_name': f"{self.user.first_name} {self.user.name}",
                        'sender_type': self.user.account_type,
                        'timestamp': message_instance.sent_at.isoformat()
                    }
                )
                print(f"Message envoyé au groupe {self.room_group_name}")
            except Exception as e:
                print(f"Erreur lors de l'enregistrement du message: {str(e)}")
                await self.send(text_data=json.dumps({
                    'error': 'Une erreur est survenue lors de l\'envoi du message. Veuillez réessayer.'
                }))

    async def chat_message(self, event):
        # Envoyer le message au WebSocket
        print(f"Sending message to websocket: {self.user.account_type} (ID: {self.user.id})")
        print(f"Message content: {event['message'][:30]}...")
        print(f"Sender ID: {event['sender_id']}, Current user ID: {self.user.id}")
        
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'sender_type': event['sender_type'],
            'timestamp': event['timestamp']
        }))
        print(f"Message sent to websocket for {self.user.account_type} (ID: {self.user.id})")

    async def typing_status(self, event):
        # Envoyer l'état de frappe au WebSocket
        await self.send(text_data=json.dumps({
            'typing': {
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }
        }))

    @database_sync_to_async
    def can_access_chat(self):
        """Vérifier si l'utilisateur peut accéder à cette conversation"""
        try:
            service_request = ServiceRequest.objects.get(id=self.request_id)
            
            # Si l'utilisateur est le client de cette demande
            if self.user.account_type.lower() == 'client' and service_request.client == self.user:
                return True
            
            # Si l'utilisateur est l'expert assigné à cette demande
            if self.user.account_type.lower() == 'expert' and service_request.expert == self.user:
                return True
            
            # Si l'utilisateur est un administrateur
            if self.user.account_type.lower() == 'admin':
                return True
            
            return False
        except ServiceRequest.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """Enregistrer le message dans la base de données"""
        service_request = ServiceRequest.objects.get(id=self.request_id)
        
        # Déterminer le destinataire en fonction de l'expéditeur
        if self.user.account_type.lower() == 'client':
            recipient = service_request.expert
        else:  # expert ou admin
            recipient = service_request.client
        
        # Créer le message
        message = Message.objects.create(
            sender=self.user,
            recipient=recipient,
            content=content,
            service_request=service_request,
            sent_at=timezone.now()
        )
        
        # Créer une notification pour le destinataire
        Notification.objects.create(
            user=recipient,
            type='message',
            title='Nouveau message',
            content=f'Vous avez reçu un nouveau message de {self.user.first_name} {self.user.name}',
            related_message=message,
            related_service_request=service_request,
            created_at=timezone.now()
        )
        
        return message

    @database_sync_to_async
    def has_prior_message_from_expert(self):
        """Vérifier si l'expert a déjà envoyé un message pour cette demande"""
        try:
            service_request = ServiceRequest.objects.get(id=self.request_id)
            
            # Vérifier s'il existe un message de l'expert au client pour cette demande
            return Message.objects.filter(
                sender=service_request.expert,
                recipient=service_request.client,
                service_request=service_request
            ).exists()
        except ServiceRequest.DoesNotExist:
            return False
