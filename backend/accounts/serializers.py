from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'is_employer']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # hash the password before saving
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)
