from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Service, TourismService, AdministrativeService, 
    InvestmentService, RealEstateService, FiscalService,
    ServiceCategory, ServiceType
)

class ServiceAdmin(admin.ModelAdmin):
    """Admin configuration for Service model"""
    list_display = ('title', 'service_type', 'is_active', 'created_at', 'price')
    list_filter = ('service_type', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {
            'fields': ('service_type', 'title', 'description')
        }),
        (_('Availability'), {
            'fields': ('is_active', 'price', 'duration', 'expert')
        }),
    )

class TourismServiceAdmin(admin.ModelAdmin):
    """Admin configuration for TourismService model"""
    list_display = ('get_title', 'location', 'includes_transport', 'includes_accommodation', 'group_size')
    list_filter = ('location', 'includes_accommodation', 'includes_transport')
    search_fields = ('service_ptr__title', 'location')
    
    def get_title(self, obj):
        return obj.title
    get_title.short_description = _('Title')
    get_title.admin_order_field = 'service_ptr__title'

class AdministrativeServiceAdmin(admin.ModelAdmin):
    """Admin configuration for AdministrativeService model"""
    list_display = ('get_title', 'document_type', 'processing_time')
    list_filter = ('document_type',)
    search_fields = ('service_ptr__title', 'document_type', 'requirements')
    
    def get_title(self, obj):
        return obj.title
    get_title.short_description = _('Title')
    get_title.admin_order_field = 'service_ptr__title'

class InvestmentServiceAdmin(admin.ModelAdmin):
    """Admin configuration for InvestmentService model"""
    list_display = ('get_title', 'investment_type', 'min_investment', 'risk_level')
    list_filter = ('investment_type', 'risk_level')
    search_fields = ('service_ptr__title', 'investment_type')
    
    def get_title(self, obj):
        return obj.title
    get_title.short_description = _('Title')
    get_title.admin_order_field = 'service_ptr__title'

class RealEstateServiceAdmin(admin.ModelAdmin):
    """Admin configuration for RealEstateService model"""
    list_display = ('get_title', 'property_type', 'location', 'area')
    list_filter = ('property_type', 'location')
    search_fields = ('service_ptr__title', 'property_type', 'location')
    
    def get_title(self, obj):
        return obj.title
    get_title.short_description = _('Title')
    get_title.admin_order_field = 'service_ptr__title'

class FiscalServiceAdmin(admin.ModelAdmin):
    """Admin configuration for FiscalService model"""
    list_display = ('get_title', 'tax_type', 'jurisdiction')
    list_filter = ('tax_type', 'jurisdiction')
    search_fields = ('service_ptr__title', 'tax_type')
    
    def get_title(self, obj):
        return obj.title
    get_title.short_description = _('Title')
    get_title.admin_order_field = 'service_ptr__title'

class ServiceCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ServiceCategory model"""
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

class ServiceTypeAdmin(admin.ModelAdmin):
    """Admin configuration for ServiceType model"""
    list_display = ('name', 'category', 'price')
    list_filter = ('category',)
    search_fields = ('name', 'description')

# Register models with their admin configurations
admin.site.register(Service, ServiceAdmin)
admin.site.register(TourismService, TourismServiceAdmin)
admin.site.register(AdministrativeService, AdministrativeServiceAdmin)
admin.site.register(InvestmentService, InvestmentServiceAdmin)
admin.site.register(RealEstateService, RealEstateServiceAdmin)
admin.site.register(FiscalService, FiscalServiceAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(ServiceType, ServiceTypeAdmin)
