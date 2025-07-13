from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import AnonymousUser
import warnings


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


def deprecated_api(message="This API endpoint is deprecated", new_endpoint=None):
    """
    Decorator for marking API endpoints as deprecated.
    Returns a deprecation warning in the response and optionally suggests a new endpoint.
    
    Args:
        message: Custom deprecation message
        new_endpoint: Optional new endpoint to suggest to users
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Log deprecation warning for developers
            full_message = message
            if new_endpoint:
                full_message += f" Please use {new_endpoint} instead."
            
            warnings.warn(full_message, DeprecationWarning, stacklevel=2)
            
            # Return error response indicating deprecation
            return Response({
                'error': 'API deprecated',
                'message': full_message,
                'deprecated': True
            }, status=status.HTTP_410_GONE)
        return wrapped_view
    return decorator


def deprecated_api_with_fallback(message="This API endpoint is deprecated", new_endpoint=None):
    """
    Decorator for deprecated APIs that still executes the original function but adds deprecation warnings.
    Useful for gradual deprecation where you want to warn users but still provide functionality.
    
    Args:
        message: Custom deprecation message
        new_endpoint: Optional new endpoint to suggest to users
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Log deprecation warning
            full_message = message
            if new_endpoint:
                full_message += f" Please use {new_endpoint} instead."
            
            warnings.warn(full_message, DeprecationWarning, stacklevel=2)
            
            # Execute the original function
            response = view_func(request, *args, **kwargs)
            
            # Add deprecation headers to the response
            if hasattr(response, 'headers'):
                response.headers['X-Deprecated'] = 'true'
                response.headers['X-Deprecated-Message'] = full_message
            
            return response
        return wrapped_view
    return decorator
