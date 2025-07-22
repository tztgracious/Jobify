import os
import threading
import time
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from interview.models import InterviewSession
from interview.utils import get_questions_using_openai
from jobify_backend.logger import logger
from .utils import check_file_size_with_message, parse_resume, get_session_by_id


@api_view(['POST'])
def upload_resume(request):
    """
    Upload a PDF resume file and return an id for future operations.
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
            "id": None,
            "valid_file": False,
            "error_msg": "No file uploaded"
        }, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Received file: {file.name}, size: {file.size} bytes, content_type: {file.content_type}")

    # Check file type
    if not file.content_type == 'application/pdf':
        logger.warning(f"Upload attempt with invalid file type: {file.content_type}, filename: {file.name}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - INVALID FILE TYPE ===")
        return Response({
            "id": None,
            "valid_file": False,
            "error_msg": "Not a PDF file."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check file size (max 5MB)
    is_valid_size, size_error_msg = check_file_size_with_message(file, max_size_mb=5)
    if not is_valid_size:
        logger.warning(f"Upload attempt with oversized file: {file.size} bytes, filename: {file.name}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - FILE TOO BIG ===")
        return Response({
            "id": None,
            "valid_file": False,
            "error_msg": "File too big."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generate id
    session_id = str(uuid.uuid4())
    filename = f"{session_id}.pdf"
    save_path = os.path.join(settings.MEDIA_ROOT, 'resumes', filename)

    logger.info(f"Generated id: {session_id}")
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
            "id": None,
            "valid_file": False,
            "error_msg": f"Failed to save file: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Store file metadata in database
    try:
        interview_session = InterviewSession.objects.create(
            id=session_id,
            resume_local_path=save_path
        )
        logger.info(f"Interview session record created in database: {session_id}")
    except Exception as e:
        logger.error(f"Failed to create resume record in database: {str(e)}")
        logger.info("=== UPLOAD RESUME REQUEST FAILED - DATABASE ERROR ===")
        return Response({
            "id": None,
            "valid_file": False,
            "error_msg": f"Database error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Log successful upload
    logger.info(f"Resume uploaded successfully: id={session_id}, filename={filename}, file_size={file.size} bytes")

    # Start background parsing
    try:
        threading.Thread(target=parse_resume, args=(interview_session.id,)).start()
        logger.info(f"Background parsing thread started for id: {session_id}")
    except Exception as e:
        logger.error(f"Failed to start background parsing thread: {str(e)}")
        # Don't fail the request, just log the error

    logger.info("=== UPLOAD RESUME REQUEST COMPLETED SUCCESSFULLY ===")
    return Response({
        "id": session_id,
        "valid_file": True,
        "error_msg": None
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def get_grammar_results(request):
    """
    Retrieve grammar check results for a given id.
    Returns processing status and grammar check results.
    """
    logger.info("=== GET GRAMMAR RESULTS REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")

    session_id = request.data.get('id')
    if not session_id:
        logger.warning("get_grammar_results called without id")
        logger.info("=== GET GRAMMAR RESULTS REQUEST FAILED - NO ID ===")
        return Response({
            "finished": False,
            "grammar_check": None,
            "error": "id is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    session = get_session_by_id(session_id)
    if not session:
        logger.warning(f"Grammar results requested for non-existent id: {session_id}")
        logger.info("=== GET GRAMMAR RESULTS REQUEST FAILED - RESUME NOT FOUND ===")
        return Response({
            "finished": False,
            "grammar_check": None,
            "error": "Resume not found"
        }, status=status.HTTP_404_NOT_FOUND)

    # Check processing status
    if session.resume_status == InterviewSession.Status.FAILED:
        logger.error(f"Resume processing failed for id: {session_id}, restarting parse")
        threading.Thread(target=parse_resume, args=(session.id,)).start()
        logger.info("=== GET GRAMMAR RESULTS REQUEST - PROCESSING FAILED, RESTARTING ===")
        return Response({
            "finished": False,
            "grammar_check": None,
            "error": "Resume processing failed. Trying again."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif session.resume_status == InterviewSession.Status.PROCESSING:
        logger.info(f"Resume still processing for id: {session_id}")
        logger.info("=== GET GRAMMAR RESULTS REQUEST - STILL PROCESSING ===")
        return Response({
            "finished": False,
            "grammar_check": None,
            "error": ""
        }, status=status.HTTP_200_OK)

    elif session.resume_status == InterviewSession.Status.COMPLETE:
        grammar_results = session.grammar_results or {}
        logger.info(f"Resume processing complete for id: {session_id}, grammar results count: {len(grammar_results)}")
        logger.info(f"Grammar results: {grammar_results}")
        logger.info("=== GET GRAMMAR RESULTS REQUEST COMPLETED SUCCESSFULLY ===")
        return Response({
            "finished": True,
            "grammar_check": grammar_results,
            "error": ""
        }, status=status.HTTP_200_OK)

    else:
        return Response({
            "finished": False,
            "grammar_check": None,
            "error": "Unknown session status"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_keywords(request):
    """
    Retrieve keywords for a given id from multipart form data.
    Returns processing status and keywords according to API specification.
    """
    logger.info("=== GET KEYWORDS REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")

    session_id = request.data.get('id')
    if not session_id:
        logger.warning("get_keywords called without id")
        logger.info("=== GET KEYWORDS REQUEST FAILED - NO ID ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "id is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Looking up resume for id: {session_id}")
    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Keywords requested for non-existent id: {session_id}")
        logger.info("=== GET KEYWORDS REQUEST FAILED - RESUME NOT FOUND ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "Resume not found"
        }, status=status.HTTP_404_NOT_FOUND)

    logger.info(f"Resume found: {session_id}, status: {resume.resume_status}")

    # Check processing status
    if resume.resume_status == InterviewSession.Status.FAILED:
        logger.error(f"Resume processing failed for id: {session_id}, restarting parse")
        threading.Thread(target=parse_resume, args=(resume.id,)).start()
        logger.info("=== GET KEYWORDS REQUEST - PROCESSING FAILED, RESTARTING ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": "Resume processing failed. Trying again."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif resume.resume_status == InterviewSession.Status.PROCESSING:
        logger.info(f"Resume still processing for id: {session_id}")
        logger.info("=== GET KEYWORDS REQUEST - STILL PROCESSING ===")
        return Response({
            "finished": False,
            "keywords": [],
            "error": ""
        }, status=status.HTTP_200_OK)
    elif resume.resume_status == InterviewSession.Status.COMPLETE:
        keywords = resume.keywords or []
        logger.info(f"Resume processing complete for id: {session_id}, keywords count: {len(keywords)}")
        logger.info(f"Keywords: {keywords}")
        logger.info("=== GET KEYWORDS REQUEST COMPLETED SUCCESSFULLY ===")
        return Response({
            "finished": True,
            "keywords": keywords,
            "error": ""
        }, status=status.HTTP_200_OK)

    # Unknown status
    logger.error(f"Unknown resume status: {resume.resume_status} for id: {session_id}")
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
    Accepts JSON data with:
    - id: The resume document ID
    - title: The target job title
    - answer_type: How the user will submit answers ('text' or 'video', defaults to 'text')
    """
    logger.info("=== TARGET JOB REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")

    # Extract data from request
    session_id = request.data.get('id')
    title = request.data.get('title')
    answer_type = request.data.get('answer_type', 'text')  # 'text' or 'video'

    logger.info(f"Received id: {session_id}, title: {title}, answer_type: {answer_type}")

    # Validate required fields
    if not session_id or not title or not title.strip():
        logger.warning(f"Target job called without required fields - id: {session_id}, title: {title}")
        logger.info("=== TARGET JOB REQUEST FAILED - MISSING FIELDS ===")
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate answer_type
    if answer_type not in ['text', 'video']:
        logger.warning(f"Invalid answer_type provided: {answer_type}")
        logger.info("=== TARGET JOB REQUEST FAILED - INVALID ANSWER TYPE ===")
        return Response({"error": "answer_type must be either 'text' or 'video'"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Target job requested for non-existent id: {session_id}")
        logger.info("=== TARGET JOB REQUEST FAILED - RESUME NOT FOUND ===")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Save target job
    resume.target_job = title
    resume.answer_type = answer_type
    resume.save()
    logger.info(f"Target job updated for id: {session_id}, new: '{title}', answer_type: '{answer_type}'")
    logger.info("=== TARGET JOB REQUEST COMPLETED SUCCESSFULLY ===")
    threading.Thread(target=get_questions_using_openai, args=(resume,)).start()
    return Response({
        "id": session_id,
        "message": "Target job and answer type saved successfully",
        "answer_type": answer_type
    })


@api_view(['POST'])
def remove_resume(request):
    """
    Remove a resume and its associated media file.
    Accepts id and removes both the database entry and the PDF file.
    """
    logger.info("=== REMOVE RESUME REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")

    id = request.data.get('id')
    if not id:
        logger.warning("remove_resume called without id")
        logger.info("=== REMOVE RESUME REQUEST FAILED - NO ID ===")
        return Response({
            "success": False,
            "error": "id is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Looking up resume for id: {id}")
    resume = get_session_by_id(id)
    if not resume:
        logger.warning(f"Remove resume requested for non-existent id: {id}")
        logger.info("=== REMOVE RESUME REQUEST FAILED - RESUME NOT FOUND ===")
        return Response({
            "success": False,
            "error": "Resume not found"
        }, status=status.HTTP_404_NOT_FOUND)

    # Get the file path before deleting the database entry
    file_path = resume.resume_local_path
    logger.info(f"Resume found: {id}, file_path: {file_path}")

    # Remove the database entry
    try:
        resume.delete()
        logger.info(f"Resume database entry deleted for id: {id}")
    except Exception as e:
        logger.error(f"Failed to delete resume database entry for id: {id}, error: {str(e)}")
        logger.info("=== REMOVE RESUME REQUEST FAILED - DATABASE ERROR ===")
        return Response({
            "success": False,
            "error": f"Database error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Remove the media file
    file_removed = False
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            file_removed = True
            logger.info(f"Media file removed: {file_path}")
        except Exception as e:
            logger.error(f"Failed to remove media file: {file_path}, error: {str(e)}")
            # Don't fail the request if file removal fails, as DB entry is already deleted
    else:
        logger.warning(f"Media file not found or no path specified: {file_path}")

    logger.info(f"Resume removal completed for id: {id}, file_removed: {file_removed}")
    logger.info("=== REMOVE RESUME REQUEST COMPLETED SUCCESSFULLY ===")

    return Response({
        "success": True,
        "id": id,
        "message": "Resume removed successfully",
        "file_removed": file_removed
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def cleanup_all_resumes(request):
    """
    Remove ALL resume files and database entries.
    
    SECURITY MEASURES:
    - Requires confirmation token
    - Only works in DEBUG mode (development/testing)
    - Comprehensive logging
    - Rate limiting protection
    
    WARNING: This is a destructive operation that removes ALL resume data!
    """
    logger.info("=== CLEANUP ALL RESUMES REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")
    logger.info(f"Request IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    logger.info(f"Request User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}")

    # Security Check 1: Only allow in DEBUG mode (development/testing)
    # if not settings.DEBUG:
    #     logger.warning("Cleanup all resumes attempted in production mode - BLOCKED")
    #     logger.info("=== CLEANUP ALL RESUMES REQUEST BLOCKED - PRODUCTION MODE ===")
    #     return Response({
    #         "success": False,
    #         "error": "This operation is only allowed in development mode"
    #     }, status=status.HTTP_403_FORBIDDEN)

    # Security Check 2: Require confirmation token
    confirmation_token = request.data.get('confirmation_token')
    expected_token = os.getenv('DELETE_ALL_RESUMES_TOKEN', 'o2euinpiebvoian;*&Ts')  # Change this periodically

    if confirmation_token != expected_token:
        logger.warning(f"Cleanup all resumes attempted with invalid token: {confirmation_token}")
        logger.info("=== CLEANUP ALL RESUMES REQUEST BLOCKED - INVALID TOKEN ===")
        return Response({
            "success": False,
            "error": "Invalid confirmation token required for this destructive operation"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Security Check 3: Additional confirmation field
    confirm_action = request.data.get('confirm_action')
    if confirm_action != "DELETE_ALL_RESUME_DATA":
        logger.warning(f"Cleanup all resumes attempted without proper confirmation: {confirm_action}")
        logger.info("=== CLEANUP ALL RESUMES REQUEST BLOCKED - MISSING CONFIRMATION ===")
        return Response({
            "success": False,
            "error": "Must confirm action with 'DELETE_ALL_RESUME_DATA'"
        }, status=status.HTTP_400_BAD_REQUEST)

    logger.warning("=== STARTING DESTRUCTIVE CLEANUP OPERATION ===")

    # Get statistics before cleanup
    total_resumes = InterviewSession.objects.count()
    logger.info(f"Total interview sessions in database before cleanup: {total_resumes}")

    # Count files in media directory
    media_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
    file_count = 0
    if os.path.exists(media_dir):
        try:
            file_count = len([f for f in os.listdir(media_dir) if f.endswith('.pdf')])
            logger.info(f"Total PDF files in media directory: {file_count}")
        except Exception as e:
            logger.error(f"Error counting files in media directory: {str(e)}")

    # Statistics tracking
    files_removed = 0
    files_failed = 0
    db_records_removed = 0
    db_errors = []

    # Step 1: Remove all files from media directory
    logger.info("Starting file cleanup from media directory...")
    if os.path.exists(media_dir):
        try:
            for filename in os.listdir(media_dir):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(media_dir, filename)
                    try:
                        os.remove(file_path)
                        files_removed += 1
                        logger.info(f"Removed file: {filename}")
                    except Exception as e:
                        files_failed += 1
                        logger.error(f"Failed to remove file {filename}: {str(e)}")
        except Exception as e:
            logger.error(f"Error accessing media directory: {str(e)}")
    else:
        logger.warning(f"Media directory does not exist: {media_dir}")

    # Step 2: Remove all database entries
    logger.info("Starting database cleanup...")
    try:
        # Get all interview session IDs for logging
        resume_ids = list(InterviewSession.objects.values_list('id', flat=True))
        logger.info(f"Interview session IDs to be deleted: {resume_ids}")

        # Delete all interview sessions
        db_records_removed, deletion_info = InterviewSession.objects.all().delete()
        logger.info(f"Database cleanup completed. Records removed: {db_records_removed}")
        logger.info(f"Deletion details: {deletion_info}")

    except Exception as e:
        error_msg = f"Database cleanup failed: {str(e)}"
        logger.error(error_msg)
        db_errors.append(error_msg)

    # Prepare response
    cleanup_summary = {
        "success": True,
        "operation": "cleanup_all_resumes",
        "timestamp": time.time(),
        "statistics": {
            "total_resumes_before": total_resumes,
            "total_files_before": file_count,
            "files_removed": files_removed,
            "files_failed": files_failed,
            "db_records_removed": db_records_removed,
            "db_errors": db_errors
        },
        "message": "Cleanup operation completed"
    }

    # Log final summary
    logger.warning("=== CLEANUP OPERATION COMPLETED ===")
    logger.info(f"Final summary: {cleanup_summary}")

    # Return appropriate status based on results
    if files_failed > 0 or db_errors:
        cleanup_summary["success"] = False
        cleanup_summary["message"] = "Cleanup completed with errors"
        return Response(cleanup_summary, status=status.HTTP_206_PARTIAL_CONTENT)
    else:
        return Response(cleanup_summary, status=status.HTTP_200_OK)
