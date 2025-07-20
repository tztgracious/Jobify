from django.urls import path

from .debug import debug_view
from .views import upload_resume, get_keywords, target_job, remove_resume, cleanup_all_resumes, get_grammar_results

urlpatterns = [
    path('upload-resume/', upload_resume, name='upload-resume'),
    path('get-keywords/', get_keywords, name='get-keywords'),
    path('get-grammar-results/', get_grammar_results, name='get-grammar-results'),
    path('target-job/', target_job, name='target-job'),
    path('remove-resume/', remove_resume, name='remove-resume'),
    path('cleanup-all-resumes/', cleanup_all_resumes, name='cleanup-all-resumes'),
    path('debug/', debug_view, name='debug-view'),
]
