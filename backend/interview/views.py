import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from resume.utils import get_resume_by_doc_id

logger = logging.getLogger(__name__)


@api_view(['POST'])
def get_interview_questions(request):
    """
    Retrieve interview questions for a given doc_id.
    """
    doc_id = request.data.get('doc_id')
    if not doc_id:
        logger.warning("get_interview_questions called without doc_id")
        return Response({"error": "doc_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    resume = get_resume_by_doc_id(doc_id)
    if not resume:
        logger.warning(f"Interview questions requested for non-existent doc_id: {doc_id}")
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    target_job: str = resume.target_job
    keywords: list[str] = resume.keywords or []

    # Simulate fetching interview questions
    # TODO: use multi-agent models to get the questions
    interview_questions = [
        "What are your strengths?",
        "Why do you want to work here?",
        "Describe a challenging situation you've faced."
    ]

    return Response({
        "doc_id": doc_id,
        "interview_questions": interview_questions
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_answer(request):
    return Response({"error": "not implemented yet!"}, status=status.HTTP_400_BAD_REQUEST)
