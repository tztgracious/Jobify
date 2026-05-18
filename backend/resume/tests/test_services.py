import uuid
import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from interview.models.interview_session import InterviewSession
from resume.services import ResumeService

class ResumeServiceTest(TestCase):
    def setUp(self):
        self.session_id = str(uuid.uuid4())
        self.test_file = SimpleUploadedFile(
            "test_resume.pdf",
            b"test content",
            content_type="application/pdf"
        )

    def test_create_interview_session(self):
        session = ResumeService.create_interview_session(self.session_id, "/tmp/test.pdf")
        self.assertEqual(str(session.id), self.session_id)
        self.assertEqual(session.resume_status, InterviewSession.Status.PROCESSING)

    def test_get_session_by_id(self):
        ResumeService.create_interview_session(self.session_id, "/tmp/test.pdf")
        retrieved = ResumeService.get_session_by_id(self.session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(str(retrieved.id), self.session_id)

    def test_set_target_job(self):
        ResumeService.create_interview_session(self.session_id, "/tmp/test.pdf")
        success = ResumeService.set_target_job(self.session_id, "Software Engineer", "video")
        self.assertTrue(success)
        
        session = InterviewSession.objects.get(id=self.session_id)
        self.assertEqual(session.target_job, "Software Engineer")
        self.assertEqual(session.answer_type, "video")

    def test_cleanup_all_resumes(self):
        ResumeService.create_interview_session(self.session_id, "/tmp/test.pdf")
        results = ResumeService.cleanup_all_resumes()
        self.assertEqual(results["db_records_removed"], 1)
        self.assertEqual(InterviewSession.objects.count(), 0)
