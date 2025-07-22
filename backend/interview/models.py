import uuid

from django.db import models


class InterviewSession(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'
    
    class AnswerType(models.TextChoices):
        TEXT = 'text', 'Text'
        VIDEO = 'video', 'Video'

    # Primary key - using doc_id as the primary identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Resume-related fields (moved from Resume model)
    resume_local_path = models.CharField(max_length=512, default='')  # e.g. "resumes/123e4567-e89b-12d3-a456-426614174000.pdf"
    keywords = models.JSONField(default=list)  # stores like ["python", "django"]
    target_job = models.CharField(max_length=255, blank=True, null=True)
    answer_type = models.CharField(max_length=10, choices=AnswerType.choices, default=AnswerType.TEXT)
    resume_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    grammar_results = models.JSONField(blank=True, null=True)

    question_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    # Technical interview fields
    tech_questions = models.JSONField(default=list)  # ["Tech Question 1?", "Tech Question 2?", "Tech Question 3?"]
    tech_answers = models.JSONField(default=list)  # ["Tech Answer 1", "Tech Answer 2", "Tech Answer 3"]
    tech_feedback = models.TextField(blank=True, null=True)

    # General interview fields
    questions = models.JSONField(default=list)  # ["Question 1?", "Question 2?", "Question 3?"]
    answers = models.JSONField(default=list)  # ["Answer 1", "Answer 2", "Answer 3"]
    feedback = models.JSONField(default=dict)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)  # When resume was uploaded
    created_at = models.DateTimeField(auto_now_add=True)   # When session was created
    updated_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)  # Track if all questions are answered

    def __str__(self):
        return f"Interview Session {self.id} ({self.resume_status})"

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

    @property
    def tech_progress(self):
        """Return the number of answered technical questions out of total technical questions"""
        answered_count = len([answer for answer in self.tech_answers if answer and answer.strip()])
        total_count = len(self.tech_questions)
        return f"{answered_count}/{total_count}"

    @property
    def tech_completion_percentage(self):
        """Return technical questions completion percentage"""
        if not self.tech_questions:
            return 0
        answered_count = len([answer for answer in self.tech_answers if answer and answer.strip()])
        return round((answered_count / len(self.tech_questions)) * 100, 1)

    class Meta:
        ordering = ['-created_at']
