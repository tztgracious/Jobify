from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import AnonymousUser


def login_required_api(view_func):
    """
    Decorator for API views that requires user authentication.
    Returns 401 JSON response if user is not authenticated.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        return view_func(request, *args, **kwargs)
    return wrapped_view


def login_required_api_with_message(message="Authentication required"):
    """
    Decorator factory that allows custom error messages.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
