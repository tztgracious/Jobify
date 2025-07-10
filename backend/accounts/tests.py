from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status

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
