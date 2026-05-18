import os
import threading
import uuid
from django.conf import settings
from interview.models.interview_session import InterviewSession
from jobify_backend.logger import logger
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from .services import ResumeService
from .utils import check_file_size_with_message


@api_view(["POST"])
def upload_resume(request):
    """
    Upload a PDF resume file and return an id for future operations.
    Validates file size (max 5MB) and file type (PDF only).
    """
    logger.info("=== UPLOAD RESUME REQUEST STARTED ===")

    file = request.FILES.get("file")
    if not file:
        logger.warning("Upload attempt with no file provided")
        return Response(
            {"id": None, "valid_file": False, "error_msg": "No file uploaded"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check file type
    if not file.content_type == "application/pdf":
        logger.warning(f"Upload attempt with invalid file type: {file.content_type}")
        return Response(
            {"id": None, "valid_file": False, "error_msg": "Not a PDF file."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check file size (max 5MB)
    is_valid_size, size_error_msg = check_file_size_with_message(file, max_size_mb=5)
    if not is_valid_size:
        return Response(
            {"id": None, "valid_file": False, "error_msg": size_error_msg},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Generate session ID
    session_id = str(uuid.uuid4())

    try:
        # Save file via service
        file_path = ResumeService.save_resume_file(file, session_id)
        
        # Create session via service
        ResumeService.create_interview_session(session_id, file_path)
        
        # Trigger background parsing via service
        ResumeService.trigger_resume_parsing(session_id)
        
        logger.info(f"Resume upload and task trigger successful for id: {session_id}")
        return Response(
            {"id": session_id, "valid_file": True, "error_msg": None},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Failed to process resume upload: {str(e)}")
        return Response(
            {
                "id": None,
                "valid_file": False,
                "error_msg": f"Server error: {str(e)}",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def get_grammar_results(request):
    """
    Retrieve grammar check results for a given id.
    """
    session_id = request.data.get("id")
    if not session_id:
        return Response({"finished": False, "grammar_check": None, "error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = ResumeService.get_session_by_id(session_id)
    if not session:
        return Response({"finished": False, "grammar_check": None, "error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    if session.resume_status == InterviewSession.Status.FAILED:
        ResumeService.trigger_resume_parsing(str(session.id))
        return Response(
            {"finished": False, "grammar_check": None, "error": "Resume processing failed. Trying again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    elif session.resume_status == InterviewSession.Status.PROCESSING:
        return Response({"finished": False, "grammar_check": None, "error": ""}, status=status.HTTP_200_OK)
    
    elif session.resume_status == InterviewSession.Status.COMPLETE:
        return Response(
            {"finished": True, "grammar_check": session.grammar_results, "error": ""},
            status=status.HTTP_200_OK,
        )

    return Response({"finished": False, "grammar_check": None, "error": "Unknown status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def get_keywords(request):
    """
    Retrieve keywords for a given id.
    """
    session_id = request.data.get("id")
    if not session_id:
        return Response({"finished": False, "keywords": [], "error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = ResumeService.get_session_by_id(session_id)
    if not session:
        return Response({"finished": False, "keywords": [], "error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check processing status
    if session.resume_status == InterviewSession.Status.FAILED:
        ResumeService.trigger_resume_parsing(str(session.id))
        return Response(
            {"finished": False, "keywords": [], "error": "Resume processing failed. Trying again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    elif session.resume_status == InterviewSession.Status.PROCESSING:
        return Response({"finished": False, "keywords": [], "error": ""}, status=status.HTTP_200_OK)
    
    elif session.resume_status == InterviewSession.Status.COMPLETE:
        return Response(
            {"finished": True, "keywords": session.keywords or [], "error": ""},
            status=status.HTTP_200_OK,
        )

    return Response({"finished": False, "keywords": [], "error": "Unknown status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def target_job(request):
    """
    Save user's target job preferences.
    """
    session_id = request.data.get("id")
    title = request.data.get("title")
    answer_type = request.data.get("answer_type", "text")

    if not session_id or not title or not title.strip():
        logger.warning(f"Target job called without required fields: {session_id}")
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    if answer_type not in ["text", "video"]:
        return Response({"error": "answer_type must be either 'text' or 'video'"}, status=status.HTTP_400_BAD_REQUEST)

    if ResumeService.set_target_job(session_id, title, answer_type):
        return Response(
            {
                "id": session_id,
                "message": "Target job and answer type saved successfully",
                "answer_type": answer_type,
            },
            status=status.HTTP_200_OK
        )
    
    return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def remove_resume(request):
    """
    Remove a resume and its associated media file.
    Accepts id and removes both the database entry and the PDF file.
    """
    session_id = request.data.get("id")
    if not session_id:
        return Response({"success": False, "error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = ResumeService.get_session_by_id(session_id)
    if not resume:
        return Response({"success": False, "error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    file_path = resume.resume_local_path

    try:
        resume.delete()
    except Exception as e:
        return Response({"success": False, "error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    file_removed = False
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            file_removed = True
        except Exception as e:
            logger.error(f"Failed to remove media file: {file_path}, error: {str(e)}")

    return Response(
        {
            "success": True,
            "id": session_id,
            "message": "Resume removed successfully",
            "file_removed": file_removed,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def cleanup_all_resumes(request):
    """
    Remove ALL resume files and database entries.
    """
    logger.warning("=== CLEANUP ALL RESUMES REQUEST STARTED BY ADMIN ===")
    
    confirm_action = request.data.get("confirm_action")
    if confirm_action != "DELETE_ALL_RESUME_DATA":
        return Response(
            {"success": False, "error": "Must confirm action with 'DELETE_ALL_RESUME_DATA'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = ResumeService.cleanup_all_resumes()

    return Response({
        "success": True,
        "message": f"Deleted {results['files_removed']} files and {results['db_records_removed']} database records",
        "errors": results["errors"]
    }, status=status.HTTP_200_OK)
