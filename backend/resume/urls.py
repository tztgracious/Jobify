from django.urls import path

from .debug import debug_view
from .views import upload_resume, get_keywords, target_job, get_interview_questions

urlpatterns = [
    path('upload-resume/', upload_resume, name='upload-resume'),
    path('get-keywords/', get_keywords, name='get-keywords'),
    path('target-job/', target_job, name='target-job'),
    path('get-questions/', get_interview_questions, name='get-questions'),
    path('debug/', debug_view, name='debug-view'),
]
