import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from resume.utils import get_resume_by_doc_id
from .models import InterviewSession
from .utils import get_questions_using_openai, get_feedback_using_openai

logger = logging.getLogger(__name__)


@api_view(['POST'])
def get_interview_questions(request):
    """
    Retrieve interview questions for a given doc_id and create an InterviewSession.
    """
    doc_id = request.data.get('doc_id')
    if not doc_id:
        logger.warning("get_interview_questions called without doc_id")
        return Response({"error": "doc_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Interview questions requested for non-existent doc_id: {doc_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if an interview session already exists for this doc_id
    existing_session = InterviewSession.objects.filter(doc_id=doc_id).first()
    if existing_session:
        logger.info(f"Returning existing interview session for doc_id: {doc_id}")
        return Response({
            "doc_id": doc_id,
            "interview_questions": existing_session.questions
        }, status=status.HTTP_200_OK)

    target_job: str = resume.target_job
    keywords: list[str] = resume.keywords or []
    interview_questions = get_questions_using_openai(target_job, keywords)
    if not interview_questions:
        logger.warning(f"No interview questions found for doc_id: {doc_id}")
        return Response({"error": "No interview questions found"}, status=status.HTTP_404_NOT_FOUND)

    # Create a new InterviewSession
    try:
        interview_session = InterviewSession.objects.create(
            resume=resume,
            doc_id=doc_id,
            questions=interview_questions
        )
        logger.info(f"Created new interview session {interview_session.id} for doc_id: {doc_id}")

        return Response({
            "doc_id": doc_id,
            "interview_questions": interview_questions
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Failed to create interview session for doc_id {doc_id}: {str(e)}")
        return Response({
            "doc_id": doc_id,
            "interview_questions": interview_questions,
            "error": "Failed to create interview session"
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_answer(request):
    """
    Submit an answer to a specific question in an interview session.
    Expected payload: {
        "doc_id": "uuid",
        "question_index": 0,  # Index of the question being answered (0-based)
        "question": "What are your biggest strengths?",  # The actual question text for validation
        "answer": "My answer to this question"
    }
    """
    doc_id = request.data.get('doc_id')
    question_index = request.data.get('question_index')
    question_text = request.data.get('question', '').strip()
    answer = request.data.get('answer', '').strip()

    if not doc_id:
        logger.warning("submit_answer called without doc_id")
        return Response({"error": "doc_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if question_index is None:
        logger.warning("submit_answer called without question_index")
        return Response({"error": "question_index is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not question_text:
        logger.warning("submit_answer called without question text")
        return Response({"error": "question is required for validation"}, status=status.HTTP_400_BAD_REQUEST)

    if not answer:
        logger.warning("submit_answer called without valid answer")
        return Response({"error": "answer is required and cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

    # Find the interview session by doc_id
    interview_session = InterviewSession.objects.filter(doc_id=doc_id).first()
    if not interview_session:
        logger.warning(f"Interview session not found for doc_id: {doc_id}")
        return Response({"error": "Interview session not found"}, status=status.HTTP_404_NOT_FOUND)

    # Validate question_index
    if question_index < 0 or question_index >= len(interview_session.questions):
        logger.warning(f"Invalid question_index {question_index} for doc_id {doc_id}")
        return Response({
            "error": f"question_index must be between 0 and {len(interview_session.questions) - 1}"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate that the question text matches the stored question
    stored_question = interview_session.questions[question_index]
    if question_text.strip() != stored_question.strip():
        logger.warning(f"Question mismatch for doc_id {doc_id}, question_index {question_index}")
        return Response({
            "error": "Question text does not match the stored question",
            "expected_question": stored_question,
            "provided_question": question_text
        }, status=status.HTTP_400_BAD_REQUEST)

    # Initialize answers list if needed (pad with empty strings)
    if len(interview_session.answers) < len(interview_session.questions):
        interview_session.answers = [''] * len(interview_session.questions)

    # Update the specific answer
    interview_session.answers[question_index] = answer

    # Check if all questions are answered
    answered_count = len([ans for ans in interview_session.answers if ans and ans.strip()])
    is_completed = answered_count == len(interview_session.questions)
    interview_session.is_completed = is_completed

    interview_session.save()

    logger.info(f"Updated interview session for doc_id {doc_id} - answered question {question_index}")

    return Response({
        "doc_id": doc_id,
        "message": f"Answer submitted for question {question_index + 1}",
        "question": stored_question,
        "answer": answer,
        "progress": interview_session.progress,
        "is_completed": is_completed
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_feedback(request):
    """
    Retrieve feedback questions for a given doc_id.

    """
    doc_id = request.query_params.get('doc_id')
    if not doc_id:
        logger.warning("get_feedback called without doc_id")
        return Response({"error": "doc_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Feedback questions requested for non-existent doc_id: {doc_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    # Find the interview session
    interview_session = InterviewSession.objects.filter(doc_id=doc_id).first()
    if not interview_session:
        logger.warning(f"Interview session not found for doc_id: {doc_id}")
        return Response({"error": "Interview session not found"}, status=status.HTTP_404_NOT_FOUND)

    feedback = get_feedback_using_openai(resume, interview_session)

    if not feedback:
        logger.warning(f"No feedback questions generated for session {interview_session.id}")
        return Response({"error": "No feedback questions found"}, status=status.HTTP_404_NOT_FOUND)
    interview_session.feedback = feedback
    interview_session.save()

    return Response({
        "doc_id": doc_id,
        "feedbacks": feedback
    }, status=status.HTTP_200_OK)
