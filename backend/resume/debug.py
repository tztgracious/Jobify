from django.conf import settings
from django.http import JsonResponse
from interview.utils import get_questions_using_openai
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_200_OK


@api_view(["GET"])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse(
            {"error": "Debug endpoint disabled in production"}, status=403
        )
    keywords = ["python", "django", "vue", "redis"]
    questions = get_questions_using_openai(
        target_job="software engineer", keywords=keywords
    )
    return JsonResponse(
        {
            "DEBUG": settings.DEBUG,
            "questions": questions,
        },
        status=HTTP_200_OK,
    )
