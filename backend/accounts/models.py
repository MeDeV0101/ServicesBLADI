from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import json

class UserManager(BaseUserManager):
    """Custom user manager for Utilisateur model"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('account_type', 'admin')
        extra_fields.setdefault('is_verified', True)
        
        return self.create_user(email, password, **extra_fields)

class Utilisateur(AbstractUser):
    """Custom user model for ServicesBLADI"""
    ACCOUNT_TYPES = (
        ('client', _('Client')),
        ('expert', _('Expert')),
        ('admin', _('Admin')),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(_('name'), max_length=100)
    first_name = models.CharField(_('first name'), max_length=100)
    phone = models.CharField(_('phone'), max_length=20, blank=True, null=True)
    birth_date = models.DateField(_('birth date'), blank=True, null=True)
    residence_country = models.CharField(_('residence country'), max_length=100, blank=True)
    preferred_languages = models.CharField(_('preferred languages'), max_length=100, default='fr')
    is_verified = models.BooleanField(_('is verified'), default=False)
    registration_date = models.DateTimeField(_('registration date'), auto_now_add=True)
    account_type = models.CharField(_('account type'), max_length=20, choices=ACCOUNT_TYPES, default='client')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'first_name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.name} {self.first_name} ({self.email})"
    
    def get_preferred_languages_list(self):
        """Return a list of preferred languages"""
        return self.preferred_languages.split(',')
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class Client(models.Model):
    """Client profile model"""
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='client_profile')
    mre_status = models.BooleanField(_('MRE status'), default=True)
    origin_country = models.CharField(_('origin country'), max_length=100, default='Maroc')
    last_visit = models.DateField(_('last visit to Morocco'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.name} {self.user.first_name} - Client"

class Expert(models.Model):
    """Expert profile model"""
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='expert_profile')
    specialty = models.CharField(_('specialty'), max_length=100)
    competencies = models.TextField(_('competencies'), blank=True)
    spoken_languages = models.CharField(_('spoken languages'), max_length=100, default='fr')
    biography = models.TextField(_('biography'), blank=True)
    hourly_rate = models.DecimalField(_('hourly rate'), max_digits=10, decimal_places=2, default=0)
    years_of_experience = models.IntegerField(_('years of experience'), default=0)
    availability = models.TextField(_('availability'), blank=True)
    
    def __str__(self):
        return f"{self.user.name} {self.user.first_name} - Expert ({self.specialty})"
    
    def get_spoken_languages_list(self):
        """Return a list of spoken languages"""
        return self.spoken_languages.split(',')
    
    def get_competencies_list(self):
        """Return a list of competencies"""
        try:
            return json.loads(self.competencies)
        except:
            return []

class Admin(models.Model):
    """Admin profile model"""
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='admin_profile')
    level = models.IntegerField(_('admin level'), default=1)
    access_rights = models.TextField(_('access rights'), blank=True)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.name} {self.user.first_name} - Admin (Level {self.level})"
    
    def get_access_rights_list(self):
        """Return a list of access rights"""
        try:
            return json.loads(self.access_rights)
        except:
            return []

class Address(models.Model):
    """Address model for users"""
    ADDRESS_TYPES = (
        ('HOME', _('Home')),
        ('WORK', _('Work')),
        ('OTHER', _('Other')),
    )
    
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(_('address type'), max_length=10, choices=ADDRESS_TYPES, default='HOME')
    street = models.CharField(_('street'), max_length=100)
    city = models.CharField(_('city'), max_length=50)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=50)
    is_default = models.BooleanField(_('is default'), default=False)
    
    def __str__(self):
        return f"{self.user.name} {self.user.first_name} - {self.get_address_type_display()} Address"
    
    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')

class Notification(models.Model):
    """Notification model for users"""
    NOTIFICATION_TYPES = (
        ('INFO', _('Information')),
        ('WARNING', _('Warning')),
        ('SUCCESS', _('Success')),
        ('ERROR', _('Error')),
    )
    
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(_('title'), max_length=100)
    message = models.TextField(_('message'))
    notification_type = models.CharField(_('type'), max_length=10, choices=NOTIFICATION_TYPES, default='INFO')
    is_read = models.BooleanField(_('is read'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.title}"
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
