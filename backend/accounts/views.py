from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSignupSerializer
from .models import User

class SignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import generics
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password_hash')

    user = get_object_or_404(User, email=email)
    if user.password_hash == password:
        return Response({"message": "Login successful"})
    return Response({"error": "Invalid credentials"}, status=400)
