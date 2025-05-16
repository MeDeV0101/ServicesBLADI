from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
import csv
import os
from io import StringIO
from django.http import HttpResponse
from django.utils.translation import gettext as _

from accounts.models import Utilisateur, Client, Expert, Address
from accounts.forms import UserEditForm
from custom_requests.models import ServiceRequest, Document, RendezVous, Message, Notification
from services.models import Service, ServiceCategory
from resources.models import Resource

@login_required
def admin_requests_view(request):
    """View to display all service requests for admin with filtering and search capabilities"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        category_filter = request.GET.get('category', '')
        period_filter = request.GET.get('period', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        service_requests = ServiceRequest.objects.select_related(
            'client', 
            'expert',
            'service'
        )
        
        # Apply filters
        if status_filter:
            service_requests = service_requests.filter(status=status_filter)
            
        if category_filter:
            service_requests = service_requests.filter(service__category=category_filter)
            
        if period_filter:
            today = timezone.now().date()
            if period_filter == 'today':
                service_requests = service_requests.filter(created_at__date=today)
            elif period_filter == 'week':
                week_ago = today - timedelta(days=7)
                service_requests = service_requests.filter(created_at__date__gte=week_ago)
            elif period_filter == 'month':
                month_ago = today - timedelta(days=30)
                service_requests = service_requests.filter(created_at__date__gte=month_ago)
                
        if search_query:
            service_requests = service_requests.filter(
                Q(description__icontains=search_query) |
                Q(service__title__icontains=search_query) |
                Q(client__first_name__icontains=search_query) |
                Q(client__name__icontains=search_query) |
                Q(expert__first_name__icontains=search_query) |
                Q(expert__name__icontains=search_query)
            )
            
        # Order by creation date (newest first)
        service_requests = service_requests.order_by('-created_at')
        
        # Get statistics for dashboard
        total_requests = service_requests.count()
        pending_requests = service_requests.filter(status='pending').count()
        in_progress_requests = service_requests.filter(status='in_progress').count()
        completed_requests = service_requests.filter(status='completed').count()
        
        # Get categories for filter
        categories = ServiceCategory.objects.all()
        
        # Get all experts for assignment
        experts = Utilisateur.objects.filter(account_type='expert')
        
        # Pagination
        paginator = Paginator(service_requests, 10)  # 10 requests per page
        page = request.GET.get('page')
        
        try:
            requests_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            requests_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            requests_page = paginator.page(paginator.num_pages)
        
        context = {
            'user': request.user,
            'service_requests': requests_page,  # Make sure this matches template variable
            'experts': experts,  # Add experts to context for assignment
            'categories': categories,
            'status_filter': status_filter,
            'category_filter': category_filter,
            'period_filter': period_filter,
            'search_query': search_query,
            # Variables directes pour le template
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'in_progress_requests': in_progress_requests,
            'completed_requests': completed_requests,
            # Garder la structure stats également
            'stats': {
                'total': total_requests,
                'pending': pending_requests,
                'in_progress': in_progress_requests,
                'completed': completed_requests
            }
        }
        
        return render(request, 'admin/demandes.html', context)
    
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/demandes.html', context)

@login_required
def admin_users_view(request):
    """View to display all users for admin with filtering and search capabilities"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get filter parameters
        user_type = request.GET.get('user_type', '')
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        users = Utilisateur.objects.all()
        
        # Apply filters
        if user_type:
            users = users.filter(account_type__iexact=user_type)
            
        if status_filter:
            if status_filter == 'active':
                users = users.filter(is_active=True)
            elif status_filter == 'inactive':
                users = users.filter(is_active=False)
                
        if search_query:
            users = users.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
            
        # Order by registration date
        users = users.order_by('-date_joined')
        
        # Debug logging
        print(f"ADMIN USERS VIEW - Query: {str(users.query)}")
        print(f"ADMIN USERS VIEW - Total users found: {users.count()}")
        
        # Get statistics for dashboard (before pagination)
        total_users = Utilisateur.objects.count()
        clients_count = Utilisateur.objects.filter(account_type__iexact='client').count()
        experts_count = Utilisateur.objects.filter(account_type__iexact='expert').count()
        admins_count = Utilisateur.objects.filter(account_type__iexact='admin').count()
        active_users = Utilisateur.objects.filter(is_active=True).count()
        inactive_users = Utilisateur.objects.filter(is_active=False).count()
        
        # Get recent users (last 7 days)
        one_week_ago = timezone.now() - timedelta(days=7)
        recent_users = Utilisateur.objects.filter(date_joined__gte=one_week_ago).count()
        
        # Pagination
        paginator = Paginator(users, 10)  # 10 users per page
        page = request.GET.get('page')
        
        try:
            users_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            users_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            users_page = paginator.page(paginator.num_pages)
        
        context = {
            'user': request.user,
            'users': users_page,  # Use users_page directly as 'users'
            'user_type': user_type,
            'status_filter': status_filter,
            'search_query': search_query,
            # Variables directes
            'total_users': total_users,
            'clients_count': clients_count,
            'experts_count': experts_count,
            'admins_count': admins_count,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'recent_users': recent_users,
            # Structure stats
            'stats': {
                'total': total_users,
                'clients': clients_count,
                'experts': experts_count,
                'admins': admins_count,
                'active': active_users,
                'inactive': inactive_users,
                'recent': recent_users
            }
        }
        
        return render(request, 'admin/users.html', context)
    
    except Exception as e:
        print(f"ADMIN USERS VIEW - Error: {str(e)}")
        import traceback
        print(f"ADMIN USERS VIEW - Traceback: {traceback.format_exc()}")
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/users.html', context)

@login_required
def admin_add_user(request):
    """View to handle adding new users by admin"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name', '')
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            password = request.POST.get('password', '')
            account_type = request.POST.get('account_type', 'client')
            is_active = request.POST.get('is_active') == 'on'
            
            # Check if user with this email already exists
            if Utilisateur.objects.filter(email=email).exists():
                messages.error(request, f"Un utilisateur avec l'email {email} existe déjà.")
                return redirect('admin_users')
            
            # Create user
            user = Utilisateur.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                name=name,
                phone=phone,
                account_type=account_type,
                is_active=is_active
            )
            
            # Create related profile based on account type
            if account_type == 'client':
                Client.objects.create(user=user)
            elif account_type == 'expert':
                Expert.objects.create(user=user)
            
            messages.success(request, f"L'utilisateur {first_name} {name} a été créé avec succès.")
            return redirect('admin_users')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return redirect('admin_users')
    
    # If GET request, redirect to users page
    return redirect('admin_users')

@login_required
def admin_toggle_user_status(request, user_id):
    """Toggle user's active status"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        user = get_object_or_404(Utilisateur, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_message = "activé" if user.is_active else "désactivé"
        messages.success(request, f"L'utilisateur {user.first_name} {user.name} a été {status_message}.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_active': user.is_active,
                'message': f"L'utilisateur {user.first_name} {user.name} a été {status_message}."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    return redirect('admin_users')

@login_required
def admin_delete_user(request, user_id):
    """Delete user from the system"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        user = get_object_or_404(Utilisateur, id=user_id)
        user_name = f"{user.first_name} {user.name}"
        user.delete()
        
        messages.success(request, f"L'utilisateur {user_name} a été supprimé avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"L'utilisateur {user_name} a été supprimé avec succès."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors de la suppression: {str(e)}"
            })
    
    return redirect('admin_users')

@login_required
def admin_edit_user(request, user_id):
    """Edit user details"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    
    # Get profile based on account type
    client_profile = None
    expert_profile = None
    
    if user.account_type.lower() == 'client':
        try:
            client_profile = Client.objects.get(user=user)
        except Client.DoesNotExist:
            pass
    elif user.account_type.lower() == 'expert':
        try:
            expert_profile = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            pass
    
    if request.method == 'POST':
        try:
            # Get form data for user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.name = request.POST.get('name', user.name)
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.is_active = request.POST.get('is_active') == 'on'
            
            # Check if password should be updated
            new_password = request.POST.get('password', '')
            if new_password:
                user.set_password(new_password)
            
            user.save()
            
            # Update profile data if available
            if user.account_type.lower() == 'client' and client_profile:
                client_profile.mre_status = request.POST.get('mre_status') == 'on'
                client_profile.origin_country = request.POST.get('origin_country', client_profile.origin_country)
                
                last_visit = request.POST.get('last_visit', '')
                if last_visit:
                    client_profile.last_visit = last_visit
                
                client_profile.save()
                
            elif user.account_type.lower() == 'expert' and expert_profile:
                expert_profile.specialty = request.POST.get('specialty', expert_profile.specialty)
                expert_profile.spoken_languages = request.POST.get('spoken_languages', expert_profile.spoken_languages)
                expert_profile.years_of_experience = request.POST.get('years_of_experience', expert_profile.years_of_experience)
                expert_profile.hourly_rate = request.POST.get('hourly_rate', expert_profile.hourly_rate)
                expert_profile.biography = request.POST.get('biography', expert_profile.biography)
                expert_profile.competencies = request.POST.get('competencies', expert_profile.competencies)
                
                expert_profile.save()
            
            messages.success(request, f"Les informations de l'utilisateur {user.first_name} {user.name} ont été mises à jour.")
            return redirect('admin_user_detail', user_id=user.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}")
            return render(request, 'admin/edit_user.html', {
                'user': request.user,
                'target_user': user,
                'client_profile': client_profile,
                'expert_profile': expert_profile,
                'error': str(e)
            })
    
    # For GET request, render the form
    return render(request, 'admin/edit_user.html', {
        'user': request.user,
        'target_user': user,
        'client_profile': client_profile,
        'expert_profile': expert_profile
    })

@login_required
def admin_verify_document(request, document_id):
    """Mark a document as verified"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        document = get_object_or_404(Document, id=document_id)
        document.status = 'verified'
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        messages.success(request, f"Le document '{document.name}' a été vérifié avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Le document '{document.name}' a été vérifié avec succès."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    return redirect('admin_documents')

@login_required
def admin_reject_document(request, document_id):
    """Mark a document as rejected"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        document = get_object_or_404(Document, id=document_id)
        document.status = 'rejected'
        document.verified_by = request.user
        document.verified_at = timezone.now()
        rejection_reason = request.POST.get('rejection_reason', '')
        document.rejection_reason = rejection_reason
        document.save()
        
        messages.success(request, f"Le document '{document.name}' a été refusé.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Le document '{document.name}' a été refusé."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    return redirect('admin_documents')

@login_required
def admin_delete_document(request, document_id):
    """Delete a document"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        document = get_object_or_404(Document, id=document_id)
        document_name = document.name
        document.delete()
        
        messages.success(request, f"Le document '{document_name}' a été supprimé avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Le document '{document_name}' a été supprimé avec succès."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors de la suppression: {str(e)}"
            })
    
    return redirect('admin_documents')

@login_required
def admin_complete_appointment(request, appointment_id):
    """Mark an appointment as completed"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        appointment = get_object_or_404(RendezVous, id=appointment_id)
        appointment.status = 'completed'
        appointment.save()
        
        messages.success(request, f"Le rendez-vous a été marqué comme complété.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Le rendez-vous a été marqué comme complété."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    return redirect('admin_rendezvous')

@login_required
def admin_cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        appointment = get_object_or_404(RendezVous, id=appointment_id)
        appointment.status = 'cancelled'
        cancellation_reason = request.POST.get('cancellation_reason', '')
        appointment.notes = f"Annulé par l'administrateur. Raison: {cancellation_reason}"
        appointment.save()
        
        messages.success(request, f"Le rendez-vous a été annulé.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Le rendez-vous a été annulé."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    return redirect('admin_rendezvous')

@login_required
def admin_reschedule_appointment(request, appointment_id):
    """Reschedule an appointment"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_rendezvous')
    
    try:
        appointment = get_object_or_404(RendezVous, id=appointment_id)
        
        # Get new date and time from POST data
        new_date = request.POST.get('date', '')
        new_time = request.POST.get('time', '')
        
        if not new_date or not new_time:
            messages.error(request, "La date et l'heure doivent être spécifiées.")
            return redirect('admin_rendezvous')
        
        # Update the appointment
        appointment.date = datetime.strptime(new_date, '%Y-%m-%d').date()
        appointment.time = new_time
        appointment.save()
        
        # Notify client and expert about the rescheduling
        # This could be implemented with a notification system
        
        messages.success(request, f"Le rendez-vous a été replanifié pour le {new_date} à {new_time}.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Le rendez-vous a été replanifié pour le {new_date} à {new_time}."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur lors de la replanification: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors de la replanification: {str(e)}"
            })
    
    return redirect('admin_rendezvous')

@login_required
def admin_add_resource(request):
    """Add a new resource"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_ressources')
    
    try:
        # Get form data
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        category = request.POST.get('category', '')
        is_public = request.POST.get('is_public') == 'on'
        
        if not title or not description or not category:
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect('admin_ressources')
            
        # Create new resource
        resource = Resource(
            title=title,
            description=description,
            category=category,
            is_public=is_public,
            created_by=request.user
        )
        
        # Handle file upload if present
        if 'file' in request.FILES:
            resource.file = request.FILES['file']
            
        # Handle thumbnail upload if present
        if 'thumbnail' in request.FILES:
            resource.thumbnail = request.FILES['thumbnail']
            
        resource.save()
        
        messages.success(request, f"La ressource '{title}' a été ajoutée avec succès.")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'ajout de la ressource: {str(e)}")
    
    return redirect('admin_ressources')

@login_required
def admin_edit_resource(request, resource_id):
    """Edit an existing resource"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_ressources')
    
    try:
        resource = get_object_or_404(Resource, id=resource_id)
        
        # Update resource data
        resource.title = request.POST.get('title', resource.title)
        resource.description = request.POST.get('description', resource.description)
        resource.category = request.POST.get('category', resource.category)
        resource.is_public = request.POST.get('is_public') == 'on'
        
        # Handle file upload if present
        if 'file' in request.FILES:
            resource.file = request.FILES['file']
            
        # Handle thumbnail upload if present
        if 'thumbnail' in request.FILES:
            resource.thumbnail = request.FILES['thumbnail']
            
        resource.save()
        
        messages.success(request, f"La ressource '{resource.title}' a été mise à jour avec succès.")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la mise à jour de la ressource: {str(e)}")
    
    return redirect('admin_ressources')

@login_required
def admin_delete_resource(request, resource_id):
    """Delete a resource"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        resource = get_object_or_404(Resource, id=resource_id)
        resource_title = resource.title
        resource.delete()
        
        messages.success(request, f"La ressource '{resource_title}' a été supprimée avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"La ressource '{resource_title}' a été supprimée avec succès."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors de la suppression: {str(e)}"
            })
    
    return redirect('admin_ressources')

@login_required
def admin_toggle_resource_visibility(request, resource_id):
    """Toggle resource visibility (public/private)"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        resource = get_object_or_404(Resource, id=resource_id)
        resource.is_public = not resource.is_public
        resource.save()
        
        visibility_status = "publique" if resource.is_public else "privée"
        messages.success(request, f"La ressource '{resource.title}' est maintenant {visibility_status}.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_public': resource.is_public,
                'message': f"La ressource '{resource.title}' est maintenant {visibility_status}."
            })
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    return redirect('admin_ressources')

@login_required
def admin_resources_view(request):
    """View to display all resources for admin with filtering and search capabilities"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get filter parameters
        category = request.GET.get('category', '')
        visibility = request.GET.get('visibility', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        resources = Resource.objects.all()
        
        # Apply filters
        if category:
            resources = resources.filter(category=category)
            
        if visibility:
            is_public = visibility == 'public'
            resources = resources.filter(is_public=is_public)
                
        if search_query:
            resources = resources.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__icontains=search_query)
            )
            
        # Order by newest first
        resources = resources.order_by('-created_at')
        
        # Get statistics for dashboard
        total_resources = resources.count()
        public_resources = resources.filter(is_public=True).count()
        private_resources = resources.filter(is_public=False).count()
        
        # Add missing variables
        document_count = resources.filter(file_type='document').count() if hasattr(Resource, 'file_type') else 0
        video_count = resources.filter(file_type='video').count() if hasattr(Resource, 'file_type') else 0
        popular_resources = resources.order_by('-downloads')[:5] if hasattr(Resource, 'downloads') else resources[:5]
        visibilities = ['public', 'private']  # Options pour le filtre de visibilité
        
        # Get categories for filters
        categories = Resource.objects.values_list('category', flat=True).distinct()
        
        # Pagination
        paginator = Paginator(resources, 12)  # 12 resources per page (better for grid)
        page = request.GET.get('page')
        
        try:
            resources_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            resources_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            resources_page = paginator.page(paginator.num_pages)
        
        context = {
            'user': request.user,
            'resources': resources_page,
            'categories': categories,
            'visibilities': visibilities,
            'category_filter': category,
            'visibility_filter': visibility,
            'search_query': search_query,
            # Variables directes
            'total_resources': total_resources,
            'public_resources': public_resources,
            'private_resources': private_resources,
            'document_count': document_count,
            'video_count': video_count,
            'popular_resources': popular_resources,
            # Structure stats
            'stats': {
                'total': total_resources,
                'public': public_resources,
                'private': private_resources,
                'documents': document_count,
                'videos': video_count
            }
        }
        
        return render(request, 'admin/ressources.html', context)
    
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/ressources.html', context)

@login_required
def admin_messages_view(request):
    """View to display all messages for admin with filtering and search capabilities"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        period_filter = request.GET.get('period', '')
        search_query = request.GET.get('search', '')
        
        # Add missing variables
        sender_id = request.GET.get('sender', '')
        recipient_id = request.GET.get('recipient', '')
        users = Utilisateur.objects.all()
        
        # Base queryset - get all messages
        messages_obj = Message.objects.select_related('sender', 'recipient', 'service_request')
        
        # Apply filters
        if status_filter:
            if status_filter == 'read':
                messages_obj = messages_obj.filter(is_read=True)
            elif status_filter == 'unread':
                messages_obj = messages_obj.filter(is_read=False)
                
        if period_filter:
            today = timezone.now().date()
            if period_filter == 'today':
                messages_obj = messages_obj.filter(sent_at__date=today)
            elif period_filter == 'week':
                start_of_week = today - timedelta(days=today.weekday())
                messages_obj = messages_obj.filter(sent_at__date__gte=start_of_week)
            elif period_filter == 'month':
                start_of_month = today.replace(day=1)
                messages_obj = messages_obj.filter(sent_at__date__gte=start_of_month)
                
        if search_query:
            messages_obj = messages_obj.filter(
                Q(content__icontains=search_query) |
                Q(sender__first_name__icontains=search_query) |
                Q(sender__name__icontains=search_query) |
                Q(recipient__first_name__icontains=search_query) |
                Q(recipient__name__icontains=search_query) |
                Q(service_request__title__icontains=search_query)
            )
            
        # Order by sent date (newest first)
        messages_obj = messages_obj.order_by('-sent_at')
        
        # Get statistics for dashboard
        total_messages = messages_obj.count()
        unread_messages = messages_obj.filter(is_read=False).count()
        today_messages = messages_obj.filter(sent_at__date=today).count()
        
        # Add missing variables
        admin_messages = messages_obj.filter(Q(sender__account_type='admin') | Q(recipient__account_type='admin')).count()
        recent_messages = messages_obj.filter(sent_at__gte=timezone.now() - timedelta(days=7)).count()
        
        # Pagination
        paginator = Paginator(messages_obj, 20)  # 20 messages per page
        page = request.GET.get('page')
        
        try:
            messages_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            messages_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            messages_page = paginator.page(paginator.num_pages)
        
        context = {
            'user': request.user,
            'messages_list': messages_page,  # Use 'messages_list' to match template expectation
            'users': users,
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'status_filter': status_filter,
            'search_query': search_query,
            # Variables directes
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'admin_messages': admin_messages,
            'recent_messages': recent_messages,
            # Structure stats
            'stats': {
                'total': total_messages,
                'unread': unread_messages,
                'admin': admin_messages
            }
        }
        
        return render(request, 'admin/messages.html', context)
    
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/messages.html', context)

@login_required
def admin_mark_message_read(request, message_id):
    """Mark a message as read"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        message = get_object_or_404(Message, id=message_id)
        message.is_read = True
        message.save()
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': "Message marqué comme lu."
            })
    
    except Exception as e:
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Erreur: {str(e)}"
            })
    
    # Redirect back to messages page if not AJAX
    return redirect('admin_messages')

@login_required
def admin_documents_view(request):
    """View to display all documents for admin with filtering and search capabilities"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        document_type = request.GET.get('type', '')
        client_id = request.GET.get('client', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset - correct the field names based on Document model
        documents = Document.objects.select_related('uploaded_by', 'service_request')
        
        # Apply filters
        if status_filter:
            documents = documents.filter(status=status_filter)
            
        if document_type:
            documents = documents.filter(type=document_type)
            
        if client_id:
            documents = documents.filter(uploaded_by__id=client_id)
                
        if search_query:
            documents = documents.filter(
                Q(name__icontains=search_query) |
                Q(type__icontains=search_query) |
                Q(uploaded_by__first_name__icontains=search_query) |
                Q(uploaded_by__name__icontains=search_query)
            )
            
        # Order by upload date (newest first)
        documents = documents.order_by('-uploaded_at')
        
        # Get statistics for dashboard
        total_documents = documents.count()
        verified_documents = documents.filter(status='verified').count()
        pending_documents = documents.filter(status='pending').count()
        rejected_documents = documents.filter(status='rejected').count()
        
        # Get document types for filters
        document_types = Document.objects.values_list('document_type', flat=True).distinct()
        
        # Get clients for filters
        clients = Client.objects.select_related('user').all()
        
        # Pagination
        paginator = Paginator(documents, 10)  # 10 documents per page
        page = request.GET.get('page')
        
        try:
            documents_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            documents_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            documents_page = paginator.page(paginator.num_pages)
        
        context = {
            'user': request.user,
            'documents': documents_page,
            'document_types': document_types,
            'clients': clients,
            'client_id': client_id,
            'document_type': document_type,
            'status_filter': status_filter,
            'search_query': search_query,
            # Variables directes
            'total_documents': total_documents,
            'verified_documents': verified_documents,
            'pending_documents': pending_documents,
            'rejected_documents': rejected_documents,
            # Structure stats
            'stats': {
                'total': total_documents,
                'verified': verified_documents,
                'pending': pending_documents,
                'rejected': rejected_documents
            }
        }
        
        return render(request, 'admin/documents.html', context)
    
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/documents.html', context)

@login_required
def admin_appointments_view(request):
    """View to display all appointments for admin with filtering and search capabilities"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date', '')
        client_id = request.GET.get('client', '')
        expert_id = request.GET.get('expert', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset avec les relations correctes
        appointments = RendezVous.objects.select_related(
            'client', 
            'expert', 
            'service_request'
        )
        
        # Apply filters
        if status_filter:
            appointments = appointments.filter(status=status_filter)
            
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                appointments = appointments.filter(date_time__date=today)
            elif date_filter == 'tomorrow':
                tomorrow = today + timedelta(days=1)
                appointments = appointments.filter(date_time__date=tomorrow)
            elif date_filter == 'week':
                week_later = today + timedelta(days=7)
                appointments = appointments.filter(date_time__date__gte=today, date_time__date__lte=week_later)
            
        if client_id:
            appointments = appointments.filter(client_id=client_id)
            
        if expert_id:
            appointments = appointments.filter(expert_id=expert_id)
                
        if search_query:
            appointments = appointments.filter(
                Q(client__first_name__icontains=search_query) |
                Q(client__name__icontains=search_query) |
                Q(expert__first_name__icontains=search_query) |
                Q(expert__name__icontains=search_query) |
                Q(service_request__service__title__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
            
        # Order by date and time
        appointments = appointments.order_by('date_time')
        
        # Get statistics for dashboard
        total_appointments = appointments.count()
        upcoming_appointments = appointments.filter(date_time__gte=timezone.now()).count()
        completed_appointments = appointments.filter(status='completed').count()
        cancelled_appointments = appointments.filter(status='cancelled').count()
        
        # Add missing variables
        today = timezone.now().date()
        today_appointments = appointments.filter(date_time__date=today).count()
        
        # Get clients and experts for filters
        clients = Client.objects.select_related('user').all()
        experts = Expert.objects.select_related('user').all()
        
        # Pagination
        paginator = Paginator(appointments, 10)  # 10 appointments per page
        page = request.GET.get('page')
        
        try:
            appointments_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            appointments_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            appointments_page = paginator.page(paginator.num_pages)
        
        context = {
            'user': request.user,
            'appointments': appointments_page,
            'experts': experts,
            'clients': clients,
            'expert_id': expert_id,
            'client_id': client_id,
            'status_filter': status_filter,
            'period_filter': date_filter,
            'search_query': search_query,
            # Variables directes
            'total_appointments': total_appointments,
            'upcoming_appointments': upcoming_appointments,
            'completed_appointments': completed_appointments,
            'cancelled_appointments': cancelled_appointments,
            'today_appointments': today_appointments,
            # Structure stats
            'stats': {
                'total': total_appointments,
                'upcoming': upcoming_appointments,
                'completed': completed_appointments,
                'cancelled': cancelled_appointments,
                'today': today_appointments
            }
        }
        
        return render(request, 'admin/rendezvous.html', context)
    
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/rendezvous.html', context)

@login_required
def admin_edit_profile_view(request):
    """View for admins to edit their profile information"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('admin_profile')  # Redirect to profile view after successful update
        else:
            messages.error(request, "Des erreurs ont été trouvées dans le formulaire. Veuillez les corriger.")
    else:
        user_form = UserEditForm(instance=request.user)
    
    context = {
        'user_form': user_form,
    }
    
    return render(request, 'admin/edit_profile.html', context)

@login_required
def admin_profile_view(request):
    """View for admins to see their profile information"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    # Fetch some statistics for the admin
    users_count = Utilisateur.objects.count()
    requests_count = ServiceRequest.objects.count()
    documents_count = Document.objects.count()
    
    context = {
        'users_count': users_count,
        'requests_count': requests_count,
        'documents_count': documents_count
    }
    
    return render(request, 'admin/profile.html', context)

@login_required
def admin_assign_expert(request, request_id):
    """Assign an expert to a service request"""
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    # Get the service request
    demande = get_object_or_404(ServiceRequest, id=request_id)
    
    if request.method == 'POST':
        expert_id = request.POST.get('expert_id')
        notes = request.POST.get('notes', '')
        
        if expert_id:
            # Get the expert user
            expert_user = get_object_or_404(Utilisateur, id=expert_id, account_type='expert')
            
            # Update the request
            demande.expert = expert_user
            demande.status = 'in_progress'  # Change status to in progress
            demande.save()
            
            # Notify the expert
            Notification.objects.create(
                user=expert_user,
                type='request_assignment',
                title=_('New Assignment'),
                content=_(f'You have been assigned to the request "{demande.title}" by {request.user.name} {request.user.first_name}.'),
                related_service_request=demande
            )
            
            # Also notify the client
            Notification.objects.create(
                user=demande.client,
                type='request_update',
                title=_('Expert Assigned'),
                content=_(f'An expert has been assigned to your request "{demande.title}".'),
                related_service_request=demande
            )
            
            # Add notes as a message if provided
            if notes:
                # From admin to expert
                Message.objects.create(
                    sender=request.user,
                    recipient=expert_user,
                    content=_('Admin notes: ') + notes,
                    service_request=demande
                )
            
            messages.success(request, _('Expert successfully assigned to the request.'))
        else:
            messages.error(request, _('Please select an expert to assign.'))
    
    return redirect('admin_demandes')

@login_required
def admin_update_request_status(request, request_id):
    """Update the status of a service request"""
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    # Get the service request
    demande = get_object_or_404(ServiceRequest, id=request_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if new_status in [s[0] for s in ServiceRequest.STATUS_CHOICES]:
            # Store the old status for notification
            old_status = demande.status
            
            # Update the request status
            demande.status = new_status
            demande.save()
            
            # Add comment as message if provided
            if comment:
                Message.objects.create(
                    sender=request.user,
                    recipient=demande.client,
                    content=_('Statut mis à jour: ') + comment,
                    service_request=demande
                )
                
                # If there's an expert assigned, send the message to them as well
                if demande.expert:
                    Message.objects.create(
                        sender=request.user,
                        recipient=demande.expert,
                        content=_('Statut mis à jour: ') + comment,
                        service_request=demande
                    )
            
            # Create notification for client
            status_translated = dict(ServiceRequest.STATUS_CHOICES).get(new_status, new_status)
            Notification.objects.create(
                user=demande.client,
                type='request_update',
                title=_('Statut de la demande mis à jour'),
                content=_(f'Le statut de votre demande "{demande.title}" a été mis à jour à "{status_translated}".'),
                related_service_request=demande
            )
            
            # Create notification for expert if assigned
            if demande.expert:
                Notification.objects.create(
                    user=demande.expert,
                    type='request_update',
                    title=_('Statut de la demande mis à jour'),
                    content=_(f'Le statut de la demande "{demande.title}" a été mis à jour à "{status_translated}".'),
                    related_service_request=demande
                )
            
            messages.success(request, _('Le statut de la demande a été mis à jour avec succès.'))
        else:
            messages.error(request, _('Le statut spécifié est invalide.'))
    
    return redirect('admin_demandes')

@login_required
def admin_request_detail(request, request_id):
    """View to display detailed information about a specific service request for admin"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get the service request with all related objects
        service_request = get_object_or_404(
            ServiceRequest.objects.select_related(
                'client__user',
                'expert__user',
                'service',
                'service__category'
            ),
            id=request_id
        )
        
        # Get documents related to this request
        documents = Document.objects.filter(service_request=service_request).order_by('-upload_date')
        
        # Get messages related to this request
        messages_list = Message.objects.filter(service_request=service_request).order_by('sent_at')
        
        # Get appointments related to this request
        appointments = RendezVous.objects.filter(service_request=service_request).order_by('date_time')
        
        # Get experts for potential assignment
        experts = Utilisateur.objects.filter(account_type='expert')
        
        context = {
            'user': request.user,
            'service_request': service_request,
            'documents': documents,
            'messages_list': messages_list,
            'appointments': appointments,
            'experts': experts
        }
        
        return render(request, 'admin/request_detail.html', context)
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('admin_demandes')

@login_required
def admin_send_message(request):
    """Handle sending a message from admin"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_messages')
    
    try:
        # Get form data
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        service_request_id = request.POST.get('service_request_id')
        
        if not recipient_id or not content:
            messages.error(request, "Recipient and content are required.")
            if service_request_id:
                return redirect('admin_request_detail', request_id=service_request_id)
            return redirect('admin_messages')
        
        # Get the recipient
        recipient = get_object_or_404(Utilisateur, id=recipient_id)
        
        # Get the service request if available
        service_request = None
        if service_request_id:
            service_request = get_object_or_404(ServiceRequest, id=service_request_id)
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content,
            service_request=service_request
        )
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('New Message'),
            content=_(f'You have received a new message from {request.user.first_name} {request.user.name}.'),
            related_message=message,
            related_service_request=service_request
        )
        
        messages.success(request, _('Message sent successfully.'))
        
        # Redirect back to appropriate page
        if service_request_id:
            return redirect('admin_request_detail', request_id=service_request_id)
        return redirect('admin_messages')
        
    except Exception as e:
        messages.error(request, f"Error sending message: {str(e)}")
        if service_request_id:
            return redirect('admin_request_detail', request_id=service_request_id)
        return redirect('admin_messages')

@login_required
def admin_user_detail(request, user_id):
    """View to display detailed information about a specific user for admin"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    try:
        # Get the user with all related objects
        user = get_object_or_404(Utilisateur, id=user_id)
        
        # Get additional information based on account type
        client_profile = None
        expert_profile = None
        
        if user.account_type.lower() == 'client':
            try:
                client_profile = Client.objects.get(user=user)
            except Client.DoesNotExist:
                pass
        elif user.account_type.lower() == 'expert':
            try:
                expert_profile = Expert.objects.get(user=user)
            except Expert.DoesNotExist:
                pass
        
        # Get service requests related to this user
        if user.account_type.lower() == 'client':
            service_requests = ServiceRequest.objects.filter(client=user).order_by('-created_at')
        elif user.account_type.lower() == 'expert':
            service_requests = ServiceRequest.objects.filter(expert=user).order_by('-created_at')
        else:
            service_requests = []
        
        # Get documents related to this user
        documents = Document.objects.filter(uploaded_by=user).order_by('-upload_date')
        
        # Get messages related to this user
        messages_list = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('-sent_at')
        
        # Get appointments related to this user
        if user.account_type.lower() == 'client':
            appointments = RendezVous.objects.filter(client=user).order_by('date_time')
        elif user.account_type.lower() == 'expert':
            appointments = RendezVous.objects.filter(expert=user).order_by('date_time')
        else:
            appointments = []
        
        context = {
            'user': request.user,
            'target_user': user,
            'client_profile': client_profile,
            'expert_profile': expert_profile,
            'service_requests': service_requests,
            'documents': documents,
            'messages_list': messages_list,
            'appointments': appointments
        }
        
        return render(request, 'admin/user_detail.html', context)
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('admin_users')
