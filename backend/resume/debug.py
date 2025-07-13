import os

from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_200_OK


@api_view(['GET'])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "Debug endpoint disabled in production"}, status=403)

    return JsonResponse({
        "DEBUG": settings.DEBUG,
        "DATABASES": settings.DB_ENGINE,
        "KEYS": {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        },
    }, status=HTTP_200_OK)
