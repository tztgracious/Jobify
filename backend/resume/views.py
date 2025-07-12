import os
import uuid
import logging

import requests
from django.conf import settings
from django.http import JsonResponse
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .utils import grammar_check, get_keywords_using_openai, check_file_size_with_message
from .models import Resume
from accounts.decorators import deprecated_api

logger = logging.getLogger(__name__)


def get_resume_by_doc_id(doc_id):
    """
    Helper function to retrieve a resume by its doc_id.
    Returns the Resume object or None if not found.
    """
    try:
        return Resume.objects.get(id=doc_id)
    except Resume.DoesNotExist:
        return None


@api_view(['POST'])
def upload_resume(request):
    """
    Upload a PDF resume file and return a doc_id for future operations.
    Validates file size (max 5MB) and file type (PDF only).
    """
    file = request.FILES.get('file')
    if not file:
        logger.warning("Upload attempt with no file provided")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "No file uploaded"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check file type
    if not file.content_type == 'application/pdf':
        logger.warning(f"Upload attempt with invalid file type: {file.content_type}, filename: {file.name}")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "Not a PDF file."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check file size (max 5MB)
    is_valid_size, size_error_msg = check_file_size_with_message(file, max_size_mb=5)
    if not is_valid_size:
        logger.warning(f"Upload attempt with oversized file: {file.size} bytes, filename: {file.name}")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "File too big."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generate doc_id
    doc_id = str(uuid.uuid4())
    filename = f"{doc_id}.pdf"
    save_path = os.path.join(settings.MEDIA_ROOT, 'resumes', filename)

    # Make sure the directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Save file to disk
    try:
        with open(save_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    except IOError as e:
        logger.error(f"Failed to save resume file: {str(e)}, attempted path: {save_path}")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": f"Failed to save file: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Store file metadata in database
    relative_path = f"resumes/{filename}"
    resume = Resume.objects.create(
        id=doc_id,
        local_path=relative_path
    )

    # Log successful upload
    logger.info(f"Resume uploaded successfully: doc_id={doc_id}, filename={filename}, file_size={file.size} bytes")

    return Response({
        "doc_id": doc_id,
        "valid_file": True,
        "error_msg": None
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "Debug endpoint disabled in production"}, status=403)

    sample_text = "My name is Alice and I have 3 years experience in machine learning."

    # run your functions
    keywords = get_keywords_using_openai(sample_text)
    grammar_result = grammar_check(sample_text)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")
    return JsonResponse({
        "DEBUG": settings.DEBUG,
        "DATABASES": settings.DB_ENGINE,
        "KEYS": {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "LANGUAGETOOL_API_KEY": os.getenv("LANGUAGETOOL_API_KEY"),
            "EXAMPLE_KEY": os.getenv("EXAMPLE_KEY")
        },
    }, status=HTTP_200_OK)


@api_view(['POST'])
@deprecated_api(
    message="The parse-resume endpoint is deprecated",
    new_endpoint="/api/v1/upload-resume/"
)
def parse_resume(request):
    """
    DEPRECATED: This endpoint is deprecated. Use /api/v1/upload-resume/ instead.
    """
    pass  # The decorator handles the response
