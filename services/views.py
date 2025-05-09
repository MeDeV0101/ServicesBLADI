from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import ServiceCategory, ServiceType, Service, TourismService, AdministrativeService
from .models import InvestmentService, RealEstateService, FiscalService
from accounts.models import Expert, Utilisateur

def all_services_view(request):
    """View for the main services page showing all categories"""
    categories = ServiceCategory.objects.all()
    
    # If no categories exist yet, create default ones
    if not categories.exists():
        categories = create_default_categories()
    
    featured_services = Service.objects.filter(
        is_active=True
    ).select_related('expert', 'expert__user', 'service_type')[:6]
    
    context = {
        'categories': categories,
        'featured_services': featured_services,
        'page_title': 'Our Services'
    }
    
    return render(request, 'frontend/template/index.html', context)

def create_default_categories():
    """Helper function to create default service categories"""
    categories = [
        {
            'name': 'Tourism',
            'name_fr': 'Tourisme',
            'name_ar': 'سياحة',
            'description': 'Explore Morocco through our guided tours and experiences',
            'description_fr': 'Explorez le Maroc à travers nos visites guidées et expériences',
            'description_ar': 'اكتشف المغرب من خلال جولاتنا وتجاربنا المصحوبة بمرشدين',
            'slug': 'tourism',
            'icon': 'bi bi-globe'
        },
        {
            'name': 'Administrative',
            'name_fr': 'Administratif',
            'name_ar': 'إداري',
            'description': 'Administrative procedures and document processing services',
            'description_fr': 'Procédures administratives et services de traitement de documents',
            'description_ar': 'الإجراءات الإدارية وخدمات معالجة المستندات',
            'slug': 'administrative',
            'icon': 'bi bi-file-earmark-text'
        },
        {
            'name': 'Fiscal',
            'name_fr': 'Fiscal',
            'name_ar': 'ضريبي',
            'description': 'Tax planning and fiscal advisory services',
            'description_fr': 'Services de planification fiscale et de conseil',
            'description_ar': 'خدمات التخطيط الضريبي والاستشارات المالية',
            'slug': 'fiscal',
            'icon': 'bi bi-calculator'
        },
        {
            'name': 'Real Estate',
            'name_fr': 'Immobilier',
            'name_ar': 'عقارات',
            'description': 'Real estate consulting and property management services',
            'description_fr': "Services de conseil immobilier et de gestion de propriétés",
            'description_ar': 'خدمات استشارات العقارات وإدارة الممتلكات',
            'slug': 'real-estate',
            'icon': 'bi bi-house'
        },
        {
            'name': 'Investment',
            'name_fr': 'Investissement',
            'name_ar': 'استثمار',
            'description': 'Investment opportunities and financial advisory services',
            'description_fr': "Opportunités d'investissement et services de conseil financier",
            'description_ar': 'فرص الاستثمار وخدمات الاستشارات المالية',
            'slug': 'investment',
            'icon': 'bi bi-graph-up-arrow'
        },
    ]
    
    created_categories = []
    for cat_data in categories:
        category = ServiceCategory.objects.create(**cat_data)
        created_categories.append(category)
    
    return created_categories

def tourism_services_view(request):
    """View for tourism services"""
    tourism_services = TourismService.objects.filter(is_active=True)
    
    context = {
        'services': tourism_services,
        'title': 'Services Touristiques',
        'description': 'Découvrez nos services d\'accompagnement pour vos voyages au Maroc',
    }
    
    return render(request, 'Tourisme.html', context)

def administrative_services_view(request):
    """View for administrative services"""
    admin_services = AdministrativeService.objects.filter(is_active=True)
    
    context = {
        'services': admin_services,
        'title': 'Services Administratifs',
        'description': 'Simplifiez vos démarches administratives au Maroc',
    }
    
    return render(request, 'Administrative.html', context)

def fiscal_services_view(request):
    """View for fiscal services"""
    fiscal_services = FiscalService.objects.filter(is_active=True)
    
    context = {
        'services': fiscal_services,
        'title': 'Services Fiscaux',
        'description': 'Optimisez votre situation fiscale entre votre pays de résidence et le Maroc',
    }
    
    return render(request, 'Fiscale.html', context)

def real_estate_services_view(request):
    """View for real estate services"""
    real_estate_services = RealEstateService.objects.filter(is_active=True)
    
    context = {
        'services': real_estate_services,
        'title': 'Services Immobiliers',
        'description': 'Trouvez, achetez ou gérez votre bien immobilier au Maroc',
    }
    
    return render(request, 'Immobilier.html', context)

def investment_services_view(request):
    """View for investment services"""
    investment_services = InvestmentService.objects.filter(is_active=True)
    
    context = {
        'services': investment_services,
        'title': 'Services d\'Investissement',
        'description': 'Accompagnement dans vos projets d\'investissement au Maroc',
    }
    
    return render(request, 'Investisment.html', context)

def contact_view(request):
    """View for contact page and form handling"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')
        
        # Prepare email message
        full_message = f"Message from: {name}\nEmail: {email}\n\n{message_text}"
        
        try:
            # Send email
            send_mail(
                subject=f"ServicesBladi Contact: {subject}",
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SERVICESBLADI_CONTACT_EMAIL],
                fail_silently=False,
            )
            
            messages.success(request, 'Votre message a été envoyé avec succès. Nous vous contacterons bientôt.')
            return redirect('contact')
            
        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'envoi du message: {str(e)}')
    
    return render(request, 'contact.html')
