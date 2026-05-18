import uuid
from django.db import models

class Feedback(models.Model):
    """
    Model representing detailed AI-generated feedback for an answer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(
        'interview.Question',
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    score = models.IntegerField(null=True, blank=True, help_text="Score from 1-10")
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    feedback_text = models.TextField(blank=True, help_text="Detailed feedback commentary")
    improvement_tips = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.question}"
