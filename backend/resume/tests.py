import os
import unittest
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

    def test_parse_resume_success(self):
        """Test that parse_resume endpoint returns deprecation message"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        response = self.client.post(self.url, {'file': pdf_file})

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['error'], 'API deprecated')
        self.assertTrue(response.data.get('deprecated', False))

    def test_parse_resume_no_file(self):
        """Test that parse_resume endpoint is deprecated"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'API deprecated')
        self.assertTrue(response.data.get('deprecated', False))

    @pytest.mark.skip(reason="Function not implemented")
    @unittest.skip("Empty file validation not yet implemented - external API accepts empty files")
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

    def test_parse_resume_invalid_file_type(self):
        """Test that parse_resume endpoint returns deprecation message"""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"This is a text file",
            content_type="text/plain"
        )

        response = self.client.post(self.url, {'file': txt_file})

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['error'], 'API deprecated')

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
    @unittest.skip("Test environment patching doesn't affect Django settings loaded at startup")
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


class UploadResumeTests(APITestCase):
    def setUp(self):
        self.url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from resume.models import Resume
        import os
        from django.conf import settings
        
        resumes = Resume.objects.all()
        for resume in resumes:
            file_path = os.path.join(settings.MEDIA_ROOT, resume.local_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        Resume.objects.all().delete()

    def test_upload_resume_success(self):
        """Test successful PDF upload"""
        from resume.models import Resume
        
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        response = self.client.post(self.url, {'file': pdf_file})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('doc_id', response.data)
        self.assertTrue(response.data['valid_file'])
        self.assertIsNone(response.data['error_msg'])
        
        # Verify database record was created
        doc_id = response.data['doc_id']
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.local_path, f"resumes/{doc_id}.pdf")

    def test_upload_resume_no_file(self):
        """Test upload without providing a file"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(response.data['doc_id'])
        self.assertFalse(response.data['valid_file'])
        self.assertEqual(response.data['error_msg'], 'No file uploaded')

    def test_upload_resume_invalid_file_type(self):
        """Test upload with non-PDF file"""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"This is a text file",
            content_type="text/plain"
        )

        response = self.client.post(self.url, {'file': txt_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(response.data['doc_id'])
        self.assertFalse(response.data['valid_file'])
        self.assertEqual(response.data['error_msg'], 'Not a PDF file.')

    def test_upload_resume_large_file(self):
        """Test upload with file exceeding size limit"""
        # Create a large file (over 5MB)
        large_content = self.valid_pdf_content * 100000  # Much larger than 5MB
        large_file = SimpleUploadedFile(
            "large_resume.pdf",
            large_content,
            content_type="application/pdf"
        )

        response = self.client.post(self.url, {'file': large_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(response.data['doc_id'])
        self.assertFalse(response.data['valid_file'])
        self.assertEqual(response.data['error_msg'], 'File too big.')
