from django.shortcuts import render

import os
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv

from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .utils import grammar_check, get_keywords_using_openai

load_dotenv('../.api-keys')  # Adjust the path as necessary

LLAMA_API_KEY = os.getenv("LLAMA_PARSE_API_KEY")
LLAMA_API_URL = "https://api.llamaindex.ai/v1/parse"

@api_view(['POST'])
def parse_resume(request):
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    files = {
        'file': (file.name, file.read(), file.content_type)
    }
    headers = {
        "Authorization": f"Bearer {LLAMA_API_KEY}"
    }

    try:
        r = requests.post(LLAMA_API_URL, headers=headers, files=files)
        r.raise_for_status()
        data = r.json()
        return Response({"parsed": data})
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
        "sample_text": sample_text,
        "keywords": keywords,
        "grammar": grammar_result,
        "KEYS": {
            "LLAMA_PARSE_API_KEY": LLAMA_API_KEY,
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "LANGUAGETOOL_API_KEY": os.getenv("LANGUAGETOOL_API_KEY"),
            "EXAMPLE_KEY": os.getenv("EXAMPLE_KEY")
        },
        "DJANGO_SECRET_KEY": os.getenv("DJANGO_SECRET_KEY")
    })