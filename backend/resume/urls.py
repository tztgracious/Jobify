from django.urls import path
from .views import parse_resume, debug_view, upload_resume

urlpatterns = [
    path('upload-resume/', upload_resume, name='upload-resume'),
    path('parse-resume/', parse_resume, name='parse-resume'),
    path('debug/', debug_view, name='debug-view'),
]
