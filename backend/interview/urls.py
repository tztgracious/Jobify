from django.urls import path

from .views import (
    get_all_questions,
    get_interview_questions,
    submit_interview_answer,
    submit_tech_answer,
    get_feedback,
)

urlpatterns = [
    path('get-all-questions/', get_all_questions, name='get-all-questions'),
    path('get-interview-questions/', get_interview_questions, name='get-interview-questions'),
    path('submit-tech-answer/', submit_tech_answer, name='submit-tech-answer'),
    path('submit-interview-answer/', submit_interview_answer, name='submit-interview-answer'),
    path('feedback/', get_feedback, name='get-feedback'),
]
