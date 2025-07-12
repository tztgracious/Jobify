import os
import uuid

import requests
from django.conf import settings
from django.http import JsonResponse
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .utils import grammar_check, get_keywords_using_openai, check_file_size_with_message
from accounts.decorators import deprecated_api


@api_view(['POST'])
def upload_resume(request):
    """
    Upload a PDF resume file and return a doc_id for future operations.
    Validates file size (max 5MB) and file type (PDF only).
    """
    file = request.FILES.get('file')
    if not file:
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "No file uploaded"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check file type
    if not file.content_type == 'application/pdf':
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "Not a PDF file."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check file size (max 5MB)
    is_valid_size, size_error_msg = check_file_size_with_message(file, max_size_mb=5)
    if not is_valid_size:
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "File too big."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generate doc_id
    doc_id = str(uuid.uuid4())

    # TODO: Store the file and doc_id in database/storage for later retrieval
    # For now, just return success response

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
