from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation
from django.db.models import Q, F

from .models import Resource, ResourceFile, ResourceLink, ConsulateEmbassy, FAQ

# Resource views
def resource_list_view(request):
    """Display list of available resources"""
    # Get current language
    current_language = translation.get_language()
    
    # Filter active resources
    resources = Resource.objects.filter(is_active=True)
    
    # Filter by category if specified
    category = request.GET.get('category')
    if category:
        resources = resources.filter(category=category)
    
    # Filter by language if specified, otherwise use current language
    language = request.GET.get('language', current_language)
    if language:
        resources = resources.filter(available_languages__contains=language)
    
    # Sort resources by category
    resources = resources.order_by('category', '-created_at')
    
    context = {
        'resources': resources,
        'category': category,
        'current_language': language,
    }
    
    return render(request, 'resources/resource_list.html', context)

def resource_detail_view(request, resource_id):
    """Display details of a specific resource"""
    resource = get_object_or_404(Resource, id=resource_id, is_active=True)
    
    # Increment view count
    Resource.objects.filter(id=resource_id).update(view_count=F('view_count') + 1)
    
    # Get resource files
    files = ResourceFile.objects.filter(resource=resource)
    
    # Get resource links
    links = ResourceLink.objects.filter(resource=resource)
    
    context = {
        'resource': resource,
        'files': files,
        'links': links,
    }
    
    return render(request, 'resources/resource_detail.html', context)

def resource_category_view(request, category):
    """Display resources filtered by category"""
    # Get current language
    current_language = translation.get_language()
    
    # Filter active resources by category
    resources = Resource.objects.filter(is_active=True, category=category)
    
    # Filter by language if specified, otherwise use current language
    language = request.GET.get('language', current_language)
    if language:
        resources = resources.filter(available_languages__contains=language)
    
    # Sort resources by creation date
    resources = resources.order_by('-created_at')
    
    context = {
        'resources': resources,
        'category': category,
        'current_language': language,
    }
    
    return render(request, 'resources/resource_category.html', context)

def download_resource_view(request, resource_file_id):
    """Download a resource file"""
    resource_file = get_object_or_404(ResourceFile, id=resource_file_id)
    
    # Increment download count for the resource
    Resource.objects.filter(id=resource_file.resource.id).update(download_count=F('download_count') + 1)
    
    # Return the file as a response
    return FileResponse(
        resource_file.file, 
        as_attachment=True, 
        filename=resource_file.file.name.split('/')[-1]
    )

# Expert resource management views
@login_required
def add_resource(request):
    """Add a new resource (for experts and admins)"""
    # Check if user is admin or expert
    if request.user.account_type.lower() not in ['admin', 'expert']:
        return redirect('home')
    
    if request.method == 'POST':
        # Extract resource data
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        available_languages = request.POST.getlist('languages')
        
        if not all([title, description, category]):
            return render(request, 'resources/add_resource.html', {
                'error': _('Please provide all required fields')
            })
        
        # Create resource
        resource = Resource.objects.create(
            title=title,
            description=description,
            category=category,
            created_by=request.user,
            available_languages=','.join(available_languages) if available_languages else 'fr',
            is_active=True
        )
        
        # Handle file uploads
        files = request.FILES.getlist('files')
        for file in files:
            ResourceFile.objects.create(
                resource=resource,
                file=file,
                file_name=file.name,
                file_size=file.size,
                uploaded_by=request.user
            )
        
        # Handle links
        links = request.POST.getlist('links')
        link_titles = request.POST.getlist('link_titles')
        for i, link in enumerate(links):
            if link:
                title = link_titles[i] if i < len(link_titles) and link_titles[i] else f"Link {i+1}"
                ResourceLink.objects.create(
                    resource=resource,
                    url=link,
                    title=title
                )
        
        return redirect('resources:resource_detail', resource_id=resource.id)
    
    # Render form
    return render(request, 'resources/add_resource.html')

@login_required
def edit_resource(request, resource_id):
    """Edit an existing resource (for creators, experts and admins)"""
    # Get resource
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user is admin, expert, or creator of resource
    if request.user.account_type.lower() not in ['admin', 'expert'] and resource.created_by != request.user:
        return redirect('home')
    
    if request.method == 'POST':
        # Update resource data
        resource.title = request.POST.get('title', resource.title)
        resource.description = request.POST.get('description', resource.description)
        resource.category = request.POST.get('category', resource.category)
        
        available_languages = request.POST.getlist('languages')
        if available_languages:
            resource.available_languages = ','.join(available_languages)
        
        resource.is_active = 'is_active' in request.POST
        resource.save()
        
        # Handle file uploads
        files = request.FILES.getlist('files')
        for file in files:
            ResourceFile.objects.create(
                resource=resource,
                file=file,
                file_name=file.name,
                file_size=file.size,
                uploaded_by=request.user
            )
        
        # Handle new links
        new_links = request.POST.getlist('new_links')
        new_link_titles = request.POST.getlist('new_link_titles')
        for i, link in enumerate(new_links):
            if link:
                title = new_link_titles[i] if i < len(new_link_titles) and new_link_titles[i] else f"Link {i+1}"
                ResourceLink.objects.create(
                    resource=resource,
                    url=link,
                    title=title
                )
        
        # Handle existing links (edited or deleted)
        for link in resource.links.all():
            link_id = str(link.id)
            if f'delete_link_{link_id}' in request.POST:
                link.delete()
            elif f'edit_link_{link_id}' in request.POST:
                new_url = request.POST.get(f'link_url_{link_id}')
                new_title = request.POST.get(f'link_title_{link_id}')
                if new_url:
                    link.url = new_url
                if new_title:
                    link.title = new_title
                link.save()
        
        # Handle file deletions
        for file in resource.files.all():
            if f'delete_file_{file.id}' in request.POST:
                file.delete()
        
        return redirect('resources:resource_detail', resource_id=resource.id)
    
    # Prepare data for form
    context = {
        'resource': resource,
        'files': resource.files.all(),
        'links': resource.links.all(),
        'available_languages': resource.available_languages.split(',') if resource.available_languages else []
    }
    
    return render(request, 'resources/edit_resource.html', context)

@login_required
def delete_resource(request, resource_id):
    """Delete a resource (for creators, experts and admins)"""
    # Get resource
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user is admin, expert, or creator of resource
    if request.user.account_type.lower() not in ['admin', 'expert'] and resource.created_by != request.user:
        return redirect('home')
    
    if request.method == 'POST':
        # Soft delete or hard delete based on configuration
        if hasattr(resource, 'is_active'):
            resource.is_active = False
            resource.save()
        else:
            resource.delete()
        
        return redirect('resources:resource_list')
    
    # Confirm deletion
    return render(request, 'resources/delete_resource.html', {'resource': resource})

# Embassy and consulate views
def embassy_list_view(request):
    """Display list of embassies and consulates"""
    # Filter by entity type if specified
    entity_type = request.GET.get('entity_type')
    if entity_type:
        embassies = ConsulateEmbassy.objects.filter(entity_type=entity_type)
    else:
        embassies = ConsulateEmbassy.objects.all()
    
    # Filter by country if specified
    country = request.GET.get('country')
    if country:
        embassies = embassies.filter(country=country)
    
    # Get list of unique countries for filtering
    countries = ConsulateEmbassy.objects.values_list('country', flat=True).distinct().order_by('country')
    
    # Sort by country and city
    embassies = embassies.order_by('country', 'city')
    
    context = {
        'embassies': embassies,
        'countries': countries,
        'entity_type': entity_type,
        'selected_country': country,
    }
    
    return render(request, 'resources/embassy_list.html', context)

def embassy_country_view(request, country):
    """Display embassies and consulates for a specific country"""
    embassies = ConsulateEmbassy.objects.filter(country=country).order_by('entity_type', 'city')
    
    context = {
        'embassies': embassies,
        'country': country,
    }
    
    return render(request, 'resources/embassy_country.html', context)

def embassy_detail_view(request, country, city):
    """Display details of a specific embassy or consulate"""
    # Use the first match if there are multiple entity types in the same location
    embassy = get_object_or_404(ConsulateEmbassy, country=country, city=city)
    
    # Check if there are other entities in the same location (e.g., embassy and consulate)
    related_entities = ConsulateEmbassy.objects.filter(country=country, city=city).exclude(id=embassy.id)
    
    context = {
        'embassy': embassy,
        'related_entities': related_entities,
    }
    
    return render(request, 'resources/embassy_detail.html', context)

# FAQ views
def faq_view(request):
    """Display frequently asked questions"""
    # Get current language
    current_language = translation.get_language()
    
    # Filter active FAQs in the current language
    faqs = FAQ.objects.filter(is_active=True, language=current_language)
    
    # Group by category
    categories = {}
    for faq in faqs:
        if faq.category not in categories:
            categories[faq.category] = []
        categories[faq.category].append(faq)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'resources/faq.html', context)

def faq_category_view(request, category):
    """Display FAQs for a specific category"""
    # Get current language
    current_language = translation.get_language()
    
    # Filter active FAQs in the current language and category
    faqs = FAQ.objects.filter(is_active=True, language=current_language, category=category).order_by('order', 'created_at')
    
    context = {
        'faqs': faqs,
        'category': category,
    }
    
    return render(request, 'resources/faq_category.html', context)

# API endpoints
@csrf_exempt
def api_resource_list(request):
    """API endpoint to list resources"""
    # Get current language
    current_language = translation.get_language()
    
    # Filter active resources
    resources = Resource.objects.filter(is_active=True)
    
    # Filter by category if specified
    category = request.GET.get('category')
    if category:
        resources = resources.filter(category=category)
    
    # Filter by language if specified, otherwise use current language
    language = request.GET.get('language', current_language)
    if language:
        resources = resources.filter(available_languages__contains=language)
    
    # Sort resources
    resources = resources.order_by('category', '-created_at')
    
    # Prepare response data
    resource_data = []
    for resource in resources:
        resource_data.append({
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'category': resource.category,
            'available_languages': resource.available_languages.split(',') if resource.available_languages else [],
            'available_formats': resource.available_formats,
            'view_count': resource.view_count,
            'download_count': resource.download_count,
        })
    
    return JsonResponse({
        'success': True,
        'resources': resource_data
    })

@csrf_exempt
def api_resource_detail(request, resource_id):
    """API endpoint to get resource details"""
    try:
        resource = Resource.objects.get(id=resource_id, is_active=True)
        
        # Increment view count
        resource.view_count += 1
        resource.save()
        
        # Get resource files
        files_data = []
        for file in ResourceFile.objects.filter(resource=resource):
            files_data.append({
                'id': file.id,
                'language': file.language,
                'file_format': file.file_format,
                'file_size': file.file_size,
                'download_url': f'/resources/download/{file.id}/'
            })
        
        # Get resource links
        links_data = []
        for link in ResourceLink.objects.filter(resource=resource):
            links_data.append({
                'id': link.id,
                'language': link.language,
                'url': link.url,
                'title': link.title or link.url
            })
        
        # Prepare response data
        resource_data = {
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'category': resource.category,
            'available_languages': resource.available_languages.split(',') if resource.available_languages else [],
            'available_formats': resource.available_formats,
            'view_count': resource.view_count,
            'download_count': resource.download_count,
            'created_at': resource.created_at.isoformat(),
            'files': files_data,
            'links': links_data,
        }
        
        return JsonResponse({
            'success': True,
            'resource': resource_data
        })
        
    except Resource.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Resource not found')
        }, status=404)

@csrf_exempt
def api_embassy_list(request):
    """API endpoint to list embassies and consulates"""
    # Filter by entity type if specified
    entity_type = request.GET.get('entity_type')
    query = {}
    if entity_type:
        query['entity_type'] = entity_type
    
    # Filter by country if specified
    country = request.GET.get('country')
    if country:
        query['country'] = country
    
    # Get embassies and consulates
    embassies = ConsulateEmbassy.objects.filter(**query).order_by('country', 'city')
    
    # Prepare response data
    embassy_data = []
    for embassy in embassies:
        embassy_data.append({
            'id': embassy.id,
            'country': embassy.country,
            'city': embassy.city,
            'entity_type': embassy.entity_type,
            'entity_type_display': embassy.get_entity_type_display(),
            'address': embassy.address,
            'phone': embassy.phone,
            'email': embassy.email,
            'website': embassy.website,
            'latitude': embassy.latitude,
            'longitude': embassy.longitude,
        })
    
    # Get list of unique countries
    countries = list(ConsulateEmbassy.objects.values_list('country', flat=True).distinct().order_by('country'))
    
    return JsonResponse({
        'success': True,
        'embassies': embassy_data,
        'countries': countries
    })

@csrf_exempt
def api_embassy_country(request, country):
    """API endpoint to get embassies and consulates for a specific country"""
    embassies = ConsulateEmbassy.objects.filter(country=country).order_by('entity_type', 'city')
    
    # Prepare response data
    embassy_data = []
    for embassy in embassies:
        embassy_data.append({
            'id': embassy.id,
            'country': embassy.country,
            'city': embassy.city,
            'entity_type': embassy.entity_type,
            'entity_type_display': embassy.get_entity_type_display(),
            'address': embassy.address,
            'phone': embassy.phone,
            'email': embassy.email,
            'website': embassy.website,
            'working_hours': embassy.working_hours,
            'services': embassy.services,
            'latitude': embassy.latitude,
            'longitude': embassy.longitude,
        })
    
    return JsonResponse({
        'success': True,
        'country': country,
        'embassies': embassy_data
    })

@csrf_exempt
def api_faq_list(request):
    """API endpoint to list FAQs"""
    # Get current language
    current_language = translation.get_language()
    
    # Filter active FAQs in the specified language
    language = request.GET.get('language', current_language)
    faqs = FAQ.objects.filter(is_active=True, language=language)
    
    # Filter by category if specified
    category = request.GET.get('category')
    if category:
        faqs = faqs.filter(category=category)
    
    # Sort FAQs by order and creation date
    faqs = faqs.order_by('category', 'order', 'created_at')
    
    # Prepare response data
    faq_data = []
    for faq in faqs:
        faq_data.append({
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'category': faq.category,
            'language': faq.language,
        })
    
    # Group by category if requested
    group_by_category = request.GET.get('group_by_category') == 'true'
    if group_by_category:
        category_data = {}
        for faq in faq_data:
            if faq['category'] not in category_data:
                category_data[faq['category']] = []
            category_data[faq['category']].append(faq)
        
        return JsonResponse({
            'success': True,
            'categories': category_data
        })
    else:
        return JsonResponse({
            'success': True,
            'faqs': faq_data
        })
