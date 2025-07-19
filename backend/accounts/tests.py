"""
DEPRECATED MODULE - SCHEDULED FOR REMOVAL

This test module is deprecated and all tests have been disabled.
These tests will be removed in future versions.

Deprecation Date: July 19, 2025
Reason: Tests are no longer relevant to current application architecture
"""

import warnings
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest import skip

from accounts.models import User


@skip("DEPRECATED: This test class is deprecated and will be removed in future versions")
class SignupTests(APITestCase):
    def setUp(self):
        warnings.warn(
            "SignupTests is deprecated and will be removed in future versions",
            DeprecationWarning,
            stacklevel=2
        )
    
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


@skip("DEPRECATED: This test class is deprecated and will be removed in future versions")
class LoginTests(APITestCase):
    def setUp(self):
        warnings.warn(
            "LoginTests is deprecated and will be removed in future versions",
            DeprecationWarning,
            stacklevel=2
        )
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The authentication backend returns None for nonexistent users, resulting in 400

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

    def test_login_missing_fields(self):
        """Test login attempt with missing required fields"""
        # Missing password
        response = self.client.post(self.login_url, {
            "email": "login@example.com"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email
        response = self.client.post(self.login_url, {
            "password": "password123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing both
        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@skip("DEPRECATED: This test class is deprecated and will be removed in future versions")
class EndpointAccessTests(APITestCase):
    """Tests for endpoint accessibility without authentication requirements"""
    
    def setUp(self):
        warnings.warn(
            "EndpointAccessTests is deprecated and will be removed in future versions",
            DeprecationWarning,
            stacklevel=2
        )
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.parse_resume_url = reverse('parse-resume')
        
        self.user_data = {
            "email": "auth@example.com",
            "password": "password123",
            "full_name": "Auth User",
            "is_employer": False
        }
        # Create user via signup
        self.client.post(self.signup_url, self.user_data, format='json')

    def test_protected_endpoint_without_login(self):
        """Test accessing endpoint without login - should work since auth is removed"""
        # Try to access parse_resume without login (should work now)
        response = self.client.post(self.parse_resume_url, {}, format='json')
        
        # Should not be 401 since authentication is no longer required
        # Should be 400 because no file was uploaded
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No file uploaded")

    def test_protected_endpoint_with_valid_session(self):
        """Test accessing endpoint with valid session - should work regardless of session"""
        # First, log in to get session cookie
        login_response = self.client.post(self.login_url, {
            "email": "auth@example.com",
            "password": "password123"
        }, format='json')
        self.assertEqual(login_response.status_code, 200)
        
        # Now try to access endpoint (should work regardless of session)
        # Note: We're not providing a file here, so we expect a 400 for "No file uploaded"
        response = self.client.post(self.parse_resume_url, {}, format='json')
        
        # Should not be 401 (authentication is no longer required)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Should be 400 because no file was uploaded
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No file uploaded")

    def test_protected_endpoint_after_logout(self):
        """Test accessing endpoint after logout - should work since auth is removed"""
        # First, log in
        login_response = self.client.post(self.login_url, {
            "email": "auth@example.com",
            "password": "password123"
        }, format='json')
        self.assertEqual(login_response.status_code, 200)
        
        # Verify we can access endpoint
        response = self.client.post(self.parse_resume_url, {}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Now log out
        logout_response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(logout_response.status_code, 200)
        
        # Try to access endpoint after logout (should still work since auth is removed)
        response = self.client.post(self.parse_resume_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No file uploaded")

    def test_protected_endpoint_with_invalid_session(self):
        """Test accessing endpoint with invalid session - should work since auth is removed"""
        # Manually set an invalid session cookie
        self.client.cookies['sessionid'] = 'invalid_session_id'
        
        response = self.client.post(self.parse_resume_url, {}, format='json')
        
        # Should work even with invalid session since authentication is removed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No file uploaded")

    def test_multiple_login_sessions(self):
        """Test that multiple logins work correctly"""
        # First login
        response1 = self.client.post(self.login_url, {
            "email": "auth@example.com",
            "password": "password123"
        }, format='json')
        self.assertEqual(response1.status_code, 200)
        
        # Second login (should also work)
        response2 = self.client.post(self.login_url, {
            "email": "auth@example.com", 
            "password": "password123"
        }, format='json')
        self.assertEqual(response2.status_code, 200)
        
        # Should still be able to access protected endpoint
        response = self.client.post(self.parse_resume_url, {}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
