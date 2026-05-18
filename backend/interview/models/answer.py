import uuid
from django.db import models

class Answer(models.Model):
    """
    Model representing a candidate's answer to a specific question.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(
        'interview.Question',
        on_delete=models.CASCADE,
        related_name='answer'
    )
    text = models.TextField(blank=True, help_text="Text content of the answer or transcription")
    video = models.ForeignKey(
        'interview.Video',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_answer'
    )
    is_video = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer to {self.question}"
