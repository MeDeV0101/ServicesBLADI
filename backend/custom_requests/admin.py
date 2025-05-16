from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ServiceRequest, RendezVous, Document, Message, Notification

class DocumentInline(admin.TabularInline):
    """Inline for documents associated with requests"""
    model = Document
    extra = 1
    fields = ('name', 'file', 'type', 'is_official', 'uploaded_by')
    readonly_fields = ('uploaded_by',)

class MessageInline(admin.TabularInline):
    """Inline for messages associated with requests"""
    model = Message
    extra = 0
    fields = ('sender', 'recipient', 'content', 'sent_at', 'is_read')
    readonly_fields = ('sent_at',)

class ServiceRequestAdmin(admin.ModelAdmin):
    """Admin configuration for ServiceRequest model"""
    list_display = ('title', 'client_name', 'service_name', 'created_at', 'status', 'priority', 'assigned_expert_name')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'client__user__name', 'client__user__first_name', 'service__title')
    inlines = [DocumentInline, MessageInline]
    date_hierarchy = 'created_at'
    
    def client_name(self, obj):
        return f"{obj.client.user.name} {obj.client.user.first_name}"
    client_name.short_description = _('Client')
    
    def service_name(self, obj):
        return obj.service.title
    service_name.short_description = _('Service')
    
    def assigned_expert_name(self, obj):
        if obj.expert:
            return f"{obj.expert.user.name} {obj.expert.user.first_name}"
        return _('Not assigned')
    assigned_expert_name.short_description = _('Assigned Expert')

class RendezVousAdmin(admin.ModelAdmin):
    """Admin configuration for RendezVous model"""
    list_display = ('client_name', 'expert_name', 'date_time', 'duration', 'consultation_type', 'status')
    list_filter = ('status', 'consultation_type', 'date_time')
    search_fields = ('client__user__name', 'client__user__first_name', 'expert__user__name', 'expert__user__first_name')
    date_hierarchy = 'date_time'
    
    def client_name(self, obj):
        return f"{obj.client.user.name} {obj.client.user.first_name}"
    client_name.short_description = _('Client')
    
    def expert_name(self, obj):
        return f"{obj.expert.user.name} {obj.expert.user.first_name}"
    expert_name.short_description = _('Expert')

class DocumentAdmin(admin.ModelAdmin):
    """Admin configuration for Document model"""
    list_display = ('name', 'type', 'uploaded_by_name', 'is_official', 'upload_date')
    list_filter = ('type', 'is_official', 'upload_date')
    search_fields = ('name', 'reference_number', 'uploaded_by__name', 'uploaded_by__first_name')
    date_hierarchy = 'upload_date'
    
    def uploaded_by_name(self, obj):
        return f"{obj.uploaded_by.name} {obj.uploaded_by.first_name}"
    uploaded_by_name.short_description = _('Uploaded by')

class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model"""
    list_display = ('sender_name', 'recipient_name', 'short_content', 'sent_at', 'is_read')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('content', 'sender__name', 'sender__first_name', 'recipient__name', 'recipient__first_name')
    date_hierarchy = 'sent_at'
    
    def sender_name(self, obj):
        return f"{obj.sender.name} {obj.sender.first_name}"
    sender_name.short_description = _('Sender')
    
    def recipient_name(self, obj):
        return f"{obj.recipient.name} {obj.recipient.first_name}"
    recipient_name.short_description = _('Recipient')
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = _('Content')

class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model"""
    list_display = ('title', 'user_name', 'type', 'created_at', 'is_read')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'content', 'user__name', 'user__first_name')
    date_hierarchy = 'created_at'
    
    def user_name(self, obj):
        return f"{obj.user.name} {obj.user.first_name}"
    user_name.short_description = _('User')

# Register models with their admin configurations
admin.site.register(ServiceRequest, ServiceRequestAdmin)
admin.site.register(RendezVous, RendezVousAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Notification, NotificationAdmin)
