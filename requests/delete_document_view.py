@login_required
def delete_document_view(request, document_id):
    """Delete a document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Check permission to delete
    if request.user.account_type == 'client':        # Clients can only delete their own documents
        if document.uploaded_by != request.user and (
            not document.service_request or document.service_request.client != request.user):
            messages.error(request, _('You do not have permission to delete this document.'))
            return redirect('requests:documents')
    elif request.user.account_type == 'expert':
        # Experts can only delete their own documents
        if document.uploaded_by != request.user and (
            not document.service_request or document.service_request.expert != request.user):
            messages.error(request, _('You do not have permission to delete this document.'))
            return redirect('requests:documents')
    elif request.user.account_type != 'admin':
        messages.error(request, _('You do not have permission to delete this document.'))
        return redirect('requests:documents')
    
    # Delete the document
    document.delete()
    
    messages.success(request, _('Document successfully deleted.'))
    return redirect('requests:documents')
