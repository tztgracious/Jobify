import os
import time
import uuid

import deprecated
import django
from django.conf import settings
from django.utils import timezone
from jobify_backend.logger import logger
from jobify_backend.settings import MAX_VIDEO_FILE_SIZE
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from resume.utils import get_session_by_id

from .models import InterviewSession
from .utils import (
    get_feedback_using_openai_text,
    get_questions_using_openai, get_feedback_using_openai_multi_agent,
)


@api_view(["POST"])
def get_all_questions(request):
    """
    Retrieve all questions for a given id.
    Accepts JSON data with:
        - id: The resume document ID
    Response:
        - id: The resume document ID
        - finished: True/False
        - tech_questions: List of tech questions
        - interview_questions: List of interview questions
        - message: Status message
    """
    session_id = request.data.get("id")
    if not session_id:
        logger.warning("get_all_questions called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = get_session_by_id(session_id)
    if not session:
        logger.warning(f"All questions requested for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if resume processing is complete
    if session.resume_status != InterviewSession.Status.COMPLETE:
        logger.info(
            f"Resume still processing for id: {session_id}, status: {session.resume_status}"
        )
        return Response(
            {
                "id": session_id,
                "finished": False,
                "tech_questions": [],
                "interview_questions": [],
                "message": "Resume is still being processed. Please wait.",
            },
            status=status.HTTP_200_OK,
        )

    # Check if questions are ready
    if session.question_status != InterviewSession.Status.COMPLETE:
        logger.info(
            f"Questions still processing for id: {session_id}, status: {session.question_status}"
        )
        return Response(
            {
                "id": session_id,
                "finished": False,
                "tech_questions": [],
                "interview_questions": [],
                "message": "Questions are still being generated. Please wait.",
            },
            status=status.HTTP_200_OK,
        )

    # Get technical questions
    tech_questions = session.tech_questions or []

    # Get interview questions
    interview_questions = session.questions or []

    logger.info(
        f"Retrieved all questions for id: {session_id}, tech: {len(tech_questions)}, interview: {len(interview_questions)}"
    )

    return Response(
        {
            "id": session_id,
            "finished": True,
            "tech_questions": tech_questions,
            "interview_questions": interview_questions,
            "message": "All questions retrieved successfully",
        },
        status=status.HTTP_200_OK,
    )


@deprecated.deprecated(reason="Use get_all_questions instead")
@api_view(["POST"])
def get_tech_question(request):
    """
    Retrieve tech questions for a given id.
    Accepts JSON data with:
        - id: The resume document ID
    """
    session_id = request.data.get("id")
    if not session_id:
        logger.warning("get_interview_questions called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(
            f"Interview questions requested for non-existent id: {session_id}"
        )
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    # TODO: write proper tech questions
    return Response(
        {"id": session_id, "tech_questions": resume.tech_questions},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def submit_tech_answer(request):
    """
    Submit an answer to a technical question in an interview session.
    Expected payload: {
        "id": "uuid",
        "index": 0,  # Index of the question being answered (0-based)
        "question": "What is your experience with Python?",  # The technical question text for validation
        "answer": "I have 5 years of experience with Python..."
    }
    """
    session_id = request.data.get("id")
    question_index = request.data.get("index")
    tech_question = request.data.get("question", "").strip()
    tech_answer = request.data.get("answer", "").strip()

    if not session_id:
        logger.warning("submit_tech_answer called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if question_index is None:
        logger.warning("submit_tech_answer called without question_index")
        return Response(
            {"error": "question_index is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not tech_question:
        logger.warning("submit_tech_answer called without tech_question")
        return Response(
            {"error": "tech_question is required for validation"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not tech_answer:
        logger.warning("submit_tech_answer called without valid tech_answer")
        return Response(
            {"error": "tech_answer is required and cannot be empty"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify that the resume exists for the given id
    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Tech answer submitted for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Validate question index
    tech_questions = resume.tech_questions or []
    if question_index < 0 or question_index >= len(tech_questions):
        logger.warning(f"Invalid question_index {question_index} for id: {session_id}")
        return Response(
            {
                "error": f"Invalid question_index. Must be between 0 and {len(tech_questions) - 1}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate that the question text matches
    if tech_questions[question_index] != tech_question:
        logger.warning(
            f"Question mismatch at index {question_index} for id: {session_id}"
        )
        return Response(
            {
                "error": "Question text does not match the question at the specified index"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Ensure tech_answers list is properly sized
    tech_answers = resume.tech_answers or []
    while len(tech_answers) <= question_index:
        tech_answers.append("")

    # Update the answer at the specified index
    tech_answers[question_index] = tech_answer
    resume.tech_answers = tech_answers
    resume.save()

    logger.info(f"Updated tech answer at index {question_index} for id: {session_id}")

    return Response(
        {
            "id": session_id,
            "message": "Technical answer submitted successfully",
            "index": question_index,
            "question": tech_question,
            "answer": tech_answer,
        },
        status=status.HTTP_200_OK,
    )


@deprecated.deprecated(reason="Use get_all_questions instead")
@api_view(["POST"])
def get_interview_questions(request):
    """
    Retrieve interview questions for a given id.
    Accepts JSON data with:
        - id: The resume document ID
    """
    session_id = request.data.get("id")
    if not session_id:
        logger.warning("get_interview_questions called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(
            f"Interview questions requested for non-existent id: {session_id}"
        )
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if an interview session already exists for this id
    existing_session = InterviewSession.objects.filter(id=session_id).first()
    if existing_session:
        logger.info(f"Returning existing interview session for id: {session_id}")
        return Response(
            {"id": session_id, "interview_questions": existing_session.questions},
            status=status.HTTP_200_OK,
        )

    target_job: str = resume.target_job
    keywords: list[str] = resume.keywords or []
    interview_questions = get_questions_using_openai(target_job, keywords)
    if not interview_questions:
        logger.warning(f"No interview questions found for id: {session_id}")
        return Response(
            {"error": "No interview questions found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Create a new InterviewSession
    try:
        interview_session = InterviewSession.objects.create(
            resume=resume, id=session_id, questions=interview_questions
        )
        logger.info(
            f"Created new interview session {interview_session.id} for id: {session_id}"
        )

        return Response(
            {"id": session_id, "interview_questions": interview_questions},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(
            f"Failed to create interview session for id {session_id}: {str(e)}"
        )
        return Response(
            {
                "id": session_id,
                "interview_questions": interview_questions,
                "error": "Failed to create interview session",
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
def submit_interview_answer(request):
    """
    Submit an answer to a specific question in an interview session.

    For text answers, expected payload: {
        "id": "uuid",
        "index": 0,  # Index of the question being answered (0-based)
        "answer_type": "text",
        "question": "What are your biggest strengths?",  # The actual question text for validation
        "answer": "My answer to this question"
    }

    For video answers, expected form data:
        - id: "uuid"
        - index: 0
        - answer_type: "video"
        - question: "What are your biggest strengths?"
        - video: <video file>
    """
    session_id = request.data.get("id")
    question_index = request.data.get("index")
    question_text = request.data.get("question", "").strip()
    answer_type = request.data.get("answer_type", "").strip()

    if not session_id:
        logger.warning("submit_answer called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if question_index is None:
        logger.warning("submit_answer called without question_index")
        return Response(
            {"error": "question_index is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not question_text:
        logger.warning("submit_answer called without question text")
        return Response(
            {"error": "question is required for validation"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not answer_type:
        logger.warning("submit_answer called without answer_type")
        return Response(
            {"error": "answer_type is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Find the interview session by id
    interview_session = InterviewSession.objects.filter(id=session_id).first()
    if not interview_session:
        logger.warning(f"Interview session not found for id: {session_id}")
        return Response(
            {"error": "Interview session not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Validate question_index
    if question_index < 0 or question_index >= len(interview_session.questions):
        logger.warning(f"Invalid question_index {question_index} for id {session_id}")
        return Response(
            {
                "error": f"question_index must be between 0 and {len(interview_session.questions) - 1}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Process answer based on type using utility functions
    if answer_type == "text":
        answer = request.data.get("answer", "")
        if not answer:
            logger.warning("submit_answer called without valid text answer")
            return Response(
                {"error": "answer is required and cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate that the question text matches
        if interview_session.questions[question_index] != question_text:
            logger.warning(f"Question mismatch at index {question_index} for session {session_id}")
            return Response(
                {"error": "Question text does not match the question at the specified index"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Ensure answers list is properly sized
        answers = interview_session.answers or []
        while len(answers) <= question_index:
            answers.append("")
        
        # Update the answer at the specified index
        answers[question_index] = answer
        interview_session.answers = answers
        interview_session.save()
        
        # Calculate progress
        answered_questions = sum(1 for ans in answers if ans.strip())
        total_questions = len(interview_session.questions)
        progress = round((answered_questions / total_questions) * 100, 2) if total_questions > 0 else 0
        is_completed = answered_questions == total_questions
        
        logger.info(f"Updated interview session for id {session_id} - answered question {question_index} with text answer")
        
        result = {
            "id": session_id,
            "message": f"Text answer submitted for question {question_index + 1}",
            "question": question_text,
            "answer_type": "text",
            "answer": answer,
            "progress": progress,
            "is_completed": is_completed,
        }

    elif answer_type == "video":
        video_file = request.FILES.get("video")
        if not video_file:
            logger.warning(
                "submit_answer called without video file for video answer type"
            )
            return Response(
                {"error": "video file is required for video answers"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # TODO: implement processing logic
        # result = process_video_answer(
        #     session_id, question_index, question_text, video_file, interview_session
        # )
        result = {"error": "Video processing not yet implemented"}

    else:
        logger.warning("submit_answer called with invalid answer_type")
        return Response(
            {"error": "answer_type must be either 'text' or 'video'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Handle the result from utility functions
    if "error" in result:
        return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

    # Return the successful result
    return Response(result, status=status.HTTP_200_OK)


@api_view(["POST"])
def get_feedback(request):
    """
    Retrieve interview feedback for a given id.
    Payload: {
        "id": "uuid",
        "answer_type": "text" | "video,
    }

    Response: {
        "id": "uuid",
        "feedbacks": {
            "tech_feedbacks": ["feedback1"],
            "interview_feedbacks": ["feedback1", "feedback2", "feedback3"],
        }
    """
    logger.info("=== FEEDBACK REQUEST STARTED ===")
    session_id = request.data.get("id")
    if not session_id:
        logger.warning("get_feedback called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
    session = get_session_by_id(session_id)
    if not session:
        logger.warning(
            f"Feedback questions requested for non-existent id: {session_id}"
        )
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    answer_type = request.data.get("answer_type", "")
    match answer_type:
        case "text":
            logger.info(
                f"Retrieving feedback for id: {session_id}, answer_type: {answer_type}"
            )
            feedback = get_feedback_using_openai_multi_agent(session)
            if not feedback:
                logger.warning(
                    f"No feedback questions generated for session {session.id}"
                )
                return Response(
                    {"error": "No feedback questions found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            session.feedback = feedback
            session.save()
            return Response(
                {"id": session_id, "feedbacks": feedback}, status=status.HTTP_200_OK
            )
        case "video":
            # TODO: implement video feedback
            logger.info(
                f"Retrieving feedback for id: {session_id}, answer_type: {answer_type}"
            )
            # feedback = get_feedback_using_openai_video(session)
            return Response(
                {"error": "Video feedback not yet implemented"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        case _:
            logger.warning("get_feedback called with invalid answer_type")
            return Response(
                {"error": "answer_type must be either 'text' or 'video'"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["POST"])
def upload_video(request):
    """
    Upload a video for a given id.
    Expected payload:
    - id: The document ID associated with the video
    - video: The video file to upload
    """
    session_id = request.data.get("id")
    video_file = request.FILES.get("video")

    if not session_id:
        logger.warning("upload_video called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not video_file:
        logger.warning("upload_video called without video file")
        return Response(
            {"error": "video file is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check file size limit (75MB)
    if video_file.size > MAX_VIDEO_FILE_SIZE:
        logger.warning(
            f"Video file too large for id {session_id}: {video_file.size} bytes"
        )
        return Response(
            {
                "error": f"File size too large. Maximum allowed size is 75MB, but received {video_file.size / (1024 * 1024):.1f}MB"
            },
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    # Verify that the resume exists for the given id
    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Video upload attempted for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    logger.info(
        f"Video upload received for id: {session_id}, filename: {video_file.name}"
    )

    # Create video directory if it doesn't exist
    video_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(video_dir, exist_ok=True)

    # Generate unique filename to prevent conflicts
    file_extension = os.path.splitext(video_file.name)[1]
    unique_filename = f"{session_id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(video_dir, unique_filename)

    # Save the video file
    try:
        with open(file_path, "wb+") as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        logger.info(f"Video saved to: {file_path}")

        # TODO: Process video file (transcription, analysis, etc.)

        return Response(
            {
                "id": session_id,
                "message": "Video uploaded and saved successfully",
                "filename": video_file.name,
                "saved_as": unique_filename,
                "size": video_file.size,
                "file_path": f"videos/{unique_filename}",
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Failed to save video for id {session_id}: {str(e)}")
        return Response(
            {"error": "Failed to save video file"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def cleanup_all_videos(request):
    """
    Remove ALL video files from the server.

    SECURITY MEASURES:
    - Requires confirmation token
    - Only works in DEBUG mode (development/testing)
    - Comprehensive logging
    - Rate limiting protection

    WARNING: This is a destructive operation that removes ALL video data!
    """
    logger.info("=== CLEANUP ALL VIDEOS REQUEST STARTED ===")
    logger.info(f"Request data: {request.data}")
    logger.info(f"Request IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    logger.info(f"Request User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}")

    # Security Check 1: Only allow in DEBUG mode (development/testing)
    # if not settings.DEBUG:
    #     logger.warning("Cleanup all videos attempted in production mode - BLOCKED")
    #     logger.info("=== CLEANUP ALL VIDEOS REQUEST BLOCKED - PRODUCTION MODE ===")
    #     return Response({
    #         "success": False,
    #         "error": "This operation is only allowed in development mode"
    #     }, status=status.HTTP_403_FORBIDDEN)

    # Security Check 2: Require confirmation token
    confirmation_token = request.data.get("confirmation_token")
    expected_token = os.getenv("DJANGO_SECRET_KEY")

    if confirmation_token != expected_token:
        logger.warning(
            f"Cleanup all videos attempted with invalid token: {confirmation_token}"
        )
        logger.info("=== CLEANUP ALL VIDEOS REQUEST BLOCKED - INVALID TOKEN ===")
        return Response(
            {
                "success": False,
                "error": "Invalid confirmation token required for this destructive operation",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Security Check 3: Additional confirmation field
    confirm_action = request.data.get("confirm_action")
    if confirm_action != "DELETE_ALL_VIDEO_DATA":
        logger.warning(
            f"Cleanup all videos attempted without proper confirmation: {confirm_action}"
        )
        logger.info("=== CLEANUP ALL VIDEOS REQUEST BLOCKED - MISSING CONFIRMATION ===")
        return Response(
            {
                "success": False,
                "error": "Must confirm action with 'DELETE_ALL_VIDEO_DATA'",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    logger.warning("=== STARTING DESTRUCTIVE VIDEO CLEANUP OPERATION ===")

    # Video directories to clean
    video_directories = [
        os.path.join(settings.MEDIA_ROOT, "videos"),
        os.path.join(settings.MEDIA_ROOT, "interview_videos"),
    ]

    # Statistics tracking
    total_files_before = 0
    files_removed = 0
    files_failed = 0
    directories_processed = 0
    cleanup_errors = []

    # Count total files before cleanup
    logger.info("Counting video files before cleanup...")
    for video_dir in video_directories:
        if os.path.exists(video_dir):
            try:
                for filename in os.listdir(video_dir):
                    if filename.lower().endswith(
                        (
                            ".mp4",
                            ".avi",
                            ".mov",
                            ".mkv",
                            ".webm",
                            ".m4v",
                            ".3gp",
                            ".flv",
                        )
                    ):
                        total_files_before += 1
                logger.info(
                    f"Found {len([f for f in os.listdir(video_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.3gp', '.flv'))])} video files in {video_dir}"
                )
            except Exception as e:
                error_msg = f"Error counting files in {video_dir}: {str(e)}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        else:
            logger.info(f"Video directory does not exist: {video_dir}")

    logger.info(f"Total video files before cleanup: {total_files_before}")

    # Step 1: Remove all video files from directories
    logger.info("Starting video file cleanup...")
    for video_dir in video_directories:
        if os.path.exists(video_dir):
            directories_processed += 1
            logger.info(f"Processing directory: {video_dir}")
            try:
                for filename in os.listdir(video_dir):
                    if filename.lower().endswith(
                        (
                            ".mp4",
                            ".avi",
                            ".mov",
                            ".mkv",
                            ".webm",
                            ".m4v",
                            ".3gp",
                            ".flv",
                        )
                    ):
                        file_path = os.path.join(video_dir, filename)
                        try:
                            os.remove(file_path)
                            files_removed += 1
                            logger.info(f"Removed video file: {filename}")
                        except Exception as e:
                            files_failed += 1
                            error_msg = (
                                f"Failed to remove video file {filename}: {str(e)}"
                            )
                            logger.error(error_msg)
                            cleanup_errors.append(error_msg)
            except Exception as e:
                error_msg = f"Error accessing video directory {video_dir}: {str(e)}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        else:
            logger.info(f"Video directory does not exist: {video_dir}")

    # Determine success status
    operation_success = files_failed == 0 and len(cleanup_errors) == 0

    # Prepare response
    cleanup_summary = {
        "success": operation_success,
        "operation": "cleanup_all_videos",
        "timestamp": time.time(),
        "statistics": {
            "total_files_before": total_files_before,
            "directories_processed": directories_processed,
            "files_removed": files_removed,
            "files_failed": files_failed,
            "cleanup_errors": cleanup_errors,
        },
        "message": (
            "Video cleanup operation completed"
            if operation_success
            else "Video cleanup completed with errors"
        ),
    }

    logger.warning("=== VIDEO CLEANUP OPERATION COMPLETED ===")
    logger.info(f"Cleanup summary: {cleanup_summary}")

    # Return appropriate status code
    response_status = (
        status.HTTP_200_OK if operation_success else status.HTTP_206_PARTIAL_CONTENT
    )

    return Response(cleanup_summary, status=response_status)


@api_view(["GET", "POST"])
def ping(request):
    """
    Simple ping endpoint to verify server status and connectivity.

    This endpoint can be used for:
    - Health checks
    - Load balancer status verification
    - API monitoring
    - Basic connectivity testing

    Returns server status, timestamp, and Django version information.
    """

    # Get Django version
    django_version = django.get_version()

    # Server timestamp
    server_time = timezone.now()

    # Basic server info
    response_data = {
        "status": "ok",
        "message": "Server is running",
        "timestamp": server_time.isoformat(),
        "server_time_utc": server_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "django_version": django_version,
        "api_version": "v1",
        "method": request.method,
        "debug_mode": settings.DEBUG,
    }

    # Add request info if POST method with data
    if request.method == "POST" and request.data:
        response_data["echo"] = {
            "received_data": request.data,
            "data_type": type(request.data).__name__,
        }

    logger.info(
        f"Ping request received from {request.META.get('REMOTE_ADDR', 'unknown')} using {request.method}"
    )

    return Response(response_data, status=status.HTTP_200_OK)
