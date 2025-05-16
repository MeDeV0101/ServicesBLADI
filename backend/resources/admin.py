from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Resource, ResourceFile, ResourceLink, ConsulateEmbassy, FAQ

class ResourceFileInline(admin.TabularInline):
    """Inline for resource files"""
    model = ResourceFile
    extra = 1

class ResourceLinkInline(admin.TabularInline):
    """Inline for resource links"""
    model = ResourceLink
    extra = 1

class ResourceAdmin(admin.ModelAdmin):
    """Admin configuration for Resource model"""
    list_display = ('title', 'category', 'is_active', 'view_count', 'download_count', 'created_by_name')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ResourceFileInline, ResourceLinkInline]
    date_hierarchy = 'created_at'
    
    def created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.name} {obj.created_by.first_name}"
        return _('System')
    created_by_name.short_description = _('Created by')

class ConsulateEmbassyAdmin(admin.ModelAdmin):
    """Admin configuration for ConsulateEmbassy model"""
    list_display = ('entity_type_display', 'country', 'city', 'phone', 'email')
    list_filter = ('entity_type', 'country')
    search_fields = ('country', 'city', 'address', 'services')
    
    def entity_type_display(self, obj):
        return obj.get_entity_type_display()
    entity_type_display.short_description = _('Entity Type')
    entity_type_display.admin_order_field = 'entity_type'

class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for FAQ model"""
    list_display = ('question', 'category', 'language', 'is_active', 'order')
    list_filter = ('category', 'language', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')
    
    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'category')
        }),
        (_('Display Options'), {
            'fields': ('language', 'is_active', 'order')
        }),
    )

# Register models with their admin configurations
admin.site.register(Resource, ResourceAdmin)
admin.site.register(ConsulateEmbassy, ConsulateEmbassyAdmin)
admin.site.register(FAQ, FAQAdmin)
