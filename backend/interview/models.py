import uuid
from django.db import models
from resume.models import Resume


class InterviewSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='interview_sessions')
    doc_id = models.UUIDField()  # Link to the doc_id from resume processing
    questions = models.JSONField(default=list)  # ["Question 1?", "Question 2?", "Question 3?"]
    answers = models.JSONField(default=list)    # ["Answer 1", "Answer 2", "Answer 3"]
    feedback = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)  # Track if all questions are answered
    
    def __str__(self):
        return f"Interview Session for resume {self.resume.id}"
    
    @property
    def progress(self):
        """Return the number of answered questions out of total questions"""
        answered_count = len([answer for answer in self.answers if answer and answer.strip()])
        total_count = len(self.questions)
        return f"{answered_count}/{total_count}"
    
    @property
    def completion_percentage(self):
        """Return completion percentage"""
        if not self.questions:
            return 0
        answered_count = len([answer for answer in self.answers if answer and answer.strip()])
        return round((answered_count / len(self.questions)) * 100, 1)
    
    class Meta:
        ordering = ['-created_at']
