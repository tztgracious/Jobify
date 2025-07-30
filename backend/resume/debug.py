from django.conf import settings
from django.http import JsonResponse
from interview.utils import get_questions_using_openai
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_200_OK
from interview.utils import get_questions_using_openai_multi_agent
from resume.utils import get_session_by_id


@api_view(["GET"])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse(
            {"error": "Debug endpoint disabled in production"}, status=403
        )
    keywords = ["python", "django", "vue", "redis"]
    session = get_session_by_id("e6e1bf9856ab47118ca1ed614f5cf320")
    get_questions_using_openai_multi_agent(session)
    return JsonResponse(
        {
            "DEBUG": settings.DEBUG,
            "questions": session.questions,
            "tech_questions": session.tech_questions,
        },
        status=HTTP_200_OK,
    )
