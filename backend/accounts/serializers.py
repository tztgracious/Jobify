from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'is_employer']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Use create_user which handles password hashing automatically
        return User.objects.create_user(**validated_data)
