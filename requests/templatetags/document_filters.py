from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='display_type')
def display_type(obj):
    """
    Custom filter to correctly display the document type
    """
    if hasattr(obj, 'get_type_display'):
        return obj.get_type_display()
    return ""

@register.filter(name='document_type_name')
def document_type_name(doc_type):
    """
    Convert document type code to readable name
    """
    document_types = {
        'identity': 'Identité',
        'proof': 'Justificatif',
        'contract': 'Contrat',
        'invoice': 'Facture',
        'report': 'Rapport',
        'other': 'Autre'
    }
    return document_types.get(doc_type, "")
