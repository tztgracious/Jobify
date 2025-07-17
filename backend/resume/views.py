import logging
import os
import threading
import uuid
from logging.handlers import RotatingFileHandler

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Resume
from .utils import check_file_size_with_message, parse_resume, get_resume_by_doc_id

# Configure custom logger for jobify.log
def setup_jobify_logger():
    """Setup custom logger that writes to jobify.log file"""
    logger = logging.getLogger('jobify')
    
    # Prevent duplicate handlers if this function is called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create rotating file handler (max 10MB, keep 5 backup files)
    log_file = os.path.join(log_dir, 'jobify.log')
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Create formatter with detailed information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger

# Initialize custom logger
logger = setup_jobify_logger()


@api_view(['POST'])
def upload_resume(request):
    """
    Upload a PDF resume file and return a doc_id for future operations.
    Validates file size (max 5MB) and file type (PDF only).
    """
    logger.info("=== UPLOAD RESUME REQUEST STARTED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    file = request.FILES.get('file')
    if not file:
        logger.warning("Upload attempt with no file provided")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - NO FILE ===")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "No file uploaded"
        }, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Received file: {file.name}, size: {file.size} bytes, content_type: {file.content_type}")

    # Check file type
    if not file.content_type == 'application/pdf':
        logger.warning(f"Upload attempt with invalid file type: {file.content_type}, filename: {file.name}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - INVALID FILE TYPE ===")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "Not a PDF file."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check file size (max 5MB)
    is_valid_size, size_error_msg = check_file_size_with_message(file, max_size_mb=5)
    if not is_valid_size:
        logger.warning(f"Upload attempt with oversized file: {file.size} bytes, filename: {file.name}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - FILE TOO BIG ===")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": "File too big."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generate doc_id
    doc_id = str(uuid.uuid4())
    filename = f"{doc_id}.pdf"
    save_path = os.path.join(settings.MEDIA_ROOT, 'resumes', filename)

    logger.info(f"Generated doc_id: {doc_id}")
    logger.info(f"Saving file to: {save_path}")

    # Make sure the directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Save file to disk
    try:
        with open(save_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        logger.info(f"File saved successfully to: {save_path}")
    except IOError as e:
        logger.error(f"Failed to save resume file: {str(e)}, attempted path: {save_path}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - IO ERROR ===")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": f"Failed to save file: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Store file metadata in database
    try:
        resume = Resume.objects.create(
            id=doc_id,
            local_path=save_path
        )
        logger.info(f"Resume record created in database: {doc_id}")
    except Exception as e:
        logger.error(f"Failed to create resume record in database: {str(e)}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - DATABASE ERROR ===")
        return Response({
            "doc_id": None,
            "valid_file": False,
            "error_msg": f"Database error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Log successful upload
    logger.info(f"Resume uploaded successfully: doc_id={doc_id}, filename={filename}, file_size={file.size} bytes")
    
    # Start background parsing
    try:
        threading.Thread(target=parse_resume, args=(resume.id,)).start()
        logger.info(f"Background parsing thread started for doc_id: {doc_id}")
    except Exception as e:
        logger.error(f"Failed to start background parsing thread: {str(e)}")
        # Don't fail the request, just log the error
    
    logger.info("=== UPLOAD RESUME REQUEST COMPLETED SUCCESSFULLY ===")
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
    logger.info("=== GET KEYWORDS REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")
    
    doc_id = request.data.get('doc_id')
    if not doc_id:
        logger.warning("get_keywords called without doc_id")
        logger.info("=== GET KEYWORDS REQUEST FAILED - NO DOC_ID ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "doc_id is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Looking up resume for doc_id: {doc_id}")
    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Keywords requested for non-existent doc_id: {doc_id}")
        logger.info("=== GET KEYWORDS REQUEST FAILED - RESUME NOT FOUND ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "Resume not found"
        }, status=status.HTTP_404_NOT_FOUND)

    logger.info(f"Resume found: {doc_id}, status: {resume.status}")

    # Check processing status
    if resume.status == Resume.Status.FAILED:
        logger.error(f"Resume processing failed for doc_id: {doc_id}, restarting parse")
        threading.Thread(target=parse_resume, args=(resume.id,)).start()
        logger.info("=== GET KEYWORDS REQUEST - PROCESSING FAILED, RESTARTING ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "Resume processing failed. Trying again."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif resume.status == Resume.Status.PROCESSING:
        logger.info(f"Resume still processing for doc_id: {doc_id}")
        logger.info("=== GET KEYWORDS REQUEST - STILL PROCESSING ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": ""
        }, status=status.HTTP_200_OK)
    elif resume.status == Resume.Status.COMPLETE:
        keywords = resume.keywords or []
        logger.info(f"Resume processing complete for doc_id: {doc_id}, keywords count: {len(keywords)}")
        logger.info(f"Keywords: {keywords}")
        logger.info("=== GET KEYWORDS REQUEST COMPLETED SUCCESSFULLY ===")
        return Response({
            "finished": True,
            "keywords": keywords,
            "error": ""
        }, status=status.HTTP_200_OK)

    # Unknown status
    logger.error(f"Unknown resume status: {resume.status} for doc_id: {doc_id}")
    logger.info("=== GET KEYWORDS REQUEST FAILED - UNKNOWN STATUS ===")
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
    logger.info("=== TARGET JOB REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")
    
    # Extract data from request
    doc_id = request.data.get('doc_id')
    title = request.data.get('title')
    # location = request.data.get('location')
    # salary_range = request.data.get('salary_range')
    # tags = request.data.get('tags', [])

    logger.info(f"Received doc_id: {doc_id}, title: {title}")

    # Validate required fields
    if not doc_id or not title or not title.strip():
        logger.warning(f"Target job called without required fields - doc_id: {doc_id}, title: {title}")
        logger.info("=== TARGET JOB REQUEST FAILED - MISSING FIELDS ===")
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Target job requested for non-existent doc_id: {doc_id}")
        logger.info("=== TARGET JOB REQUEST FAILED - RESUME NOT FOUND ===")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Save target job
    try:
        old_target_job = resume.target_job
        resume.target_job = title
        resume.save()
        logger.info(f"Target job updated for doc_id: {doc_id}, old: '{old_target_job}', new: '{title}'")
        logger.info("=== TARGET JOB REQUEST COMPLETED SUCCESSFULLY ===")
    except Exception as e:
        logger.error(f"Failed to save target job for doc_id: {doc_id}, error: {str(e)}")
        logger.info("=== TARGET JOB REQUEST FAILED - DATABASE ERROR ===")
        return Response({"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        "doc_id": doc_id,
        "message": "Target job saved successfully"
    })
