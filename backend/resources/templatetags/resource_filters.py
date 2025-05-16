from django import template
from django.utils.safestring import mark_safe
from resources.models import Resource

register = template.Library()

@register.filter(name='filter_by_category')
def filter_by_category(resources, category):
    """
    Filter resources by their category
    """
    return resources.filter(category=category)

@register.filter(name='display_category')
def display_category(obj):
    """
    Display the category in a user-friendly format
    """
    if hasattr(obj, 'get_category_display'):
        return obj.get_category_display()
    return ""

@register.filter(name='display_format')
def display_format(obj):
    """
    Display the resource format in a user-friendly format
    """
    if hasattr(obj, 'get_format_type_display'):
        return obj.get_format_type_display()
    return ""
