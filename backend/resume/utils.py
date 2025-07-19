import json
import logging
import os
import re

import requests
from django.core.exceptions import ValidationError
from llama_cloud_services import LlamaParse

from resume.models import Resume

logger = logging.getLogger(__name__)


def grammar_check(text: str) -> dict:
    response = requests.post(
        "https://api.languagetool.org/v2/check",
        data={"text": text, "language": "en-US"}
    )
    return response.json()


def get_resume_by_doc_id(doc_id):
    """
    Helper function to retrieve a resume by its doc_id.
    Returns the Resume object or None if not found or invalid UUID.
    """
    try:
        return Resume.objects.get(id=doc_id)
    except (Resume.DoesNotExist, ValueError, ValidationError):
        # ValueError is raised when doc_id is not a valid UUID
        # ValidationError is raised by Django's UUID validation
        return None


def parse_resume(doc_id: str):
    try:
        # Get the resume from database
        resume = Resume.objects.get(id=doc_id)
        resume_path = resume.local_path

        # Parse the PDF and extract text
        text = llamaparse_pdf_v1(resume_path)

        # Extract keywords using OpenAI
        keywords = get_keywords_using_openai(text)

        # Store keywords in database and mark as processed
        resume.keywords = keywords
        resume.status = Resume.Status.COMPLETE
        resume.save()

        print(f"Successfully processed resume {doc_id}")
        print(f"Keywords extracted: {keywords}")
        print(f"Resume status: {resume.status}")

    except Resume.DoesNotExist:
        print(f"Error: Resume with id {doc_id} not found")
        return False
    except Exception as e:
        print(f"Error parsing resume {doc_id}: {str(e)}")
        # Mark as failed processing (still False but we could add a failed status later)
        try:
            resume = Resume.objects.get(id=doc_id)
            resume.status = Resume.Status.FAILED
            resume.save()
        except Exception as e:
            logger.error(f"Error marking resume {doc_id} as failed: {str(e)}")
            pass
        return False

    return True


# TODO: parse the file with llama parse first and write a proper prompt
def get_keywords_using_openai(text) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPEN_ROUTER_API_KEY')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "jobify.com",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "Jobify",  # Optional. Site title for rankings on openrouter.ai.
        },
        data=json.dumps({
            "model": "openai/gpt-4o",
            "messages": [
                {"role": "user", "content": f"""You are an expert resume analyzer.

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
    """}
            ]
        })
    )
    response_text = response.json()["choices"][0]["message"]["content"]
    match = re.search(r'\[.*?\]', response_text, re.DOTALL)
    try:
        keywords = json.loads(match[0])
    except json.JSONDecodeError:
        print(f"Error parsing keywords: {response_text}")
    return keywords


def get_file_size_mb(file_size_bytes):
    """Convert bytes to MB for user display"""
    return round(file_size_bytes / (1024 * 1024), 2)


# TODO: get better error message. Rerun a Response object if invalid
def check_file_size_with_message(file, max_size_mb=5):
    """Check file size with user-friendly message"""
    max_size_bytes = max_size_mb * 1024 * 1024

    if file.size > max_size_bytes:
        current_size = get_file_size_mb(file.size)
        return False, f"File size ({current_size} MB) exceeds limit ({max_size_mb} MB)"

    return True, None


def llamaparse_pdf_v1(resume_path) -> str:
    # Handle relative path by combining with MEDIA_ROOT
    from django.conf import settings
    import os

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
    for page in result.pages:
        print(page.text)
    #     print(page.md)
    #     print(page.images)
    #     print(page.layout)
    #     print(page.structuredData)
    return result.pages[0].text
