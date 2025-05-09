from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Utilisateur
from services.models import Service

DOCUMENT_TYPES = (
    ('identity', _('Identity Document')),
    ('proof', _('Proof of Address')),
    ('contract', _('Contract')),
    ('invoice', _('Invoice')),
    ('report', _('Report')),
    ('other', _('Other')),
)

class ServiceRequest(models.Model):
    """Model for service requests from clients"""
    STATUS_CHOICES = (
        ('new', _('New')),
        ('pending_info', _('Pending Information')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('rejected', _('Rejected')),
    )
    
    PRIORITY_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    )
    
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='client_requests')
    expert = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='expert_requests')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='service_requests')
    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(_('priority'), max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    desired_date = models.DateField(_('desired date'), null=True, blank=True)
    is_urgent = models.BooleanField(_('is urgent'), default=False)
    
    def __str__(self):
        return f"{self.title} - {self.client.name} {self.client.first_name}"
    
    class Meta:
        verbose_name = _('service request')
        verbose_name_plural = _('service requests')
        ordering = ['-created_at']

class RendezVous(models.Model):
    """Model for appointments between clients and experts"""
    STATUS_CHOICES = (
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
        ('missed', _('Missed')),
    )
    
    CONSULTATION_TYPES = (
        ('in_person', _('In Person')),
        ('video', _('Video Call')),
        ('phone', _('Phone Call')),
    )
    
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='client_rendezvous')
    expert = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='expert_rendezvous')
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='rendezvous')
    date_time = models.DateTimeField(_('date and time'))
    duration = models.IntegerField(_('duration in minutes'), default=60)
    consultation_type = models.CharField(_('consultation type'), max_length=20, choices=CONSULTATION_TYPES, default='in_person')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    def __str__(self):
        return f"Rendez-vous for {self.client.name} with {self.expert.name} on {self.date_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = _('rendez-vous')
        verbose_name_plural = _('rendez-vous')
        ordering = ['date_time']

class Document(models.Model):
    """Model for documents attached to service requests"""
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    rendez_vous = models.ForeignKey(RendezVous, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    uploaded_by = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='uploaded_documents')
    type = models.CharField(_('document type'), max_length=20, choices=DOCUMENT_TYPES, default='other')
    is_official = models.BooleanField(_('is official document'), default=False)
    reference_number = models.CharField(_('reference number'), max_length=100, blank=True)
    name = models.CharField(_('name'), max_length=255)
    file = models.FileField(_('file'), upload_to='documents/%Y/%m/')
    mime_type = models.CharField(_('MIME type'), max_length=100, blank=True)
    file_size = models.IntegerField(_('file size in KB'), blank=True, null=True)
    upload_date = models.DateTimeField(_('upload date'), auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        ordering = ['-upload_date']

class Message(models.Model):
    """Message model for communications"""
    sender = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(_('content'))
    sent_at = models.DateTimeField(_('sent at'), auto_now_add=True)
    is_read = models.BooleanField(_('is read'), default=False)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)
    demande = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    
    def __str__(self):
        return f"From {self.sender.name} to {self.recipient.name} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['sent_at']

class Notification(models.Model):
    """Notification model"""
    NOTIFICATION_TYPES = (
        ('request_update', _('Request Update')),
        ('appointment', _('Appointment')),
        ('message', _('Message')),
        ('document', _('Document')),
        ('system', _('System')),
    )
    
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='request_notifications')
    type = models.CharField(_('notification type'), max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(_('title'), max_length=255)
    content = models.TextField(_('content'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_read = models.BooleanField(_('is read'), default=False)
    related_demande = models.ForeignKey(ServiceRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_rendez_vous = models.ForeignKey(RendezVous, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    def __str__(self):
        return f"{self.title} for {self.user.name} {self.user.first_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
