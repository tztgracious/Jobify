import logging
import os
import threading
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Resume
from .utils import check_file_size_with_message, parse_resume, get_resume_by_doc_id

logger = logging.getLogger(__name__)


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
    # relative_path = f"resumes/{filename}"
    resume = Resume.objects.create(
        id=doc_id,
        local_path=save_path
    )

    # Log successful upload
    logger.info(f"Resume uploaded successfully: doc_id={doc_id}, filename={filename}, file_size={file.size} bytes")
    print(f"filepath: {save_path}")
    threading.Thread(target=parse_resume, args=(resume.id,)).start()
    return Response({
        "doc_id": doc_id,
        "valid_file": True,
        "error_msg": None
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def get_keywords(request):
    """
    Retrieve keywords for a given doc_id from multipart form data.
    Returns processing status and keywords according to API specification.
    """
    doc_id = request.data.get('doc_id')
    if not doc_id:
        logger.warning("get_keywords called without doc_id")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "doc_id is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Keywords requested for non-existent doc_id: {doc_id}")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "Resume not found"
        }, status=status.HTTP_404_NOT_FOUND)

    # Check processing status
    if resume.status == Resume.Status.FAILED:
        logger.error(f"Resume processing failed for doc_id: {doc_id}, restarted")
        threading.Thread(target=parse_resume, args=(resume.id,)).start()
        return Response({
            "finished": False,
            "keywords": [],
            "error": "Resume processing failed. Trying again."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif resume.status == Resume.Status.PROCESSING:
        return Response({
            "finished": False,
            "keywords": [],
            "error": ""
        }, status=status.HTTP_200_OK)
    elif resume.status == Resume.Status.COMPLETE:
        return Response({
            "finished": True,
            "keywords": resume.keywords or [],
            "error": ""
        }, status=status.HTTP_200_OK)

    # Unknown status
    return Response({
        "finished": False,
        "keywords": [],
        "error": "Unknown resume status"
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def target_job(request):
    """
    Save user's target job preferences.
    Accepts JSON data with title, location, salary_range, and tags.
    """
    # Extract data from request
    doc_id = request.data.get('doc_id')
    title = request.data.get('title')
    # location = request.data.get('location')
    # salary_range = request.data.get('salary_range')
    # tags = request.data.get('tags', [])

    # Validate required fields
    if not doc_id or not title or not title.strip():
        logger.warning(f"Target job called without required fields")
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Target job requested for non-existent doc_id: {doc_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    resume.target_job = title
    resume.save()
    return Response({
        "doc_id": doc_id,
        "message": "Target job saved successfully"
    })
