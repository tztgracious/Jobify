import json
import os
import re

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from interview.models import InterviewSession
from jobify_backend.logger import logger
from llama_cloud_services import LlamaParse


def get_session_by_id(session_id: str):
    """
    Retrieve an interview session by id.
    Returns None if not found or if id is invalid.
    """
    try:
        return InterviewSession.objects.get(id=session_id)
    except (InterviewSession.DoesNotExist, ValueError, ValidationError):
        logger.error(f"Error retrieving interview session with id {session_id}")
        return None


def grammar_check(text: str) -> dict:
    response = requests.post(
        "https://api.languagetool.org/v2/check",
        data={"text": text, "language": "en-US"},
    )
    return response.json()


def parse_resume(session_id: str):
    """
    Parse a résumé asynchronously and update the database.
    """
    try:
        session = InterviewSession.objects.get(id=session_id)

        # Try to parse the résumé
        try:
            logger.info(f"Starting resume parsing for doc_id: {session_id}")

            # Parse the résumé using LlamaParse
            parsed_text = llamaparse_pdf_v1(session.resume_local_path)

            # Generate keywords from parsed text
            keywords = get_keywords_using_openai(parsed_text)

            # Run grammar check
            logger.info(f"Starting grammar check for doc_id: {session_id}")
            grammar_results = grammar_check(parsed_text)

            # Update resume with results
            session.keywords = keywords
            session.grammar_results = grammar_results
            session.resume_status = InterviewSession.Status.COMPLETE
            session.save()

        except Exception as grammar_error:
            logger.error(
                f"Grammar check failed for doc_id: {session_id}, error: {grammar_error}"
            )
            # Still mark as complete even if the grammar check fails
            session.resume_status = InterviewSession.Status.COMPLETE
            session.save()

    except InterviewSession.DoesNotExist:
        logger.error(f"Interview session {session_id} not found in database")
        return
    except Exception as e:
        logger.error(f"Error parsing resume {session_id}: {str(e)}")
        # Mark resume as failed
        try:
            session = InterviewSession.objects.get(id=session_id)
            session.resume_status = InterviewSession.Status.FAILED
            session.save()
        except Exception as e:
            logger.error(f"Error marking resume {session_id} as failed: {str(e)}")


def get_keywords_using_openai(text) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPEN_ROUTER_API_KEY')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "jobify.com",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "Jobify",  # Optional. Site title for rankings on openrouter.ai.
        },
        data=json.dumps(
            {
                "model": "openai/gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""You are an expert resume analyzer.

    Your task is to extract **up to 10 distinct English keywords** that best represent the skills, technologies, and important qualifications found in the following resume text.

    Please follow these strict rules:

    1. Ensure all keywords are in lowercase.
    2. Remove duplicates or near-duplicates (e.g. "python" vs "Python3" → just "python").
    3. Only include concise keywords, not full sentences.
    4. Output ONLY a JSON array of strings. Do not include any explanation, notes, or additional text.

    Here is the resume text:
    \"\"\"
    {text}
    \"\"\"
    """,
                    }
                ],
            }
        ),
    )
    response_text = response.json()["choices"][0]["message"]["content"]
    match = re.search(r"\[.*?\]", response_text, re.DOTALL)
    try:
        keywords = json.loads(match[0])
    except json.JSONDecodeError:
        print(f"Error parsing keywords: {response_text}")
        return ""
    return keywords


def get_file_size_mb(file_size_bytes):
    """Convert bytes to MB for user display"""
    return round(file_size_bytes / (1024 * 1024), 2)


def check_file_size_with_message(file, max_size_mb=5):
    """Check file size."""
    max_size_bytes = max_size_mb * 1024 * 1024

    if file.size > max_size_bytes:
        current_size = get_file_size_mb(file.size)
        return False, f"File size ({current_size} MB) exceeds limit ({max_size_mb} MB)"

    return True, None


def llamaparse_pdf_v1(resume_path) -> str:
    if not os.path.isabs(resume_path):
        full_path = os.path.join(settings.MEDIA_ROOT, resume_path)
    else:
        full_path = resume_path

    parser = LlamaParse(
        api_key=os.getenv("LLAMA_PARSE_API_KEY"),
        num_workers=4,
        verbose=True,
        language="en",
    )

    # sync
    result = parser.parse(full_path)

    # get the llama-index text documents
    text_documents = result.get_text_documents(split_by_page=False)

    # access the raw job result
    # Items will vary based on the parser configuration
    # for page in result.pages:
    #     print(page.text)
    #     print(page.md)
    #     print(page.images)
    #     print(page.layout)
    #     print(page.structuredData)
    return result.pages[0].text
