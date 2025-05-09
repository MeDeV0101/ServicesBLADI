def language_context(request):
    """
    Context processor that adds the current language code to the template context.
    This allows JavaScript to access the current language.
    """
    return {
        'LANGUAGE_CODE': request.LANGUAGE_CODE
    }