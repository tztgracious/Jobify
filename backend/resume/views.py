import os

import requests
from django.conf import settings
from django.http import JsonResponse
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .utils import grammar_check, get_keywords_using_openai
from accounts.decorators import login_required_api


@api_view(['POST'])
@login_required_api
def parse_resume(request):
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    files = {
        'file': (file.name, file.read(), file.content_type)
    }
    headers = {
        "Authorization": f"Bearer {settings.LLAMA_API_KEY}"
    }

    try:
        r = requests.post(settings.LLAMA_API_URL, headers=headers, files=files)
        r.raise_for_status()
        data = r.json()
        return Response({"parsed": data}, status=HTTP_200_OK)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
def debug_view(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "Debug endpoint disabled in production"}, status=403)

    sample_text = "My name is Alice and I have 3 years experience in machine learning."

    # run your functions
    keywords = get_keywords_using_openai(sample_text)
    grammar_result = grammar_check(sample_text)
    return JsonResponse({
        "DEBUG": settings.DEBUG,
        "DATABASES": settings.DB_ENGINE,
        "KEYS": {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "LANGUAGETOOL_API_KEY": os.getenv("LANGUAGETOOL_API_KEY"),
            "EXAMPLE_KEY": os.getenv("EXAMPLE_KEY")
        },
    }, status=HTTP_200_OK)
