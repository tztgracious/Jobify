import os
import threading
import uuid
import shutil
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from interview.models.interview_session import InterviewSession
from interview.clients.llm_client import InterviewLLMClient
from .clients.llama_client import LlamaClient
from .clients.grammar_client import GrammarClient
from jobify_backend.logger import logger

class ResumeService:
    """
    Service layer for managing resume processing and business logic.
    """

    @staticmethod
    def get_session_by_id(session_id: str) -> Optional[InterviewSession]:
        """Retrieve an interview session or return None."""
        try:
            return InterviewSession.objects.filter(id=session_id).first()
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    @staticmethod
    def save_resume_file(file, session_id: str) -> str:
        """
        Saves the uploaded resume file to the media directory.
        Returns the absolute path to the saved file.
        """
        filename = f"{session_id}.pdf"
        save_path = os.path.join(settings.MEDIA_ROOT, "resumes", filename)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, "wb") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        logger.info(f"Resume file saved to: {save_path}")
        return save_path

    @staticmethod
    def create_interview_session(session_id: str, file_path: str) -> InterviewSession:
        """
        Creates an InterviewSession record for the uploaded resume.
        """
        session = InterviewSession.objects.create(
            id=session_id,
            resume_local_path=file_path,
            resume_status=InterviewSession.Status.PROCESSING
        )
        logger.info(f"Interview session created: {session_id}")
        return session

    @staticmethod
    def trigger_resume_parsing(session_id: str) -> None:
        """
        Starts the background thread for resume parsing.
        """
        threading.Thread(
            target=ResumeService.process_resume_background,
            args=(session_id,)
        ).start()
        logger.info(f"Resume parsing thread started for session: {session_id}")

    @staticmethod
    def process_resume_background(session_id: str) -> None:
        """
        Background task to parse resume, extract keywords, and check grammar.
        """
        try:
            session = InterviewSession.objects.get(id=session_id)
            llama_client = LlamaClient()
            grammar_client = GrammarClient()
            llm_client = InterviewLLMClient()

            # 1. Parse PDF
            logger.info(f"Parsing PDF for session {session_id}")
            parsed_text = llama_client.parse_pdf(session.resume_local_path)
            
            if not parsed_text:
                raise Exception("LlamaParse returned empty text")

            # 2. Extract Keywords
            logger.info(f"Extracting keywords for session {session_id}")
            keyword_prompt = f"""You are an expert resume analyzer.
            Extract **up to 10 distinct English keywords** (lowercase) that best represent 
            the skills and technologies in this resume text.
            Output ONLY a JSON array of strings.
            
            Resume text:
            \"\"\"
            {parsed_text}
            \"\"\"
            """
            keywords = llm_client.complete(keyword_prompt)
            if not isinstance(keywords, list):
                # Attempt to extract if it's nested or returned differently
                if isinstance(keywords, dict) and "keywords" in keywords:
                    keywords = keywords["keywords"]
                else:
                    logger.warning(f"Unexpected keyword format: {keywords}")
                    keywords = []

            # 3. Grammar Check
            logger.info(f"Checking grammar for session {session_id}")
            grammar_results = grammar_client.check_grammar(parsed_text)

            # 4. Update Session
            session.keywords = keywords
            session.grammar_results = grammar_results
            session.resume_status = InterviewSession.Status.COMPLETE
            session.save()
            logger.info(f"Resume processing completed for session {session_id}")

        except Exception as e:
            logger.error(f"Error in background resume processing for {session_id}: {e}")
            try:
                session = InterviewSession.objects.get(id=session_id)
                session.resume_status = InterviewSession.Status.FAILED
                session.save()
            except:
                pass

    @staticmethod
    def set_target_job(session_id: str, title: str, answer_type: str) -> bool:
        """
        Updates the target job title and answer type for a session.
        """
        from interview.utils import get_questions_using_openai
        try:
            session = InterviewSession.objects.get(id=session_id)
            session.target_job = title
            session.answer_type = answer_type
            session.save()
            logger.info(f"Target job updated for session {session_id}: {title} ({answer_type})")
            
            # Trigger question generation
            threading.Thread(target=get_questions_using_openai, args=(session,)).start()
            logger.info(f"Question generation triggered for session {session_id}")
            
            return True
        except InterviewSession.DoesNotExist:
            logger.warning(f"Failed to set target job: session {session_id} not found")
            return False

    @staticmethod
    def cleanup_all_resumes() -> Dict[str, Any]:
        """
        Destructive operation to remove ALL resumes and database records.
        """
        media_dir = os.path.join(settings.MEDIA_ROOT, "resumes")
        results = {
            "total_resumes_before": InterviewSession.objects.count(),
            "files_removed": 0,
            "files_failed": 0,
            "db_records_removed": 0,
            "errors": []
        }

        # Step 1: Remove files
        if os.path.exists(media_dir):
            for filename in os.listdir(media_dir):
                if filename.endswith(".pdf"):
                    file_path = os.path.join(media_dir, filename)
                    try:
                        os.remove(file_path)
                        results["files_removed"] += 1
                    except Exception as e:
                        results["files_failed"] += 1
                        results["errors"].append(f"File error {filename}: {str(e)}")

        # Step 2: Clear DB
        try:
            db_removed, _ = InterviewSession.objects.all().delete()
            results["db_records_removed"] = db_removed
        except Exception as e:
            results["errors"].append(f"Database error: {str(e)}")

        return results
