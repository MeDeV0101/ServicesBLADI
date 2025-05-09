from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur, Client, Expert, Admin

class UtilisateurAdmin(UserAdmin):
    """Admin configuration for Utilisateur model"""
    list_display = ('email', 'name', 'first_name', 'account_type', 'is_verified', 'is_active')
    list_filter = ('account_type', 'is_verified', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'first_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'first_name', 'phone', 'birth_date')}),
        (_('Location'), {'fields': ('residence_country',)}),
        (_('Preferences'), {'fields': ('preferred_languages',)}),
        (_('Account'), {'fields': ('account_type', 'is_verified', 'registration_date')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'first_name', 'account_type'),
        }),
    )

class ClientAdmin(admin.ModelAdmin):
    """Admin configuration for Client model"""
    list_display = ('get_name', 'get_email', 'mre_status', 'origin_country')
    list_filter = ('mre_status', 'origin_country')
    search_fields = ('user__name', 'user__first_name', 'user__email')
    
    def get_name(self, obj):
        return f"{obj.user.name} {obj.user.first_name}"
    get_name.short_description = _('Name')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('Email')

class ExpertAdmin(admin.ModelAdmin):
    """Admin configuration for Expert model"""
    list_display = ('get_name', 'get_email', 'specialty', 'hourly_rate')
    list_filter = ('specialty',)
    search_fields = ('user__name', 'user__first_name', 'user__email', 'specialty')
    
    def get_name(self, obj):
        return f"{obj.user.name} {obj.user.first_name}"
    get_name.short_description = _('Name')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('Email')

class AdminModelAdmin(admin.ModelAdmin):
    """Admin configuration for Admin model"""
    list_display = ('get_name', 'get_email', 'level', 'last_login')
    list_filter = ('level',)
    search_fields = ('user__name', 'user__first_name', 'user__email')
    
    def get_name(self, obj):
        return f"{obj.user.name} {obj.user.first_name}"
    get_name.short_description = _('Name')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('Email')

# Register models with their admin configurations
admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Expert, ExpertAdmin)
admin.site.register(Admin, AdminModelAdmin)
