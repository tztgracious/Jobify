from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import User


class EmailBackend(BaseBackend):
    """
    Custom authentication backend for custom User model
    """
    
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        if email is None:
            email = username
            
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
