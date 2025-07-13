import os
from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from resume.models import Resume


class ResumeFlowTest(APITestCase):
    def setUp(self):
        """Set up test data"""
        # Path to the fixtures directory
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        
        # Available test PDF files
        self.test_pdfs = {
            'professional': 'professional_resume.pdf',
            'simple': 'simple_resume.pdf',
            'resume1': 'resume_1.pdf',
            'resume2': 'resume_2.pdf',
            'resume3': 'resume_3.pdf'
        }
    
    def get_pdf_content(self, pdf_name):
        """Load PDF content from fixtures directory"""
        pdf_path = os.path.join(self.fixtures_dir, self.test_pdfs[pdf_name])
        with open(pdf_path, 'rb') as f:
            return f.read()

    def tearDown(self):
        """Clean up uploaded files after each test"""
        resumes = Resume.objects.all()
        for resume in resumes:
            file_path = os.path.join(settings.MEDIA_ROOT, resume.local_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        Resume.objects.all().delete()

    def test_full_resume_process(self):
        """Test the complete resume processing flow as a user would experience it"""
        
        # 1. Upload a real resume file from fixtures
        pdf_content = self.get_pdf_content('professional')
        uploaded_file = SimpleUploadedFile(
            "professional_resume.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('upload-resume'),
            data={'file': uploaded_file},
            format='multipart'
        )

        # Verify upload was successful
        self.assertEqual(response.status_code, 201)
        self.assertIn('doc_id', response.data)
        self.assertTrue(response.data['valid_file'])
        self.assertIsNone(response.data['error_msg'])
        
        doc_id = response.data["doc_id"]

        # 2. Check keywords immediately after upload (should be processing)
        response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'  # API expects multipart form data
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["finished"])  # Should be False while processing
        self.assertEqual(response.data["keywords"], [])
        self.assertEqual(response.data["error"], "")

        # 3. Simulate background processing completion
        resume = Resume.objects.get(id=doc_id)
        resume.keywords = ["python", "django", "rest", "api"]
        resume.status = Resume.Status.COMPLETE
        resume.save()

        # 4. Check keywords again - should now be available
        response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["finished"])  # Should be True when complete
        self.assertEqual(response.data["keywords"], ["python", "django", "rest", "api"])
        self.assertEqual(response.data["error"], "")

    def test_upload_invalid_file(self):
        """Test uploading an invalid file"""
        # Try uploading a non-PDF file
        invalid_file = SimpleUploadedFile(
            "test.txt", 
            b"This is not a PDF", 
            content_type="text/plain"
        )

        response = self.client.post(
            reverse('upload-resume'),
            data={'file': invalid_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(response.data['doc_id'])
        self.assertFalse(response.data['valid_file'])
        self.assertEqual(response.data['error_msg'], 'Not a PDF file.')

    def test_get_keywords_with_invalid_doc_id(self):
        """Test getting keywords with invalid doc_id"""
        response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": "invalid-uuid"},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["finished"])
        self.assertEqual(response.data["keywords"], [])
        self.assertEqual(response.data["error"], "Resume not found")

    def test_get_keywords_without_doc_id(self):
        """Test getting keywords without providing doc_id"""
        response = self.client.post(
            reverse('get-keywords'),
            data={},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["finished"])
        self.assertEqual(response.data["keywords"], [])
        self.assertEqual(response.data["error"], "doc_id is required")

    def test_processing_failed_scenario(self):
        """Test scenario where resume processing fails"""
        # Upload a file first using a different PDF from fixtures
        pdf_content = self.get_pdf_content('simple')
        uploaded_file = SimpleUploadedFile(
            "simple_resume.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('upload-resume'),
            data={'file': uploaded_file},
            format='multipart'
        )
        
        doc_id = response.data["doc_id"]

        # Simulate processing failure
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.FAILED
        resume.save()

        # Check keywords - should return error and restart processing
        response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data["finished"])
        self.assertEqual(response.data["keywords"], [])
        self.assertEqual(response.data["error"], "Resume processing failed. Trying again.")

    def test_multiple_resume_uploads(self):
        """Test uploading multiple different resumes"""
        uploaded_docs = []
        
        # Test with different PDF files from fixtures
        for pdf_key, pdf_filename in self.test_pdfs.items():
            pdf_content = self.get_pdf_content(pdf_key)
            uploaded_file = SimpleUploadedFile(
                pdf_filename, 
                pdf_content, 
                content_type="application/pdf"
            )

            response = self.client.post(
                reverse('upload-resume'),
                data={'file': uploaded_file},
                format='multipart'
            )

            self.assertEqual(response.status_code, 201)
            self.assertIn('doc_id', response.data)
            self.assertTrue(response.data['valid_file'])
            uploaded_docs.append(response.data["doc_id"])

        # Verify all uploads created separate database entries
        self.assertEqual(Resume.objects.count(), len(self.test_pdfs))
        
        # Test getting keywords for each uploaded resume
        for doc_id in uploaded_docs:
            response = self.client.post(
                reverse('get-keywords'),
                data={"doc_id": doc_id},
                format='multipart'
            )
            
            # Should be processing initially
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.data["finished"])

    def test_complete_user_journey(self):
        """Test the complete user journey from upload to getting final keywords"""
        
        # Step 1: User uploads their resume
        pdf_content = self.get_pdf_content('resume1')
        uploaded_file = SimpleUploadedFile(
            "my_resume.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )

        upload_response = self.client.post(
            reverse('upload-resume'),
            data={'file': uploaded_file},
            format='multipart'
        )

        self.assertEqual(upload_response.status_code, 201)
        doc_id = upload_response.data["doc_id"]
        
        # Step 2: User immediately checks for keywords (should be processing)
        keywords_response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(keywords_response.status_code, 200)
        self.assertFalse(keywords_response.data["finished"])
        self.assertEqual(keywords_response.data["error"], "")
        
        # Step 3: User checks again after some time (still processing)
        keywords_response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(keywords_response.status_code, 200)
        self.assertFalse(keywords_response.data["finished"])
        
        # Step 4: Backend processing completes
        resume = Resume.objects.get(id=doc_id)
        resume.keywords = ["javascript", "react", "node.js", "mongodb", "express"]
        resume.status = Resume.Status.COMPLETE
        resume.save()
        
        # Step 5: User checks again and gets the final keywords
        final_response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(final_response.status_code, 200)
        self.assertTrue(final_response.data["finished"])
        self.assertEqual(final_response.data["keywords"], ["javascript", "react", "node.js", "mongodb", "express"])
        self.assertEqual(final_response.data["error"], "")

    def test_large_resume_upload(self):
        """Test uploading different sized resumes from fixtures"""
        # Test with the largest resume file available
        pdf_content = self.get_pdf_content('resume3')  # Assuming this might be larger
        
        uploaded_file = SimpleUploadedFile(
            "large_resume.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('upload-resume'),
            data={'file': uploaded_file},
            format='multipart'
        )

        # Should succeed as fixtures should be under 5MB limit
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['valid_file'])
        
        # Verify file was saved correctly
        doc_id = response.data["doc_id"]
        resume = Resume.objects.get(id=doc_id)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, resume.local_path)))

    def test_error_recovery_workflow(self):
        """Test the workflow when processing fails and recovers"""
        # Upload resume
        pdf_content = self.get_pdf_content('resume2')
        uploaded_file = SimpleUploadedFile(
            "error_test_resume.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('upload-resume'),
            data={'file': uploaded_file},
            format='multipart'
        )
        
        doc_id = response.data["doc_id"]

        # Simulate processing failure
        resume = Resume.objects.get(id=doc_id)
        resume.status = Resume.Status.FAILED
        resume.save()

        # User checks keywords - should get error and trigger retry
        response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"], "Resume processing failed. Trying again.")

        # Simulate successful retry
        resume.refresh_from_db()
        resume.status = Resume.Status.COMPLETE
        resume.keywords = ["python", "machine learning", "tensorflow"]
        resume.save()

        # User checks again - should now succeed
        response = self.client.post(
            reverse('get-keywords'),
            data={"doc_id": doc_id},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["finished"])
        self.assertEqual(response.data["keywords"], ["python", "machine learning", "tensorflow"])
