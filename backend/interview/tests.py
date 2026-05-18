import uuid
from django.test import TestCase
from .models.interview_session import InterviewSession
from .services import InterviewService

class InterviewServiceTest(TestCase):
    def setUp(self):
        self.session_id = uuid.uuid4()
        self.session = InterviewSession.objects.create(
            id=self.session_id,
            target_job="Software Engineer",
            keywords=["Python", "Django"],
            resume_status=InterviewSession.Status.COMPLETE,
            question_status=InterviewSession.Status.COMPLETE,
            tech_questions=["What is a decorator?"],
            questions=["Tell me about yourself."]
        )
        # Create relational Question models for testing
        from .models.question import Question
        Question.objects.create(session=self.session, text="What is a decorator?", is_technical=True, index=0)
        Question.objects.create(session=self.session, text="Tell me about yourself.", is_technical=False, index=0)

    def test_get_session_by_id(self):
        retrieved = InterviewService.get_session_by_id(str(self.session_id))
        self.assertEqual(retrieved.id, self.session_id)

    def test_check_session_readiness_complete(self):
        is_ready, message, data = InterviewService.check_session_readiness(self.session)
        self.assertTrue(is_ready)
        self.assertEqual(len(data["tech_questions"]), 1)

    def test_check_session_readiness_processing(self):
        self.session.question_status = InterviewSession.Status.PROCESSING
        self.session.save()
        is_ready, message, data = InterviewService.check_session_readiness(self.session)
        self.assertFalse(is_ready)
        self.assertIn("still being generated", message)

    def test_validate_question_submission_success(self):
        is_valid, error = InterviewService.validate_question_submission(
            self.session, 0, "What is a decorator?", is_tech=True
        )
        self.assertTrue(is_valid)

    def test_validate_question_submission_mismatch(self):
        is_valid, error = InterviewService.validate_question_submission(
            self.session, 0, "Wrong question", is_tech=True
        )
        self.assertFalse(is_valid)
        self.assertIn("does not match", error)

    def test_update_answer_tech(self):
        InterviewService.update_answer(self.session, 0, "A decorator is a function.", is_tech=True)
        self.session.refresh_from_db()
        self.assertEqual(self.session.tech_answers[0], "A decorator is a function.")
        # Verify relational Answer model
        from .models.answer import Answer
        answer = Answer.objects.get(question__session=self.session, question__is_technical=True, question__index=0)
        self.assertEqual(answer.text, "A decorator is a function.")

    def test_check_and_update_completion_status(self):
        # Answer all questions
        InterviewService.update_answer(self.session, 0, "I am a dev.", is_tech=False)
        InterviewService.update_answer(self.session, 0, "Deco", is_tech=True)
        
        is_completed = InterviewService.check_and_update_completion_status(self.session)
        self.assertTrue(is_completed)
        self.assertTrue(self.session.is_completed)
        
        from .models.answer import Answer
        self.assertEqual(Answer.objects.filter(question__session=self.session).count(), 2)
