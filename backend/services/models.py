from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from accounts.models import Expert

class ServiceCategory(models.Model):
    """Model for service categories (Tourism, Administrative, etc.)"""
    name = models.CharField(_('name'), max_length=50)
    name_fr = models.CharField(_('name (French)'), max_length=50, null=True, blank=True)
    name_ar = models.CharField(_('name (Arabic)'), max_length=50, null=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    description_fr = models.TextField(_('description (French)'), blank=True, null=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True, null=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('service category')
        verbose_name_plural = _('service categories')
        ordering = ['name']

class ServiceType(models.Model):
    """Model for service types within categories"""
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='service_types')
    name = models.CharField(_('name'), max_length=50)
    name_fr = models.CharField(_('name (French)'), max_length=50, null=True, blank=True)
    name_ar = models.CharField(_('name (Arabic)'), max_length=50, null=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    description_fr = models.TextField(_('description (French)'), blank=True, null=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    class Meta:
        verbose_name = _('service type')
        verbose_name_plural = _('service types')
        ordering = ['category', 'name']

class Service(models.Model):
    """Base service model"""
    SERVICE_STATUS_CHOICES = (
        ('active', _('Active')),
        ('pending', _('Pending')),
        ('archived', _('Archived')),
    )
    
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    duration = models.DurationField(_('duration'), null=True, blank=True)
    expert = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    status = models.CharField(_('status'), max_length=20, choices=SERVICE_STATUS_CHOICES, default='active')
    is_active = models.BooleanField(_('is active'), default=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')
        ordering = ['-created_at']

class TourismService(Service):
    """Tourism-specific service model"""
    location = models.CharField(_('location'), max_length=100)
    includes_transport = models.BooleanField(_('includes transport'), default=False)
    includes_accommodation = models.BooleanField(_('includes accommodation'), default=False)
    includes_meals = models.BooleanField(_('includes meals'), default=False)
    group_size = models.IntegerField(_('max group size'), default=1)
    
    class Meta:
        verbose_name = _('tourism service')
        verbose_name_plural = _('tourism services')

class AdministrativeService(Service):
    """Administrative service model"""
    document_type = models.CharField(_('document type'), max_length=100)
    processing_time = models.DurationField(_('processing time'))
    requirements = models.TextField(_('requirements'))
    
    class Meta:
        verbose_name = _('administrative service')
        verbose_name_plural = _('administrative services')

class InvestmentService(Service):
    """Investment service model"""
    investment_type = models.CharField(_('investment type'), max_length=100)
    min_investment = models.DecimalField(_('minimum investment'), max_digits=12, decimal_places=2)
    expected_return = models.CharField(_('expected return'), max_length=100, blank=True)
    risk_level = models.CharField(_('risk level'), max_length=50)
    
    class Meta:
        verbose_name = _('investment service')
        verbose_name_plural = _('investment services')

class RealEstateService(Service):
    """Real estate service model"""
    property_type = models.CharField(_('property type'), max_length=100)
    location = models.CharField(_('location'), max_length=100)
    area = models.DecimalField(_('area (sqm)'), max_digits=10, decimal_places=2, null=True, blank=True)
    bedrooms = models.PositiveIntegerField(_('bedrooms'), null=True, blank=True)
    bathrooms = models.PositiveIntegerField(_('bathrooms'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('real estate service')
        verbose_name_plural = _('real estate services')

class FiscalService(Service):
    """Fiscal service model"""
    tax_type = models.CharField(_('tax type'), max_length=100)
    jurisdiction = models.CharField(_('jurisdiction'), max_length=100)
    applicable_law = models.CharField(_('applicable law'), max_length=200, blank=True)
    
    class Meta:
        verbose_name = _('fiscal service')
        verbose_name_plural = _('fiscal services')
