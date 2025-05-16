from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from .models import Resource, ResourceFile, ResourceLink

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
        
        return redirect('expert_ressources_new')
    
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
        
        return redirect('expert_ressources_new')
    
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
        
        return redirect('expert_ressources_new')
    
    # Confirm deletion
    return render(request, 'resources/delete_resource.html', {'resource': resource})
