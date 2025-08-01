import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from resume.models import Resume
from .interview_session import InterviewSession


class BasicInterviewAPITest(APITestCase):
    """Basic tests for interview APIs"""

    def setUp(self):
        """Set up test data"""
        self.doc_id = uuid.uuid4()
        self.resume = Resume.objects.create(
            id=self.doc_id,
            keywords=["mongodb", "aws", "kubernetes", "agile", "rest apis", "docker", "microservices", "postgresql",
                      "python", "react"],
            target_job='Software Engineer'
        )

    def test_get_questions_success(self):
        """Test getting interview questions successfully"""
        url = reverse('get-questions')

        data = {'doc_id': str(self.doc_id)}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['doc_id'], str(self.doc_id))
        self.assertIn('interview_questions', response.data)

    def test_get_questions_missing_doc_id(self):
        """Test get questions with missing doc_id"""
        url = reverse('get-questions')

        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_get_questions_invalid_doc_id(self):
        """Test get questions with invalid doc_id"""
        url = reverse('get-questions')
        data = {'doc_id': str(uuid.uuid4())}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_submit_answer_success(self):
        """Test submitting an answer successfully"""
        # Create a session first
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["What are your strengths?", "Tell me about a project"]
        )

        url = reverse('submit-answer')
        data = {
            'doc_id': str(self.doc_id),
            'question_index': 0,
            'question': "What are your strengths?",
            'answer': 'My strengths are problem-solving and teamwork.'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['doc_id'], str(self.doc_id))

    def test_submit_answer_missing_doc_id(self):
        """Test submit answer with missing doc_id"""
        url = reverse('submit-answer')
        data = {
            'question_index': 0,
            'answer': 'Some answer'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_submit_answer_missing_answer(self):
        """Test submit answer with missing answer"""
        url = reverse('submit-answer')
        data = {
            'doc_id': str(self.doc_id),
            'question_index': 0
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_submit_answer_invalid_session(self):
        """Test submit answer with invalid session"""
        url = reverse('submit-answer')
        data = {
            'doc_id': str(uuid.uuid4()),
            'question_index': 0,
            'question': 'Some question',
            'answer': 'Some answer'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    @patch('interview.views.get_feedback_using_openai')
    def test_get_feedback_success(self, mock_openai):
        """Test getting feedback successfully"""
        # Create an interview session with completed answers (3 questions as expected by utils)
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["What are your strengths?", "Tell me about a project", "Why this company?"],
            answers=["I'm good at problem solving", "I built a web application", "Great culture and growth opportunities"],
            is_completed=True
        )

        mock_feedback = {
            "question_1_feedback": "Great answer on problem solving!",
            "question_2_feedback": "Your project experience shows good technical skills.",
            "question_3_feedback": "Good understanding of company values.",
            "summary": "Overall strong performance with room for more specific examples."
        }
        mock_openai.return_value = mock_feedback

        url = reverse('get-feedback')
        response = self.client.get(url, {'doc_id': str(self.doc_id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['doc_id'], str(self.doc_id))
        self.assertEqual(response.data['feedbacks'], mock_feedback)
        
        # Verify that OpenAI was called with correct parameters
        mock_openai.assert_called_once_with(self.resume, session)
        
        # Verify that feedback was saved to the session
        session.refresh_from_db()
        self.assertEqual(session.feedback, mock_feedback)

    @patch('interview.views.get_feedback_using_openai')
    def test_get_feedback_no_feedback_generated(self, mock_openai):
        """Test getting feedback when no feedback is generated"""
        # Create an interview session with 3 questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["What are your strengths?", "Tell me about a project", "Why this company?"],
            answers=["I'm good at problem solving", "I built a web application", "Great culture"],
            is_completed=True
        )

        # Mock OpenAI to return None/empty feedback
        mock_openai.return_value = None

        url = reverse('get-feedback')
        response = self.client.get(url, {'doc_id': str(self.doc_id)})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No feedback questions found')

    @patch('interview.views.get_feedback_using_openai')
    def test_get_feedback_empty_feedback_generated(self, mock_openai):
        """Test getting feedback when empty feedback is generated"""
        # Create an interview session with 3 questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["What are your strengths?", "Tell me about a project", "Why this company?"],
            answers=["I'm good at problem solving", "I built a web application", "Great culture"],
            is_completed=True
        )

        # Mock OpenAI to return empty dict or list
        mock_openai.return_value = {}

        url = reverse('get-feedback')
        response = self.client.get(url, {'doc_id': str(self.doc_id)})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No feedback questions found')

    def test_get_feedback_missing_doc_id(self):
        """Test get feedback with missing doc_id"""
        url = reverse('get-feedback')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'doc_id is required')

    def test_get_feedback_invalid_doc_id(self):
        """Test get feedback with invalid doc_id"""
        url = reverse('get-feedback')

        response = self.client.get(url, {'doc_id': str(uuid.uuid4())})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Resume not found')

    def test_get_feedback_no_interview_session(self):
        """Test get feedback when no interview session exists"""
        # Don't create an interview session, just use the resume
        url = reverse('get-feedback')

        response = self.client.get(url, {'doc_id': str(self.doc_id)})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Interview session not found')

    @patch('interview.views.get_feedback_using_openai')
    def test_get_feedback_with_partial_answers(self, mock_openai):
        """Test getting feedback for a session with partial answers"""
        # Create an interview session with some unanswered questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["What are your strengths?", "Tell me about a project", "Why this company?"],
            answers=["I'm good at problem solving", "I built a web application", ""],  # Last answer empty
            is_completed=False
        )

        mock_feedback = {
            "question_1_feedback": "Good start on your answers", 
            "question_2_feedback": "Consider providing more details", 
            "question_3_feedback": "Please provide an answer to this question",
            "summary": "Complete all questions for full feedback"
        }
        mock_openai.return_value = mock_feedback

        url = reverse('get-feedback')
        response = self.client.get(url, {'doc_id': str(self.doc_id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['feedbacks'], mock_feedback)
        
        # Verify that OpenAI was called even for incomplete session
        mock_openai.assert_called_once_with(self.resume, session)


class InterviewModelBasicTest(TestCase):
    """Basic tests for InterviewSession model"""

    def setUp(self):
        """Set up test data"""
        self.doc_id = uuid.uuid4()
        self.resume = Resume.objects.create(
            id=self.doc_id,
            keywords=['python'],
            target_job='Developer'
        )

    def test_create_session(self):
        """Test creating an interview session"""
        questions = ["Question 1", "Question 2"]
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=questions
        )

        self.assertEqual(session.doc_id, self.doc_id)
        self.assertEqual(session.questions, questions)
        self.assertEqual(session.answers, [])
        self.assertFalse(session.is_completed)

    def test_session_progress(self):
        """Test session progress calculation"""
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["Q1", "Q2", "Q3"],
            answers=["A1", "", "A3"]
        )

        self.assertEqual(session.progress, "2/3")
        self.assertEqual(session.completion_percentage, 66.7)
