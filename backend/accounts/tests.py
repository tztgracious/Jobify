from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class SignupTests(APITestCase):
    def test_signup_success(self):
        url = reverse('signup')
        valid_signup_data = {
            "email": "test@example.com",
            "password": "supersecure123",
            "full_name": "Test User",
            "is_employer": False
        }
        expected_status = status.HTTP_201_CREATED
        expected_response_key = "message"

        response = self.client.post(url, valid_signup_data, format='json')
        self.assertEqual(response.status_code, expected_status)
        self.assertIn(expected_response_key, response.data)

    def test_double_signing(self):
        url = reverse('signup')
        valid_signup_data = {
            "email": "test@example.com",
            "password": "supersecure123",
            "full_name": "Test User",
            "is_employer": False
        }

        # First signup - should succeed
        response = self.client.post(url, valid_signup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)

        # Second signup with same email - should fail
        response = self.client.post(url, valid_signup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)  # Error should be about the email field

        # Verify the error message indicates email already exists
        self.assertIn("already exists", str(response.data["email"]).lower())


class LoginTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.user_data = {
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
            "is_employer": False
        }
        self.client.post(self.signup_url, self.user_data, format='json')

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            "email": "login@example.com",
            "password": "password123"
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)

    def test_login_user_not_found(self):
        """Test login attempt with email that doesn't exist in the database"""
        nonexistent_user_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword123"
        }

        response = self.client.post(self.login_url, nonexistent_user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # The get_object_or_404 function returns a 404 response when user is not found

    def test_login_incorrect_password(self):
        """Test login attempt with the correct email but wrong password"""
        # create a user

        User.objects.create(
            email="testuser@example.com",
            password=make_password("correctpassword123"),
            full_name="Test User"
        )

        # try to log in with the wrong password
        response = self.client.post(self.login_url, {
            "email": "testuser@example.com",
            "password": "wrongpassword123"  # Incorrect password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Invalid credentials")
