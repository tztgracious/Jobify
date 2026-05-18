import uuid
from django.db import models

class Question(models.Model):
    """
    Model representing an interview question within a session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        'interview.InterviewSession',
        on_delete=models.CASCADE,
        related_name='related_questions'
    )
    text = models.TextField()
    is_technical = models.BooleanField(default=False)
    index = models.IntegerField(help_text="Order of the question in its category (tech or general)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_technical', 'index']
        unique_together = ['session', 'index', 'is_technical']

    def __str__(self):
        q_type = "Tech" if self.is_technical else "General"
        return f"{q_type} Q{self.index} - Session {self.session_id}"
