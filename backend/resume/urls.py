from django.urls import path
from .views import parse_resume, debug_view

urlpatterns = [
    path('parse-resume/', parse_resume, name='parse-resume'),
    path('debug/', debug_view, name='debug-view'),
]
