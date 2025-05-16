from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Utilisateur

class Resource(models.Model):
    """Resource model for downloadable resources and information"""
    CATEGORIES = (
        ('administrative', _('Administrative')),
        ('fiscal', _('Fiscal')),
        ('tourism', _('Tourism')),
        ('investment', _('Investment')),
        ('real_estate', _('Real Estate')),
        ('legal', _('Legal')),
        ('social', _('Social')),
        ('embassy', _('Embassy/Consulate')),
        ('guide', _('Guide')),
        ('other', _('Other')),
    )
    
    FORMAT_TYPES = (
        ('pdf', 'PDF'),
        ('doc', 'DOC/DOCX'),
        ('xls', 'XLS/XLSX'),
        ('ppt', 'PPT/PPTX'),
        ('image', _('Image')),
        ('video', _('Video')),
        ('link', _('External Link')),
        ('text', _('Text')),
    )
    
    category = models.CharField(_('category'), max_length=20, choices=CATEGORIES)
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    available_languages = models.CharField(_('available languages'), max_length=100, default='fr')
    available_formats = models.CharField(_('available formats'), max_length=100, choices=FORMAT_TYPES, default='pdf')
    size_kb = models.IntegerField(_('size in KB'), blank=True, null=True)
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='created_resources')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('is active'), default=True)
    view_count = models.IntegerField(_('view count'), default=0)
    download_count = models.IntegerField(_('download count'), default=0)
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"
    
    def get_available_languages_list(self):
        """Return a list of available languages"""
        return self.available_languages.split(',')

class ResourceFile(models.Model):
    """Resource file model"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='files')
    language = models.CharField(_('language'), max_length=10)
    file = models.FileField(_('file'), upload_to='resources/%Y/%m/')
    file_format = models.CharField(_('file format'), max_length=20)
    file_size = models.IntegerField(_('file size in KB'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.resource.title} - {self.language} ({self.file_format})"

class ResourceLink(models.Model):
    """Resource link model for external resources"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='links')
    language = models.CharField(_('language'), max_length=10)
    url = models.URLField(_('URL'))
    title = models.CharField(_('title'), max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.resource.title} - {self.language} - {self.title or self.url}"

class ConsulateEmbassy(models.Model):
    """Consulate/Embassy information model"""
    ENTITY_TYPES = (
        ('embassy', _('Embassy')),
        ('consulate', _('Consulate')),
        ('honorary_consulate', _('Honorary Consulate')),
    )
    
    country = models.CharField(_('country'), max_length=100)
    city = models.CharField(_('city'), max_length=100)
    entity_type = models.CharField(_('entity type'), max_length=20, choices=ENTITY_TYPES)
    address = models.TextField(_('address'))
    phone = models.CharField(_('phone'), max_length=50, blank=True)
    email = models.EmailField(_('email'), blank=True)
    website = models.URLField(_('website'), blank=True)
    working_hours = models.TextField(_('working hours'), blank=True)
    services = models.TextField(_('services'), blank=True)
    latitude = models.FloatField(_('latitude'), blank=True, null=True)
    longitude = models.FloatField(_('longitude'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_entity_type_display()} of Morocco - {self.city}, {self.country}"
    
    class Meta:
        verbose_name = _('consulate/embassy')
        verbose_name_plural = _('consulates/embassies')
        unique_together = ('country', 'city', 'entity_type')

class FAQ(models.Model):
    """Frequently Asked Questions model"""
    CATEGORIES = (
        ('administrative', _('Administrative')),
        ('fiscal', _('Fiscal')),
        ('tourism', _('Tourism')),
        ('investment', _('Investment')),
        ('real_estate', _('Real Estate')),
        ('general', _('General')),
        ('account', _('Account')),
    )
    
    category = models.CharField(_('category'), max_length=20, choices=CATEGORIES, default='general')
    question = models.CharField(_('question'), max_length=255)
    answer = models.TextField(_('answer'))
    language = models.CharField(_('language'), max_length=10, default='fr')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('is active'), default=True)
    order = models.IntegerField(_('display order'), default=0)
    
    def __str__(self):
        return f"{self.question} ({self.language})"
    
    class Meta:
        ordering = ['category', 'order', 'created_at']
