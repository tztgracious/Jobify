import os
import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from interview.models import InterviewSession


class UploadResumeTests(APITestCase):
    def setUp(self):
        self.url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from django.conf import settings

        sessions = InterviewSession.objects.all()
        for session in sessions:
            if session.resume_local_path:
                file_path = os.path.join(settings.MEDIA_ROOT, session.resume_local_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        InterviewSession.objects.all().delete()

    def test_upload_resume_success(self):
        """Test successful PDF upload"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        response = self.client.post(self.url, {'file': pdf_file})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertTrue(response.data['valid_file'])
        self.assertIsNone(response.data['error_msg'])

        # Verify database record was created
        session_id = response.data['id']
        session = InterviewSession.objects.get(id=session_id)
        # The resume_local_path stores the full absolute path
        expected_path = os.path.join(settings.MEDIA_ROOT, 'resumes', f"{session_id}.pdf")
        self.assertEqual(session.resume_local_path, expected_path)
        
        # Verify file exists
        file_path = os.path.join(settings.MEDIA_ROOT, 'resumes', f"{session_id}.pdf")
        self.assertTrue(os.path.exists(file_path))

    def test_upload_resume_no_file(self):
        """Test upload without providing a file"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(response.data['id'])
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
        self.assertIsNone(response.data['id'])
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
        self.assertIsNone(response.data['id'])
        self.assertFalse(response.data['valid_file'])
        self.assertEqual(response.data['error_msg'], 'File too big.')


class GetGrammarResultsTests(APITestCase):
    def setUp(self):
        self.url = reverse('get-grammar-results')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from django.conf import settings

        sessions = InterviewSession.objects.all()
        for session in sessions:
            if session.resume_local_path:
                file_path = os.path.join(settings.MEDIA_ROOT, session.resume_local_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        InterviewSession.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['id']

    def test_get_grammar_results_no_id(self):
        """Test get_grammar_results without providing id"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], 'id is required')

    def test_get_grammar_results_invalid_id(self):
        """Test get_grammar_results with non-existent id"""
        response = self.client.post(self.url, {'id': 'invalid-uuid'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_get_grammar_results_processing_status(self):
        """Test get_grammar_results when resume is still processing"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Ensure it's in processing state
        session = InterviewSession.objects.get(id=session_id)
        session.resume_status = InterviewSession.Status.PROCESSING
        session.save()

        response = self.client.post(self.url, {'id': session_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], '')

    def test_get_grammar_results_complete_status(self):
        """Test get_grammar_results when resume processing is complete"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Set it to complete with grammar results
        grammar_data = {
            "language": "en-US",
            "matches": [
                {
                    "message": "Possible typo: you repeated a word",
                    "shortMessage": "Possible typo",
                    "offset": 123,
                    "length": 7,
                    "replacements": [{"value": "example"}],
                    "context": {
                        "text": "...example example text...",
                        "offset": 3,
                        "length": 19
                    }
                }
            ]
        }
        session = InterviewSession.objects.get(id=session_id)
        session.resume_status = InterviewSession.Status.COMPLETE
        session.grammar_results = grammar_data
        session.save()

        response = self.client.post(self.url, {'id': session_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['grammar_check'], grammar_data)
        self.assertEqual(response.data['error'], '')

    def test_get_grammar_results_complete_status_no_results(self):
        """Test get_grammar_results when processing is complete but no grammar results"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Set it to complete without grammar results
        session = InterviewSession.objects.get(id=session_id)
        session.resume_status = InterviewSession.Status.COMPLETE
        session.grammar_results = None
        session.save()

        response = self.client.post(self.url, {'id': session_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['grammar_check'], {})
        self.assertEqual(response.data['error'], '')


class GetKeywordsTests(APITestCase):
    def setUp(self):
        self.url = reverse('get-keywords')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from django.conf import settings

        sessions = InterviewSession.objects.all()
        for session in sessions:
            if session.resume_local_path:
                file_path = os.path.join(settings.MEDIA_ROOT, session.resume_local_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        InterviewSession.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['id']

    def test_get_keywords_no_id(self):
        """Test get_keywords without providing id"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], 'id is required')

    def test_get_keywords_invalid_id(self):
        """Test get_keywords with non-existent id"""
        response = self.client.post(self.url, {'id': 'invalid-uuid'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_get_keywords_processing_status(self):
        """Test get_keywords when resume is still processing"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Ensure it's in processing state
        session = InterviewSession.objects.get(id=session_id)
        session.resume_status = InterviewSession.Status.PROCESSING
        session.save()

        response = self.client.post(self.url, {'id': session_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], '')

    def test_get_keywords_complete_status(self):
        """Test get_keywords when resume processing is complete"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Set it to complete with keywords
        session = InterviewSession.objects.get(id=session_id)
        session.resume_status = InterviewSession.Status.COMPLETE
        session.keywords = ['python', 'django', 'rest', 'api']
        session.save()

        response = self.client.post(self.url, {'id': session_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['keywords'], ['python', 'django', 'rest', 'api'])
        self.assertEqual(response.data['error'], '')


class TargetJobTests(APITestCase):
    def setUp(self):
        self.url = reverse('target-job')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from django.conf import settings

        sessions = InterviewSession.objects.all()
        for session in sessions:
            if session.resume_local_path:
                file_path = os.path.join(settings.MEDIA_ROOT, session.resume_local_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        InterviewSession.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['id']

    def test_target_job_success(self):
        """Test successful target job setting"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Set target job
        response = self.client.post(self.url, {
            'id': session_id,
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], session_id)
        self.assertEqual(response.data['message'], 'Target job and answer type saved successfully')
        self.assertEqual(response.data['answer_type'], 'text')  # Default value

        # Verify database was updated
        session = InterviewSession.objects.get(id=session_id)
        self.assertEqual(session.target_job, 'Software Engineer')
        self.assertEqual(session.answer_type, InterviewSession.AnswerType.TEXT)

    def test_target_job_with_video_answer_type(self):
        """Test target job setting with video answer type"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Set target job with video answer type
        response = self.client.post(self.url, {
            'id': session_id,
            'title': 'Software Engineer',
            'answer_type': 'video'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], session_id)
        self.assertEqual(response.data['message'], 'Target job and answer type saved successfully')
        self.assertEqual(response.data['answer_type'], 'video')

        # Verify database was updated
        session = InterviewSession.objects.get(id=session_id)
        self.assertEqual(session.target_job, 'Software Engineer')
        self.assertEqual(session.answer_type, InterviewSession.AnswerType.VIDEO)

    def test_target_job_missing_id(self):
        """Test target job without id"""
        response = self.client.post(self.url, {
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_missing_title(self):
        """Test target job without title"""
        session_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'id': session_id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_invalid_answer_type(self):
        """Test target job with invalid answer type"""
        session_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'id': session_id,
            'title': 'Software Engineer',
            'answer_type': 'invalid'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "answer_type must be either 'text' or 'video'")

    def test_target_job_invalid_id(self):
        """Test target job with non-existent id"""
        response = self.client.post(self.url, {
            'id': 'invalid-uuid-12345',
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Resume not found')


class RemoveResumeTests(APITestCase):
    def setUp(self):
        self.url = reverse('remove-resume')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up any remaining files after each test
        from django.conf import settings

        sessions = InterviewSession.objects.all()
        for session in sessions:
            if session.resume_local_path:
                file_path = os.path.join(settings.MEDIA_ROOT, session.resume_local_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        InterviewSession.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['id']

    def test_remove_resume_success(self):
        """Test successful resume removal"""
        # Upload a resume first
        session_id = self._upload_test_resume()

        # Verify the resume exists
        session = InterviewSession.objects.get(id=session_id)
        file_path = session.resume_local_path
        self.assertTrue(os.path.exists(file_path))

        # Remove the resume
        response = self.client.post(self.url, {'id': session_id})

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['id'], session_id)
        self.assertEqual(response.data['message'], 'Resume removed successfully')
        self.assertTrue(response.data['file_removed'])

        # Verify database record was deleted
        self.assertFalse(InterviewSession.objects.filter(id=session_id).exists())

        # Verify file was deleted
        self.assertFalse(os.path.exists(file_path))

    def test_remove_resume_no_id(self):
        """Test remove resume without providing id"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'id is required')

    def test_remove_resume_invalid_id(self):
        """Test remove resume with non-existent id"""
        response = self.client.post(self.url, {'id': 'invalid-uuid-12345'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_remove_resume_missing_file(self):
        """Test remove resume when database entry exists but file is missing"""
        # Upload a resume
        session_id = self._upload_test_resume()

        # Manually delete the file but keep database record
        session = InterviewSession.objects.get(id=session_id)
        file_path = session.resume_local_path
        if os.path.exists(file_path):
            os.remove(file_path)

        # Try to remove the resume
        response = self.client.post(self.url, {'id': session_id})

        # Should still succeed (database record removed)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['id'], session_id)
        self.assertEqual(response.data['message'], 'Resume removed successfully')
        self.assertFalse(response.data['file_removed'])  # File wasn't removed because it didn't exist

        # Verify database record was deleted
        self.assertFalse(InterviewSession.objects.filter(id=session_id).exists())