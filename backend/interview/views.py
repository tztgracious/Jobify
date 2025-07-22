import os
import uuid

import deprecated
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from jobify_backend.logger import logger
from jobify_backend.settings import MAX_VIDEO_FILE_SIZE
from resume.utils import get_session_by_id
from .models import InterviewSession
from .utils import (get_questions_using_openai, get_feedback_using_openai_text, process_text_answer,
                    process_video_answer, get_feedback_using_openai_video)


@api_view(['POST'])
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
    session_id = request.data.get('id')
    if not session_id:
        logger.warning("get_all_questions called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = get_session_by_id(session_id)
    if not session:
        logger.warning(f"All questions requested for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if resume processing is complete
    if session.resume_status != InterviewSession.Status.COMPLETE:
        logger.info(f"Resume still processing for id: {session_id}, status: {session.resume_status}")
        return Response({
            "id": session_id,
            "finished": False,
            "tech_questions": [],
            "interview_questions": [],
            "message": "Resume is still being processed. Please wait."
        }, status=status.HTTP_200_OK)

    # Check if questions are ready
    if session.question_status != InterviewSession.Status.COMPLETE:
        logger.info(f"Questions still processing for id: {session_id}, status: {session.question_status}")
        return Response({
            "id": session_id,
            "finished": False,
            "tech_questions": [],
            "interview_questions": [],
            "message": "Questions are still being generated. Please wait."
        }, status=status.HTTP_200_OK)

    # Get technical questions
    tech_questions = session.tech_questions or []

    # Get interview questions
    interview_questions = session.questions or []

    logger.info(
        f"Retrieved all questions for id: {session_id}, tech: {len(tech_questions)}, interview: {len(interview_questions)}")

    return Response({
        "id": session_id,
        "finished": True,
        "tech_questions": tech_questions,
        "interview_questions": interview_questions,
        "message": "All questions retrieved successfully"
    }, status=status.HTTP_200_OK)


@deprecated.deprecated(reason="Use get_all_questions instead")
@api_view(['POST'])
def get_tech_question(request):
    """
    Retrieve tech questions for a given id.
    Accepts JSON data with:
        - id: The resume document ID
    """
    session_id = request.data.get('id')
    if not session_id:
        logger.warning("get_interview_questions called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Interview questions requested for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    # TODO: write proper tech questions
    return Response({
        "id": session_id,
        "tech_questions": resume.tech_questions
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_tech_answer(request):
    """
    Submit an answer to a technical question in an interview session.
    Expected payload: {
        "id": "uuid",
        "question_index": 0,  # Index of the question being answered (0-based)
        "tech_question": "What is your experience with Python?",  # The technical question text for validation
        "tech_answer": "I have 5 years of experience with Python..."
    }
    """
    session_id = request.data.get('id')
    question_index = request.data.get('question_index')
    tech_question = request.data.get('tech_question', '').strip()
    tech_answer = request.data.get('tech_answer', '').strip()

    if not session_id:
        logger.warning("submit_tech_answer called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if question_index is None:
        logger.warning("submit_tech_answer called without question_index")
        return Response({"error": "question_index is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not tech_question:
        logger.warning("submit_tech_answer called without tech_question")
        return Response({"error": "tech_question is required for validation"}, status=status.HTTP_400_BAD_REQUEST)

    if not tech_answer:
        logger.warning("submit_tech_answer called without valid tech_answer")
        return Response({"error": "tech_answer is required and cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

    # Verify that the resume exists for the given id
    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Tech answer submitted for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Validate question index
    tech_questions = resume.tech_questions or []
    if question_index < 0 or question_index >= len(tech_questions):
        logger.warning(f"Invalid question_index {question_index} for id: {session_id}")
        return Response({"error": f"Invalid question_index. Must be between 0 and {len(tech_questions) - 1}"},
                        status=status.HTTP_400_BAD_REQUEST)

    # Validate that the question text matches
    if tech_questions[question_index] != tech_question:
        logger.warning(f"Question mismatch at index {question_index} for id: {session_id}")
        return Response({"error": "Question text does not match the question at the specified index"},
                        status=status.HTTP_400_BAD_REQUEST)

    # Ensure tech_answers list is properly sized
    tech_answers = resume.tech_answers or []
    while len(tech_answers) <= question_index:
        tech_answers.append("")

    # Update the answer at the specified index
    tech_answers[question_index] = tech_answer
    resume.tech_answers = tech_answers
    resume.save()

    logger.info(f"Updated tech answer at index {question_index} for id: {session_id}")

    return Response({
        "id": session_id,
        "message": "Technical answer submitted successfully",
        "question_index": question_index,
        "tech_question": tech_question,
        "tech_answer": tech_answer
    }, status=status.HTTP_200_OK)


@deprecated.deprecated(reason="Use get_all_questions instead")
@api_view(['POST'])
def get_interview_questions(request):
    """
    Retrieve interview questions for a given id.
    Accepts JSON data with:
        - id: The resume document ID
    """
    session_id = request.data.get('id')
    if not session_id:
        logger.warning("get_interview_questions called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Interview questions requested for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if an interview session already exists for this id
    existing_session = InterviewSession.objects.filter(id=session_id).first()
    if existing_session:
        logger.info(f"Returning existing interview session for id: {session_id}")
        return Response({
            "id": session_id,
            "interview_questions": existing_session.questions
        }, status=status.HTTP_200_OK)

    target_job: str = resume.target_job
    keywords: list[str] = resume.keywords or []
    interview_questions = get_questions_using_openai(target_job, keywords)
    if not interview_questions:
        logger.warning(f"No interview questions found for id: {session_id}")
        return Response({"error": "No interview questions found"}, status=status.HTTP_404_NOT_FOUND)

    # Create a new InterviewSession
    try:
        interview_session = InterviewSession.objects.create(
            resume=resume,
            id=session_id,
            questions=interview_questions
        )
        logger.info(f"Created new interview session {interview_session.id} for id: {session_id}")

        return Response({
            "id": session_id,
            "interview_questions": interview_questions
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Failed to create interview session for id {session_id}: {str(e)}")
        return Response({
            "id": session_id,
            "interview_questions": interview_questions,
            "error": "Failed to create interview session"
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
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
    session_id = request.data.get('id')
    question_index = request.data.get('index')
    question_text = request.data.get('question', '').strip()
    answer_type = request.data.get('answer_type', '').strip()

    if not session_id:
        logger.warning("submit_answer called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if question_index is None:
        logger.warning("submit_answer called without question_index")
        return Response({"error": "question_index is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not question_text:
        logger.warning("submit_answer called without question text")
        return Response({"error": "question is required for validation"}, status=status.HTTP_400_BAD_REQUEST)

    if not answer_type:
        logger.warning("submit_answer called without answer_type")
        return Response({"error": "answer_type is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Find the interview session by id
    interview_session = InterviewSession.objects.filter(id=session_id).first()
    if not interview_session:
        logger.warning(f"Interview session not found for id: {session_id}")
        return Response({"error": "Interview session not found"}, status=status.HTTP_404_NOT_FOUND)

    # Validate question_index
    if question_index < 0 or question_index >= len(interview_session.questions):
        logger.warning(f"Invalid question_index {question_index} for id {session_id}")
        return Response({
            "error": f"question_index must be between 0 and {len(interview_session.questions) - 1}"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Process answer based on type using utility functions
    if answer_type == 'text':
        answer = request.data.get('answer', '')
        if not answer:
            logger.warning("submit_answer called without valid text answer")
            return Response({"error": "answer is required and cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        result = process_text_answer(session_id, question_index, question_text, answer, interview_session)

    elif answer_type == 'video':
        video_file = request.FILES.get('video')
        if not video_file:
            logger.warning("submit_answer called without video file for video answer type")
            return Response({"error": "video file is required for video answers"}, status=status.HTTP_400_BAD_REQUEST)

        result = process_video_answer(session_id, question_index, question_text, video_file, interview_session)

    else:
        logger.warning("submit_answer called with invalid answer_type")
        return Response({"error": "answer_type must be either 'text' or 'video'"}, status=status.HTTP_400_BAD_REQUEST)

    # Handle the result from utility functions
    if "error" in result:
        return Response({"error": result["error"]}, status=result["status"])

    # Remove status from result before returning
    status_code = result.pop("status", 200)
    return Response(result, status=status_code)


@api_view(['POST'])
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
    session_id = request.data.get('id')
    if not session_id:
        logger.warning("get_feedback called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
    session = get_session_by_id(session_id)
    if not session:
        logger.warning(f"Feedback questions requested for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    answer_type = request.data.get('answer_type', '')
    match answer_type:
        case 'text':
            logger.info(f"Retrieving feedback for id: {session_id}, answer_type: {answer_type}")
            feedback = get_feedback_using_openai_text(session)
            if not feedback:
                logger.warning(f"No feedback questions generated for session {session.id}")
                return Response({"error": "No feedback questions found"}, status=status.HTTP_404_NOT_FOUND)
            session.feedback = feedback
            session.save()
            return Response({
                "id": session_id,
                "feedbacks": feedback
            }, status=status.HTTP_200_OK)
        case 'video':
            # TODO: implement video feedback
            logger.info(f"Retrieving feedback for id: {session_id}, answer_type: {answer_type}")
            feedback = get_feedback_using_openai_video(session)
            return Response({"error": "Video feedback not yet implemented"}, status=status.HTTP_400_BAD_REQUEST)
        case _:
            logger.warning("get_feedback called with invalid answer_type")
            return Response({"error": "answer_type must be either 'text' or 'video'"},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def upload_video(request):
    """
    Upload a video for a given id.
    Expected payload:
    - id: The document ID associated with the video
    - video: The video file to upload
    """
    session_id = request.data.get('id')
    video_file = request.FILES.get('video')

    if not session_id:
        logger.warning("upload_video called without id")
        return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not video_file:
        logger.warning("upload_video called without video file")
        return Response({"error": "video file is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check file size limit (75MB)
    if video_file.size > MAX_VIDEO_FILE_SIZE:
        logger.warning(f"Video file too large for id {session_id}: {video_file.size} bytes")
        return Response({
            "error": f"File size too large. Maximum allowed size is 75MB, but received {video_file.size / (1024 * 1024):.1f}MB"
        }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    # Verify that the resume exists for the given id
    resume = get_session_by_id(session_id)
    if not resume:
        logger.warning(f"Video upload attempted for non-existent id: {session_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    logger.info(f"Video upload received for id: {session_id}, filename: {video_file.name}")

    # Create video directory if it doesn't exist
    video_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
    os.makedirs(video_dir, exist_ok=True)

    # Generate unique filename to prevent conflicts
    file_extension = os.path.splitext(video_file.name)[1]
    unique_filename = f"{session_id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(video_dir, unique_filename)

    # Save the video file
    try:
        with open(file_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        logger.info(f"Video saved to: {file_path}")

        # TODO: Process video file (transcription, analysis, etc.)

        return Response({
            "id": session_id,
            "message": "Video uploaded and saved successfully",
            "filename": video_file.name,
            "saved_as": unique_filename,
            "size": video_file.size,
            "file_path": f"videos/{unique_filename}"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Failed to save video for id {session_id}: {str(e)}")
        return Response({
            "error": "Failed to save video file"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
