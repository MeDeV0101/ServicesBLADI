from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.db.models import F
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Resource, ResourceFile, ResourceLink
from accounts.models import Client


@login_required
def client_resources_view(request):
    """Display resources for clients"""
    # Filter active resources
    resources = Resource.objects.filter(is_active=True).order_by('category', '-created_at')
    
    # Filter by category if specified
    category = request.GET.get('category')
    if category:
        resources = resources.filter(category=category)
    
    # Search filter
    search = request.GET.get('search')
    if search:
        resources = resources.filter(title__icontains=search) | resources.filter(description__icontains=search)
    
    context = {
        'resources': resources,
        'selected_category': category,
        'search': search,
    }
    
    return render(request, 'client/ressources.html', context)


@login_required
def client_download_resource_view(request, resource_file_id):
    """Download a resource file for a client"""
    resource_file = get_object_or_404(ResourceFile, id=resource_file_id)
    
    # Check if resource is active
    if not resource_file.resource.is_active:
        messages.error(request, _('This resource is not available.'))
        return redirect('resources:client_resources')
    
    # Increment download count
    Resource.objects.filter(id=resource_file.resource.id).update(download_count=F('download_count') + 1)
    
    # Return the file as a response
    return FileResponse(
        resource_file.file, 
        as_attachment=True, 
        filename=resource_file.file.name.split('/')[-1]
    )
