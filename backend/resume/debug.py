import uuid

from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_200_OK

from interview.models import InterviewSession
from interview.utils import get_feedback_using_openai
from resume.models import Resume


@api_view(['GET'])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "Debug endpoint disabled in production"}, status=403)
    resume = Resume.objects.create(
        id=uuid.uuid4(),
        keywords=['python', 'django', 'rest', 'api'],
        target_job='Backend Developer',
        status=Resume.Status.COMPLETE
    )
    interview_session = InterviewSession.objects.create(
        resume=resume,
        doc_id=uuid.uuid4(),
        questions=["Question 1?", "Question 2?", "Question 3?"],
        answers=["Answer 1", "Answer 2", "Answer 3"],
    )
    feedback = get_feedback_using_openai(resume, interview_session)
    return JsonResponse({
        "DEBUG": settings.DEBUG,
        "FEEDBACK": feedback,
    }, status=HTTP_200_OK)
