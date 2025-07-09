from rest_framework import serializers
from .models import User

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password_hash', 'full_name', 'is_employer']
        extra_kwargs = {'password_hash': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create(**validated_data)
