import os
from unittest.mock import patch, MagicMock

import pytest
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ParseResumeTests(APITestCase):
    def setUp(self):
        self.url = reverse('parse-resume')  # Adjust URL name based on your urls.py
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_success(self):
        """Test successful PDF parsing"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        mock_response_data = {
            "text": "John Doe\nSoftware Engineer\n5 years experience",
            "pages": 1
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': pdf_file})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('parsed', response.data)
            self.assertEqual(response.data['parsed'], mock_response_data)

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_no_file(self):
        """Test parsing without uploading a file"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'No file uploaded')

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_empty_file(self):
        """Test parsing with an empty file"""
        empty_file = SimpleUploadedFile(
            "empty.pdf",
            b'',
            content_type="application/pdf"
        )

        response = self.client.post(self.url, {'file': empty_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, f"{response.json()}")
        self.assertIn('error', response.data)

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_invalid_file_type(self):
        """Test parsing with a non-PDF file"""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"This is a text file",
            content_type="text/plain"
        )

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.RequestException("Invalid file type")
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': txt_file})

            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertIn('error', response.data)

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_large_file(self):
        """Test parsing with large PDF file"""
        large_pdf_content = self.valid_pdf_content * 1000  # Simulate large file
        large_pdf_file = SimpleUploadedFile(
            "large_resume.pdf",
            large_pdf_content,
            content_type="application/pdf"
        )

        mock_response_data = {
            "text": "Large resume content",
            "pages": 10
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': large_pdf_file})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('parsed', response.data)

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_api_error(self):
        """Test handling of external API errors"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.RequestException("API Error")
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': pdf_file})

            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertIn('error', response.data)
            self.assertEqual(response.data['error'], 'API Error')

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_api_timeout(self):
        """Test handling of API timeout"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.Timeout("Request timeout")

            response = self.client.post(self.url, {'file': pdf_file})

            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertIn('error', response.data)

    @patch.dict(os.environ, {'LLAMA_PARSE_API_KEY': 'test_api_key'})
    @pytest.mark.skip(reason="Temporarily disabled for refactoring")
    def test_parse_resume_api_key_usage(self):
        """Test that the API key is properly used in requests"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"text": "Test content"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': pdf_file})

            # Verify the API was called with correct headers
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn('headers', call_args.kwargs)
            self.assertEqual(
                call_args.kwargs['headers']['Authorization'],
                'Bearer test_api_key'
            )

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_file_name_preservation(self):
        """Test that the original filename is preserved in the request"""
        original_filename = "john_doe_resume.pdf"
        pdf_file = SimpleUploadedFile(
            original_filename,
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"text": "Test content"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': pdf_file})

            # Verify the filename was passed correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn('files', call_args.kwargs)
            files_data = call_args.kwargs['files']
            self.assertEqual(files_data['file'][0], original_filename)

    @pytest.mark.skip(reason="Function not implemented")
    def test_parse_resume_content_type_validation(self):
        """Test that content type is properly handled"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"text": "Test content"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.post(self.url, {'file': pdf_file})

            # Verify content type was passed correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            files_data = call_args.kwargs['files']
            self.assertEqual(files_data['file'][2], "application/pdf")
