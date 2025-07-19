from django.urls import path

from .views import get_interview_questions, submit_answer, get_feedback

urlpatterns = [
    path('get-questions/', get_interview_questions, name='get-questions'),
    path('submit-answer/', submit_answer, name='submit-answer'),
    path('feedback/', get_feedback, name='get-feedback'),
]
