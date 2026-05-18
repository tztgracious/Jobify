import threading
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from .models.interview_session import InterviewSession
from .models.question import Question
from .models.answer import Answer
from .models.feedback import Feedback
from .utils import get_feedback_using_openai_multi_agent
from jobify_backend.logger import logger

class InterviewService:
    """
    Service layer for managing interview sessions and business logic.
    Decouples core logic from HTTP request handling.
    """

    @staticmethod
    def get_session_by_id(session_id: str) -> Optional[InterviewSession]:
        """Retrieve an interview session or return None."""
        try:
            return InterviewSession.objects.prefetch_related('related_questions__answer').filter(id=session_id).first()
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    @staticmethod
    def check_session_readiness(session: InterviewSession) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if a session is ready for question retrieval.
        Returns (is_ready, message, data).
        """
        if session.resume_status != InterviewSession.Status.COMPLETE:
            return False, "Resume is still being processed. Please wait.", {
                "finished": False,
                "tech_questions": [],
                "interview_questions": []
            }

        if session.question_status != InterviewSession.Status.COMPLETE:
            return False, "Questions are still being generated. Please wait.", {
                "finished": False,
                "tech_questions": [],
                "interview_questions": []
            }

        questions = session.related_questions.all()
        tech_questions = [q.text for q in questions if q.is_technical]
        gen_questions = [q.text for q in questions if not q.is_technical]

        return True, "Questions retrieved successfully", {
            "finished": True,
            "tech_questions": tech_questions,
            "interview_questions": gen_questions
        }

    @staticmethod
    def validate_question_submission(session: InterviewSession, index: int, question_text: str, is_tech: bool = False) -> Tuple[bool, str]:
        """Validate that the question index and text match the session data."""
        try:
            question = session.related_questions.get(index=index, is_technical=is_tech)
            if question.text.strip() != question_text.strip():
                return False, "Question text does not match the question at the specified index"
            return True, ""
        except Question.DoesNotExist:
            return False, f"Question at index {index} not found for this session"

    @staticmethod
    def update_answer(session: InterviewSession, index: int, answer_text: str, is_tech: bool = False) -> None:
        """Update the answer for a specific question using normalized models."""
        try:
            question = session.related_questions.get(index=index, is_technical=is_tech)
            answer, created = Answer.objects.update_or_create(
                question=question,
                defaults={'text': answer_text, 'is_video': False}
            )
            logger.info(f"{'Created' if created else 'Updated'} answer for question {question.id}")
            
            # Legacy support (deprecated)
            if is_tech:
                answers = session.tech_answers or []
                while len(answers) <= index: answers.append("")
                answers[index] = answer_text
                session.tech_answers = answers
            else:
                answers = session.answers or []
                while len(answers) <= index: answers.append("")
                answers[index] = answer_text
                session.answers = answers
            session.save()
            
        except Question.DoesNotExist:
            logger.error(f"Failed to update answer: Question at index {index} (tech={is_tech}) not found")

    @staticmethod
    def check_and_update_completion_status(session: InterviewSession) -> bool:
        """Check if all questions have been answered using normalized models."""
        total_questions = session.related_questions.count()
        if total_questions == 0:
            return False
            
        answered_questions = session.related_questions.filter(answer__isnull=False).count()
        
        if answered_questions == total_questions:
            if not session.is_completed:
                session.is_completed = True
                session.save()
            return True
        return False

    @staticmethod
    def trigger_feedback_generation(session: InterviewSession) -> None:
        """Trigger feedback generation in a background thread."""
        if session.feedback_status == InterviewSession.Status.PENDING:
            threading.Thread(
                target=InterviewService.generate_feedback_background, 
                args=(session.id,)
            ).start()
            logger.info(f"Feedback generation thread started for session {session.id}")

    @staticmethod
    def generate_feedback_background(session_id: str) -> None:
        """Background task to generate feedback."""
        session = InterviewService.get_session_by_id(session_id)
        if not session:
            logger.error(f"Background feedback task failed: session {session_id} not found")
            return

        try:
            session.feedback_started = timezone.now()
            session.feedback_status = InterviewSession.Status.PROCESSING
            session.save()

            logger.info(f"Retrieving feedback for session {session_id}")
            # The multi-agent feedback logic will need to be updated to populate Feedback models
            feedback_data = get_feedback_using_openai_multi_agent(session)
            
            if feedback_data:
                # feedback_data is currently a dict matching the old schema
                # We'll need a migration step or update the util to save to Feedback models
                session.feedback = feedback_data
                session.feedback_status = InterviewSession.Status.COMPLETE
            else:
                logger.warning(f"No feedback generated for session {session_id}")
                session.feedback_status = InterviewSession.Status.FAILED

            session.feedback_completed = timezone.now()
            session.save()
            logger.info(f"Feedback generation completed for session {session_id}")

        except Exception as e:
            logger.error(f"Error in background feedback generation for {session_id}: {e}")
            session.feedback_status = InterviewSession.Status.FAILED
            session.save()

    @staticmethod
    def cleanup_all_videos() -> Dict[str, Any]:
        """Destructive operation to remove ALL video files."""
        from django.conf import settings
        import os
        import shutil

        video_directories = [
            os.path.join(settings.MEDIA_ROOT, "videos"),
            os.path.join(settings.MEDIA_ROOT, "interview_videos"),
        ]
        
        results = {"deleted_files": 0, "deleted_directories": 0, "errors": []}

        for directory in video_directories:
            if not os.path.exists(directory): continue
            try:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            results["deleted_files"] += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            results["deleted_directories"] += 1
                    except Exception as e:
                        results["errors"].append(f"Error deleting {item_path}: {str(e)}")
            except Exception as e:
                results["errors"].append(f"Error accessing directory {directory}: {str(e)}")

        return results
