from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse
import os

from .models import Resource, ResourceFile, ResourceLink

# Expert resource management views
@login_required
def add_resource(request):
    """Add a new resource (for experts and admins)"""
    # Check if user is admin or expert
    if request.user.account_type.lower() not in ['admin', 'expert']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Vous n\'avez pas les permissions nécessaires.'})
        return redirect('home')
    
    # Debug info for all requests
    print(f"====== ADD RESOURCE DEBUG ======")
    print(f"User: {request.user.email}, Method: {request.method}")
    
    # Créer une ressource de test pour déboguer si aucune ressource n'existe
    resource_count = Resource.objects.count()
    print(f"Resource count in add_resource: {resource_count}")
    
    if resource_count == 0:
        try:
            # Créer une ressource de test
            test_resource = Resource.objects.create(
                title="Ressource de test",
                description="Ceci est une ressource de test créée automatiquement",
                category="guide",
                available_languages="fr",
                is_active=True,
                created_by=request.user,
                view_count=10
            )
            print(f"Ressource de test créée avec l'ID {test_resource.id}")
        except Exception as e:
            print(f"Erreur lors de la création de la ressource de test: {str(e)}")
            import traceback
            traceback.print_exc()
    
    if request.method == 'POST':
        # Debug info for POST data
        print("POST DATA:")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")
        
        print("FILES:")
        for key, value in request.FILES.items():
            print(f"  {key}: {value.name} ({value.size} bytes)")
        
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        languages = request.POST.getlist('languages')
        is_active = 'is_active' in request.POST
        
        # Validate required fields
        if not title or not description or not category:
            message = _('Please provide all required fields: title, description, and category.')
            print(f"Form validation failed - Title: {title}, Description: {bool(description)}, Category: {category}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': message})
            messages.error(request, message)
            return render(request, 'resources/resource_form.html')
        
        try:
            # Create resource
            resource = Resource.objects.create(
                title=title,
                description=description,
                category=category,
                available_languages=','.join(languages) if languages else '',
                is_active=is_active,
                created_by=request.user
            )
            
            print(f"Resource created with ID: {resource.id}, Title: {resource.title}")
            
            # Handle file uploads
            files = request.FILES.getlist('files')
            for file in files:
                ResourceFile.objects.create(
                    resource=resource,
                    file=file,
                    language='fr',  # Default language
                    file_format=file.name.split('.')[-1] if '.' in file.name else 'unknown',
                    file_size=file.size // 1024  # Convert bytes to KB
                )
                print(f"File added: {file.name}")
            
            # Handle links
            links = request.POST.getlist('links')
            link_titles = request.POST.getlist('link_titles')
            print(f"Links to add: {len([l for l in links if l])}")
            for i, link in enumerate(links):
                if link:
                    title = link_titles[i] if i < len(link_titles) and link_titles[i] else f"Link {i+1}"
                    ResourceLink.objects.create(
                        resource=resource,
                        url=link,
                        title=title,
                        language='fr'  # Default language
                    )
                    print(f"Link added: {link} with title: {title}")
            
            success_message = _('Resource added successfully!')
            print("Success! Redirecting to expert_ressources")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
            
            messages.success(request, success_message)
            return redirect('expert_ressources')
        except Exception as e:
            error_message = _(f'Error adding resource: {str(e)}')
            print(f"Error creating resource: {str(e)}")
            # Print full exception traceback
            import traceback
            traceback.print_exc()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message})
            
            messages.error(request, error_message)
            return render(request, 'resources/resource_form.html')
    
    # Render form
    print("Rendering form for GET request")
    return render(request, 'resources/resource_form.html')

@login_required
def edit_resource(request, resource_id):
    """Edit an existing resource (for creators, experts and admins)"""
    # Get resource
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user is admin, expert, or creator of resource
    if request.user.account_type.lower() not in ['admin', 'expert'] and resource.created_by != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Vous n\'avez pas les permissions nécessaires.'})
        return redirect('home')
    
    # Préparer les catégories pour le template
    resource_categories = Resource.CATEGORIES
    
    if request.method == 'POST':
        try:
            # Update resource data
            resource.title = request.POST.get('title', resource.title)
            resource.description = request.POST.get('description', resource.description)
            resource.category = request.POST.get('category', resource.category)
            
            available_languages = request.POST.getlist('languages')
            if available_languages:
                resource.available_languages = ','.join(available_languages)
            
            resource.is_active = 'is_active' in request.POST
            resource.save()
            
            print(f"Resource {resource_id} ({resource.title}) updated successfully")
            
            # Handle file uploads
            files = request.FILES.getlist('files')
            for file in files:
                extension = os.path.splitext(file.name)[1][1:].lower() if '.' in file.name else ''
                file_format = extension if extension else 'unknown'
                
                ResourceFile.objects.create(
                    resource=resource,
                    file=file,
                    language='fr',  # Default language
                    file_format=file_format,
                    file_size=file.size // 1024  # Convert bytes to KB
                )
                print(f"Added new file: {file.name}")
            
            # Handle file deletions
            for file in resource.files.all():
                if f'delete_file_{file.id}' in request.POST:
                    file_name = file.file.name
                    file.delete()
                    print(f"Deleted file: {file_name}")
            
            # Handle new links
            new_links = request.POST.getlist('new_links')
            new_link_titles = request.POST.getlist('new_link_titles')
            
            for i, link in enumerate(new_links):
                if link:
                    title = new_link_titles[i] if i < len(new_link_titles) and new_link_titles[i] else f"Link {i+1}"
                    ResourceLink.objects.create(
                        resource=resource,
                        url=link,
                        title=title,
                        language='fr'  # Default language
                    )
                    print(f"Added new link: {link} with title: {title}")
            
            # Handle existing links (edited or deleted)
            for link in resource.links.all():
                link_id = str(link.id)
                if f'delete_link_{link_id}' in request.POST:
                    link_url = link.url
                    link.delete()
                    print(f"Deleted link: {link_url}")
                elif f'edit_link_{link_id}' in request.POST:
                    new_url = request.POST.get(f'link_url_{link_id}')
                    new_title = request.POST.get(f'link_title_{link_id}')
                    if new_url:
                        link.url = new_url
                    if new_title:
                        link.title = new_title
                    link.save()
                    print(f"Updated link: {link.url} with title: {link.title}")
            
            success_message = _(f'La ressource "{resource.title}" a été mise à jour avec succès.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
                
            messages.success(request, success_message)
            return redirect('expert_ressources')
            
        except Exception as e:
            error_message = _(f'Erreur lors de la mise à jour de la ressource: {str(e)}')
            print(f"Error updating resource {resource_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message})
                
            messages.error(request, error_message)
    
    # Prepare data for form
    context = {
        'resource': resource,
        'files': resource.files.all(),
        'links': resource.links.all(),
        'resource_categories': resource_categories,
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Vous n\'avez pas les permissions nécessaires.'})
        return redirect('home')
    
    if request.method == 'POST' or request.method == 'GET':
        resource_title = resource.title
        
        try:
            # Soft delete or hard delete based on configuration
            if hasattr(resource, 'is_active'):
                resource.is_active = False
                resource.save()
                print(f"Resource {resource_id} ({resource_title}) soft-deleted (marked as inactive)")
            else:
                resource.delete()
                print(f"Resource {resource_id} ({resource_title}) hard-deleted from database")
            
            success_message = _(f'La ressource "{resource_title}" a été supprimée avec succès.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
            
            messages.success(request, success_message)
        except Exception as e:
            error_message = _(f'Erreur lors de la suppression de la ressource: {str(e)}')
            print(f"Error deleting resource {resource_id}: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message})
            
            messages.error(request, error_message)
    
    # Redirect to resources page for experts
    if request.user.account_type.lower() == 'expert':
        return redirect('expert_ressources')
    # Redirect to standard resources view for others
    return redirect('resources:resource_list')
