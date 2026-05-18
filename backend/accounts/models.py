from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model inheriting from AbstractUser to integrate with
    Django's authentication system.
    """
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    is_employer = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Standardize field names for AbstractUser compatibility
    # AbstractUser already has last_login and is_active

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Ensure username is set to email if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
