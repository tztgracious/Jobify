import os
import uuid

from rest_framework.test import APITestCase

from interview.models import InterviewSession
from resume.models import Resume


class InterviewFlowTest(APITestCase):
    def setUp(self):
        """Set up test data for interview flow"""
        # Path to the fixtures directory
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

        # Create a resume for testing
        self.doc_id = uuid.uuid4()
        self.resume = Resume.objects.create(
            id=self.doc_id,
            keywords=['python', 'django', 'rest', 'api'],
            target_job='Backend Developer',
            status=Resume.Status.COMPLETE
        )

    def tearDown(self):
        """Clean up after tests"""
        InterviewSession.objects.all().delete()
        Resume.objects.all().delete()

    def test_simple_interview_flow_step_by_step(self):
        """Test simple interview flow where user answers questions one by one"""
        # Create interview session directly in database with dummy questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=[
                "Tell me about your Python experience",
                "Describe a challenging project",
                "How do you handle debugging?"
            ]
        )

        # Step 1: User answers first question
        response1 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 0,
                'question': "Tell me about your Python experience",
                'answer': 'I have 5 years of Python experience building web applications.'
            },
            format='json'
        )

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.data['progress'], '1/3')
        self.assertFalse(response1.data['is_completed'])

        # Step 2: User answers second question
        response2 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 1,
                'question': "Describe a challenging project",
                'answer': 'I built a microservices system with complex API integrations.'
            },
            format='json'
        )

        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data['progress'], '2/3')
        self.assertFalse(response2.data['is_completed'])

        # Step 3: User answers final question
        response3 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 2,
                'question': "How do you handle debugging?",
                'answer': 'I use systematic debugging with logging and testing tools.'
            },
            format='json'
        )

        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.data['progress'], '3/3')
        self.assertTrue(response3.data['is_completed'])

        # Verify all answers are saved
        session.refresh_from_db()
        self.assertEqual(len(session.answers), 3)
        self.assertIn('Python experience', session.answers[0])
        self.assertIn('microservices', session.answers[1])
        self.assertIn('debugging', session.answers[2])
        self.assertTrue(session.is_completed)

    def test_interview_flow_with_answer_revision(self):
        """Test interview flow where user revises an answer before completing"""
        # Create session directly with dummy questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["What are your strengths?", "Tell me about a project"]
        )

        # Answer first question
        initial_answer = "My initial answer about my strengths."
        self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 0,
                'question': "What are your strengths?",
                'answer': initial_answer
            },
            format='json'
        )

        # User decides to revise the first answer
        revised_answer = "My revised and much better answer with specific examples."
        revision_response = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 0,
                'question': "What are your strengths?",
                'answer': revised_answer
            },
            format='json'
        )

        self.assertEqual(revision_response.status_code, 200)
        self.assertEqual(revision_response.data['answer'], revised_answer)
        self.assertEqual(revision_response.data['progress'], '1/2')

        # Verify the revised answer was saved
        session.refresh_from_db()
        self.assertEqual(session.answers[0], revised_answer)
        self.assertNotEqual(session.answers[0], initial_answer)

    def test_interview_flow_out_of_order_answers(self):
        """Test interview flow where user answers questions out of order"""
        # Create session directly with dummy questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["Question 1", "Question 2", "Question 3"]
        )

        # Answer third question first
        response_3 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 2,
                'question': "Question 3",
                'answer': 'Answer to question 3'
            },
            format='json'
        )

        self.assertEqual(response_3.status_code, 200)
        self.assertEqual(response_3.data['progress'], '1/3')
        self.assertFalse(response_3.data['is_completed'])

        # Answer first question second
        response_1 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 0,
                'question': "Question 1",
                'answer': 'Answer to question 1'
            },
            format='json'
        )

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_1.data['progress'], '2/3')
        self.assertFalse(response_1.data['is_completed'])

        # Answer second question last to complete
        response_2 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 1,
                'question': "Question 2",
                'answer': 'Answer to question 2'
            },
            format='json'
        )

        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_2.data['progress'], '3/3')
        self.assertTrue(response_2.data['is_completed'])

        # Verify all answers are in correct positions
        session.refresh_from_db()
        self.assertEqual(session.answers[0], 'Answer to question 1')
        self.assertEqual(session.answers[1], 'Answer to question 2')
        self.assertEqual(session.answers[2], 'Answer to question 3')

    def test_interview_flow_error_handling(self):
        """Test interview flow with various error conditions"""
        # Create session directly with dummy questions
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["Question 1", "Question 2", "Question 3"]
        )

        # Try to submit answer with wrong question text
        error_response = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 0,
                'question': 'Wrong question text',
                'answer': 'Some answer'
            },
            format='json'
        )

        self.assertEqual(error_response.status_code, 400)
        self.assertIn('Question text does not match', error_response.data['error'])

        # Try to submit answer with invalid question index
        error_response_2 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 10,
                'question': "Question 1",
                'answer': 'Some answer'
            },
            format='json'
        )

        self.assertEqual(error_response_2.status_code, 400)
        self.assertIn('question_index must be between', error_response_2.data['error'])

        # Try to submit empty answer
        error_response_3 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 0,
                'question': "Question 1",
                'answer': ''
            },
            format='json'
        )

        self.assertEqual(error_response_3.status_code, 400)
        self.assertIn('answer is required', error_response_3.data['error'])

    def test_interview_flow_with_existing_session(self):
        """Test requesting questions when session already exists"""
        # Create first session directly
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["Question 1", "Question 2", "Question 3"]
        )

        # Request questions should return existing session
        response_1 = self.client.post(
            '/api/v1/get-questions/',
            data={'doc_id': str(self.doc_id)},
            format='json'
        )

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_1.data['interview_questions'], ["Question 1", "Question 2", "Question 3"])

        # Second request for same doc_id should return same session
        response_2 = self.client.post(
            '/api/v1/get-questions/',
            data={'doc_id': str(self.doc_id)},
            format='json'
        )

        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_2.data['interview_questions'], ["Question 1", "Question 2", "Question 3"])

        # Verify only one session exists
        self.assertEqual(InterviewSession.objects.filter(doc_id=self.doc_id).count(), 1)

    def test_interview_flow_invalid_doc_id(self):
        """Test interview flow with invalid doc_id"""
        invalid_doc_id = str(uuid.uuid4())

        # Try to get questions with invalid doc_id - this should fail since no resume exists
        response = self.client.post(
            '/api/v1/get-questions/',
            data={'doc_id': invalid_doc_id},
            format='json'
        )

        self.assertEqual(response.status_code, 404)

        # Try to submit answer with invalid doc_id
        response_2 = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': invalid_doc_id,
                'question_index': 0,
                'question': 'Some question',
                'answer': 'Some answer'
            },
            format='json'
        )

        self.assertEqual(response_2.status_code, 404)
        self.assertEqual(response_2.data['error'], 'Interview session not found')

    def test_interview_session_resumption(self):
        """Test that interview can be resumed after partial completion"""
        # Create session directly with dummy questions and one answer
        session = InterviewSession.objects.create(
            resume=self.resume,
            doc_id=self.doc_id,
            questions=["Question 1", "Question 2", "Question 3"],
            answers=["Answer 1", None, None]
        )

        # Continue answering from where left off (question 2)
        response = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 1,
                'question': "Question 2",
                'answer': 'Answer 2'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['progress'], '2/3')
        self.assertFalse(response.data['is_completed'])

        # Complete the interview
        response = self.client.post(
            '/api/v1/submit-answer/',
            data={
                'doc_id': str(self.doc_id),
                'question_index': 2,
                'question': "Question 3",
                'answer': 'Answer 3'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['progress'], '3/3')
        self.assertTrue(response.data['is_completed'])

        session.refresh_from_db()
        self.assertEqual(len(session.answers), 3)
        self.assertEqual(session.answers[0], 'Answer 1')
        self.assertEqual(session.answers[1], 'Answer 2')
        self.assertEqual(session.answers[2], 'Answer 3')

    def test_feedback_endpoint_after_completion(self):
        """Test accessing feedback endpoint after completing interview"""
        # Test feedback endpoint (currently placeholder)
        response = self.client.get(
            '/api/v1/feedback/',
            {'doc_id': str(self.doc_id)}
        )

        # Current implementation returns 404 as placeholder
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'No feedback questions found')

        # Test with invalid doc_id
        response_2 = self.client.get(
            '/api/v1/feedback/',
            {'doc_id': str(uuid.uuid4())}
        )

        self.assertEqual(response_2.status_code, 404)
        self.assertEqual(response_2.data['error'], 'Resume not found')
