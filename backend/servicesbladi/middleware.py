from django.contrib import messages

class MessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Code to be executed for each request before
        the view (and later middleware) are called.
        """
        # Process the request
        response = self.get_response(request)

        # Clear error messages from login and registration pages
        # to prevent them from persisting inappropriately
        if request.path in ['/login/', '/register/']:
            storage = messages.get_messages(request)
            # Mark existing messages as used so they're cleared
            for message in storage:
                pass
        
        return response
