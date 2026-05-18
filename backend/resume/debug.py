from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_200_OK
from .services import ResumeService

@api_view(["GET"])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse(
            {"error": "Debug endpoint disabled in production"}, status=403
        )
    session_id = "e6e1bf9856ab47118ca1ed614f5cf320"
    session = ResumeService.get_session_by_id(session_id)
    if session:
        # For debug, we can trigger question generation manually
        from interview.utils import get_questions_using_openai_multi_agent
        get_questions_using_openai_multi_agent(session)
    
    return JsonResponse(
        {
            "DEBUG": settings.DEBUG,
            "session_found": session is not None,
        },
        status=HTTP_200_OK,
    )
