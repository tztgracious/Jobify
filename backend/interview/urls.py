from django.urls import path

from .views import (
    cleanup_all_videos,
    get_all_questions,
    get_feedback,
    ping,
    submit_interview_answer,
    submit_tech_answer,
)

urlpatterns = [
    path("ping/", ping, name="ping"),
    path("get-all-questions/", get_all_questions, name="get-all-questions"),
    path("submit-tech-answer/", submit_tech_answer, name="submit-tech-answer"),
    path(
        "submit-interview-answer/",
        submit_interview_answer,
        name="submit-interview-answer",
    ),
    path("feedback/", get_feedback, name="get-feedback"),
    path("cleanup-all-videos/", cleanup_all_videos, name="cleanup-all-videos"),
]
