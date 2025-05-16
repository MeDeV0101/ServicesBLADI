from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import Utilisateur

@login_required
def admin_bulk_toggle_users_status(request):
    """Toggle active status for multiple users at once"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_users')
    
    try:
        # Get list of selected user IDs from the form
        user_ids = request.POST.getlist('selected_users')
        action = request.POST.get('action')
        
        if not user_ids or not action:
            messages.error(request, "Veuillez sélectionner des utilisateurs et une action.")
            return redirect('admin_users')
            
        # Determine the target status based on the action
        if action == 'activate':
            is_active = True
            status_msg = "activés"
        elif action == 'deactivate':
            is_active = False
            status_msg = "désactivés"
        else:
            messages.error(request, "Action non valide.")
            return redirect('admin_users')
            
        # Update all selected users
        updated = Utilisateur.objects.filter(id__in=user_ids).update(is_active=is_active)
        
        messages.success(request, f"{updated} utilisateurs ont été {status_msg} avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"{updated} utilisateurs ont été {status_msg} avec succès."
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
def admin_bulk_delete_users(request):
    """Delete multiple users at once"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_users')
    
    try:
        # Get list of selected user IDs from the form
        user_ids = request.POST.getlist('selected_users')
        
        if not user_ids:
            messages.error(request, "Veuillez sélectionner des utilisateurs à supprimer.")
            return redirect('admin_users')
            
        # Get the count before deletion for messaging
        count = len(user_ids)
        
        # Delete users - this will cascade delete related objects
        Utilisateur.objects.filter(id__in=user_ids).delete()
        
        messages.success(request, f"{count} utilisateurs ont été supprimés avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"{count} utilisateurs ont été supprimés avec succès."
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
def admin_bulk_verify_documents(request):
    """Verify multiple documents at once"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_documents')
    
    try:
        # Get list of selected document IDs from the form
        from custom_requests.models import Document
        from django.utils import timezone
        
        document_ids = request.POST.getlist('selected_documents')
        
        if not document_ids:
            messages.error(request, "Veuillez sélectionner des documents à vérifier.")
            return redirect('admin_documents')
            
        # Update all selected documents
        updated = Document.objects.filter(id__in=document_ids).update(
            status='verified',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        
        messages.success(request, f"{updated} documents ont été vérifiés avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"{updated} documents ont été vérifiés avec succès."
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
def admin_bulk_reject_documents(request):
    """Reject multiple documents at once"""
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('admin_documents')
    
    try:
        # Get list of selected document IDs from the form
        from custom_requests.models import Document
        from django.utils import timezone
        
        document_ids = request.POST.getlist('selected_documents')
        rejection_reason = request.POST.get('rejection_reason', 'Rejeté par l\'administrateur')
        
        if not document_ids:
            messages.error(request, "Veuillez sélectionner des documents à rejeter.")
            return redirect('admin_documents')
            
        # Update all selected documents
        updated = Document.objects.filter(id__in=document_ids).update(
            status='rejected',
            verified_by=request.user,
            verified_at=timezone.now(),
            rejection_reason=rejection_reason
        )
        
        messages.success(request, f"{updated} documents ont été rejetés avec succès.")
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"{updated} documents ont été rejetés avec succès."
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
def generate_documents_report(request):
    """Generate a report of document uploads"""
    # Import Document model
    from custom_requests.models import Document
    
    # Get documents
    documents = Document.objects.all().order_by('-upload_date')

@login_required
def generate_experts_report(request):
    """Generate a report of experts"""
    # Import Document model
    from custom_requests.models import Document
    
    # Get all experts
