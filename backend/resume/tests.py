import os
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from resume.models import Resume


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
        # self.assertEqual(resume.local_path, f"resumes/{doc_id}.pdf")
        self.assertTrue(os.path.exists(resume.local_path), f"Resume file does not exist at path: {resume.local_path}")

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


class GetKeywordsTests(APITestCase):
    def setUp(self):
        self.url = reverse('get-keywords')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from resume.models import Resume
        import os

        resumes = Resume.objects.all()
        for resume in resumes:
            if os.path.exists(resume.local_path):
                os.remove(resume.local_path)
        Resume.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return doc_id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['doc_id']

    def test_get_keywords_no_doc_id(self):
        """Test get_keywords without providing doc_id"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], 'doc_id is required')

    def test_get_keywords_invalid_doc_id(self):
        """Test get_keywords with non-existent doc_id"""
        response = self.client.post(self.url, {'doc_id': 'invalid-uuid'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_get_keywords_processing_status(self):
        """Test get_keywords when resume is still processing"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Ensure it's in processing state
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.PROCESSING
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], '')

    def test_get_keywords_complete_status(self):
        """Test get_keywords when resume processing is complete"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with keywords
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.keywords = ['python', 'django', 'rest', 'api']
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['keywords'], ['python', 'django', 'rest', 'api'])
        self.assertEqual(response.data['error'], '')

    def test_get_keywords_complete_status_no_keywords(self):
        """Test get_keywords when processing is complete but no keywords found"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with empty keywords
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.keywords = []
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], '')

    def test_get_keywords_complete_status_null_keywords(self):
        """Test get_keywords when processing is complete but keywords is empty"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with empty keywords (since null is not allowed)
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.keywords = []  # Use empty list instead of None
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], '')

    def test_get_keywords_failed_status(self):
        """Test get_keywords when resume processing failed"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to failed status
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.FAILED
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['keywords'], [])
        self.assertEqual(response.data['error'], 'Resume processing failed. Trying again.')

    def test_get_keywords_multipart_form_data(self):
        """Test that get_keywords accepts multipart/form-data as specified in API docs"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with keywords
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.keywords = ['javascript', 'react', 'node']
        resume.save()

        # Test with multipart form data (using FILES parameter)
        response = self.client.post(self.url, data={'doc_id': doc_id}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['keywords'], ['javascript', 'react', 'node'])
        self.assertEqual(response.data['error'], '')

    def test_get_keywords_api_specification_compliance(self):
        """Test that response format matches the API specification exactly"""
        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with keywords
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.keywords = ['c++', 'java']
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        # Verify response format matches API spec exactly
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('finished', response.data)
        self.assertIn('keywords', response.data)
        self.assertIn('error', response.data)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['keywords'], ['c++', 'java'])
        self.assertEqual(response.data['error'], '')

        # Verify no extra fields
        self.assertEqual(len(response.data), 3)

    @patch('resume.views.threading.Thread')
    def test_get_keywords_failed_status_restarts_processing(self, mock_thread):
        """Test that failed status triggers reprocessing"""

        # Upload a resume but prevent automatic parsing
        with patch('resume.views.threading.Thread') as mock_upload_thread:
            doc_id = self._upload_test_resume()

        # Set it to failed status
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.FAILED
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        # Verify that a new thread was started to reprocess
        mock_thread.assert_called_once()
        thread_call_args = mock_thread.call_args
        self.assertEqual(thread_call_args[1]['target'].__name__, 'parse_resume')
        # The args should contain the UUID of the resume
        self.assertEqual(str(thread_call_args[1]['args'][0]), str(doc_id))

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['finished'])
        self.assertEqual(response.data['error'], 'Resume processing failed. Trying again.')


class TargetJobTests(APITestCase):
    def setUp(self):
        self.url = reverse('target-job')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test

        resumes = Resume.objects.all()
        for resume in resumes:
            if os.path.exists(resume.local_path):
                os.remove(resume.local_path)
        Resume.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return doc_id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['doc_id']

    def test_target_job_success(self):
        """Test successful target job setting"""

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set target job
        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['doc_id'], doc_id)
        self.assertEqual(response.data['message'], 'Target job saved successfully')

        # Verify database was updated
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, 'Software Engineer')

    def test_target_job_missing_doc_id(self):
        """Test target job without doc_id"""
        response = self.client.post(self.url, {
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_missing_title(self):
        """Test target job without title"""
        doc_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'doc_id': doc_id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_missing_both_fields(self):
        """Test target job without both required fields"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_invalid_doc_id(self):
        """Test target job with non-existent doc_id"""
        response = self.client.post(self.url, {
            'doc_id': 'invalid-uuid-12345',
            'title': 'Software Engineer'
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_target_job_empty_title(self):
        """Test target job with empty title"""
        doc_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': ''
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_whitespace_title(self):
        """Test target job with whitespace-only title"""
        doc_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': '   '
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing required fields')

    def test_target_job_update_existing(self):
        """Test updating an existing target job"""

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set initial target job
        response1 = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': 'Software Engineer'
        })
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Update target job
        response2 = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': 'Senior Software Engineer'
        })

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['doc_id'], doc_id)
        self.assertEqual(response2.data['message'], 'Target job saved successfully')

        # Verify database was updated with new value
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, 'Senior Software Engineer')

    def test_target_job_long_title(self):
        """Test target job with long title"""

        doc_id = self._upload_test_resume()
        long_title = 'Senior Principal Software Development Engineer in Test Lead Manager' * 5  # Very long title

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': long_title
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify database was updated
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, long_title)

    def test_target_job_special_characters(self):
        """Test target job with special characters"""

        doc_id = self._upload_test_resume()
        special_title = 'Software Engineer (C#/.NET) - Level II/III'

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': special_title
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify database was updated
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, special_title)

    def test_target_job_unicode_characters(self):
        """Test target job with unicode characters"""

        doc_id = self._upload_test_resume()
        unicode_title = 'Software Engineer'

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': unicode_title
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify database was updated
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, unicode_title)

    def test_target_job_multiple_resumes(self):
        """Test that setting target job for one resume doesn't affect others"""

        # Upload two resumes
        doc_id1 = self._upload_test_resume()
        doc_id2 = self._upload_test_resume()

        # Set different target jobs
        response1 = self.client.post(self.url, {
            'doc_id': doc_id1,
            'title': 'Frontend Developer'
        })
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.url, {
            'doc_id': doc_id2,
            'title': 'Backend Developer'
        })
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify both resumes have correct target jobs
        resume1 = Resume.objects.get(id=doc_id1)
        resume2 = Resume.objects.get(id=doc_id2)
        self.assertEqual(resume1.target_job, 'Frontend Developer')
        self.assertEqual(resume2.target_job, 'Backend Developer')

    def test_target_job_response_format(self):
        """Test that response format matches API specification"""
        doc_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': 'Data Scientist'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response format
        self.assertIn('doc_id', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['doc_id'], doc_id)
        self.assertEqual(response.data['message'], 'Target job saved successfully')

        # Verify no extra fields
        self.assertEqual(len(response.data), 2)

    def test_target_job_json_content_type(self):
        """Test target job with JSON content type"""

        doc_id = self._upload_test_resume()

        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': 'DevOps Engineer'
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify database was updated
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, 'DevOps Engineer')

    def test_target_job_form_data_content_type(self):
        """Test target job with form data content type"""

        doc_id = self._upload_test_resume()

        # Use format='multipart' instead of content_type for form data
        response = self.client.post(self.url, {
            'doc_id': doc_id,
            'title': 'Product Manager'
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify database was updated
        resume = Resume.objects.get(id=doc_id)
        self.assertEqual(resume.target_job, 'Product Manager')


class RemoveResumeTests(APITestCase):
    def setUp(self):
        self.url = reverse('remove-resume')
        self.upload_url = reverse('upload-resume')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up any remaining files after each test
        resumes = Resume.objects.all()
        for resume in resumes:
            if os.path.exists(resume.local_path):
                os.remove(resume.local_path)
        Resume.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return doc_id"""
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': pdf_file})
        return response.data['doc_id']

    def test_remove_resume_success(self):
        """Test successful resume removal"""
        # Upload a resume first
        doc_id = self._upload_test_resume()

        # Verify the resume exists
        resume = Resume.objects.get(id=doc_id)
        file_path = resume.local_path
        self.assertTrue(os.path.exists(file_path))

        # Remove the resume
        response = self.client.post(self.url, {'doc_id': doc_id})

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['doc_id'], doc_id)
        self.assertEqual(response.data['message'], 'Resume removed successfully')
        self.assertTrue(response.data['file_removed'])

        # Verify database record was deleted
        self.assertFalse(Resume.objects.filter(id=doc_id).exists())

        # Verify file was deleted
        self.assertFalse(os.path.exists(file_path))

    def test_remove_resume_no_doc_id(self):
        """Test remove resume without providing doc_id"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'doc_id is required')

    def test_remove_resume_invalid_doc_id(self):
        """Test remove resume with non-existent doc_id"""
        response = self.client.post(self.url, {'doc_id': 'invalid-uuid-12345'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_remove_resume_missing_file(self):
        """Test remove resume when database entry exists but file is missing"""
        # Upload a resume
        doc_id = self._upload_test_resume()

        # Manually delete the file but keep database record
        resume = Resume.objects.get(id=doc_id)
        file_path = resume.local_path
        if os.path.exists(file_path):
            os.remove(file_path)

        # Try to remove the resume
        response = self.client.post(self.url, {'doc_id': doc_id})

        # Should still succeed (database record removed)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['doc_id'], doc_id)
        self.assertEqual(response.data['message'], 'Resume removed successfully')
        self.assertFalse(response.data['file_removed'])  # File wasn't removed because it didn't exist

        # Verify database record was deleted
        self.assertFalse(Resume.objects.filter(id=doc_id).exists())

    def test_remove_resume_already_removed(self):
        """Test removing a resume that was already removed"""
        # Upload a resume
        doc_id = self._upload_test_resume()

        # Remove it once
        response1 = self.client.post(self.url, {'doc_id': doc_id})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Try to remove it again
        response2 = self.client.post(self.url, {'doc_id': doc_id})

        # Should return 404 not found
        self.assertEqual(response2.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response2.data['success'])
        self.assertEqual(response2.data['error'], 'Resume not found')

    def test_remove_resume_response_format(self):
        """Test that response format matches API specification"""
        doc_id = self._upload_test_resume()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response format
        self.assertIn('success', response.data)
        self.assertIn('doc_id', response.data)
        self.assertIn('message', response.data)
        self.assertIn('file_removed', response.data)

        # Verify correct values
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['doc_id'], doc_id)
        self.assertEqual(response.data['message'], 'Resume removed successfully')
        self.assertIsInstance(response.data['file_removed'], bool)

    def test_remove_resume_multiple_resumes(self):
        """Test removing one resume doesn't affect others"""
        # Upload two resumes
        doc_id1 = self._upload_test_resume()
        doc_id2 = self._upload_test_resume()

        # Remove only the first one
        response = self.client.post(self.url, {'doc_id': doc_id1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify first resume is gone
        self.assertFalse(Resume.objects.filter(id=doc_id1).exists())

        # Verify second resume still exists
        self.assertTrue(Resume.objects.filter(id=doc_id2).exists())
        resume2 = Resume.objects.get(id=doc_id2)
        self.assertTrue(os.path.exists(resume2.local_path))


class GetGrammarResultsTests(APITestCase):
    def setUp(self):
        self.url = reverse('get-grammar-results')
        self.valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'

    def tearDown(self):
        # Clean up uploaded files after each test
        from resume.models import Resume
        import os
        from django.conf import settings

        resumes = Resume.objects.all()
        for resume in resumes:
            if resume.local_path:
                file_path = resume.local_path
                if os.path.exists(file_path):
                    os.remove(file_path)
        Resume.objects.all().delete()

    def _upload_test_resume(self):
        """Helper method to upload a test resume and return doc_id"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        pdf_file = SimpleUploadedFile(
            "test_resume.pdf",
            self.valid_pdf_content,
            content_type="application/pdf"
        )

        upload_url = reverse('upload-resume')
        response = self.client.post(upload_url, {'file': pdf_file})
        return response.data['doc_id']

    def test_get_grammar_results_no_doc_id(self):
        """Test get_grammar_results without providing doc_id"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], 'doc_id is required')

    def test_get_grammar_results_invalid_doc_id(self):
        """Test get_grammar_results with non-existent doc_id"""
        response = self.client.post(self.url, {'doc_id': 'invalid-uuid'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_get_grammar_results_processing_status(self):
        """Test get_grammar_results when resume is still processing"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Ensure it's in processing state
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.PROCESSING
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], '')

    def test_get_grammar_results_complete_status(self):
        """Test get_grammar_results when resume processing is complete"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

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
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.grammar_results = grammar_data
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['grammar_check'], grammar_data)
        self.assertEqual(response.data['error'], '')

    def test_get_grammar_results_complete_status_no_results(self):
        """Test get_grammar_results when processing is complete but no grammar results"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete without grammar results
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.grammar_results = None
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['grammar_check'], {})
        self.assertEqual(response.data['error'], '')

    def test_get_grammar_results_complete_status_empty_results(self):
        """Test get_grammar_results when processing is complete with empty grammar results"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with empty grammar results
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.grammar_results = {}
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['grammar_check'], {})
        self.assertEqual(response.data['error'], '')

    @patch('threading.Thread')
    def test_get_grammar_results_failed_status_restarts_processing(self, mock_thread):
        """Test get_grammar_results restarts processing when status is failed"""
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to failed status
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.FAILED
        resume.save()

        response = self.client.post(self.url, {'doc_id': doc_id})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['finished'])
        self.assertIsNone(response.data['grammar_check'])
        self.assertEqual(response.data['error'], 'Resume processing failed. Trying again.')

        # Verify that parse_resume was called to restart processing
        # Note: Thread might be called twice - once from upload, once from failed status restart
        self.assertTrue(mock_thread.call_count >= 1)
        mock_thread.return_value.start.assert_called()

    def test_get_grammar_results_json_content_type(self):
        """Test that get_grammar_results accepts JSON data"""
        import json
        from resume.models import Resume

        # Upload a resume
        doc_id = self._upload_test_resume()

        # Set it to complete with grammar results
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.COMPLETE
        resume.grammar_results = {"language": "en-US", "matches": []}
        resume.save()

        response = self.client.post(
            self.url,
            json.dumps({'doc_id': doc_id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['finished'])
        self.assertEqual(response.data['grammar_check'], {"language": "en-US", "matches": []})
        self.assertEqual(response.data['error'], '')
