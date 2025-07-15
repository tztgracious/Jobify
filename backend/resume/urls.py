from django.urls import path

from .debug import debug_view
from .views import upload_resume, get_keywords, target_job, ask_graphrag

urlpatterns = [
    path("graphrag/ask/", ask_graphrag),
    path('upload-resume/', upload_resume, name='upload-resume'),
    path('get-keywords/', get_keywords, name='get-keywords'),
    path('target-job/', target_job, name='target-job'),
    path('debug/', debug_view, name='debug-view'),
]
