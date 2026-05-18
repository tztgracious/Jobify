import uuid

from django.db import models


class InterviewSession(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    class AnswerType(models.TextChoices):
        TEXT = "text", "Text"
        VIDEO = "video", "Video"

    # Primary key - using doc_id as the primary identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User association
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='interview_sessions'
    )

    # Resume-related fields
    resume_local_path = models.CharField(
        max_length=512, default=""
    )
    keywords = models.JSONField(default=list)
    target_job = models.CharField(max_length=255, blank=True, null=True)
    answer_type = models.CharField(
        max_length=10, choices=AnswerType.choices, default=AnswerType.TEXT
    )
    resume_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )
    grammar_results = models.JSONField(blank=True, null=True)

    question_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )

    # DEPRECATED fields (kept for migration safety)
    tech_questions = models.JSONField(default=list, null=True, blank=True)
    tech_answers = models.JSONField(default=list, null=True, blank=True)
    questions = models.JSONField(default=list, null=True, blank=True)
    answers = models.JSONField(default=list, null=True, blank=True)
    feedback = models.JSONField(default=dict, null=True, blank=True)

    is_completed = models.BooleanField(default=False)
    feedback_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    feedback_started = models.DateTimeField(null=True, blank=True)
    feedback_completed = models.DateTimeField(null=True, blank=True)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interview Session {self.id} ({self.resume_status})"

    @property
    def normalized_questions(self):
        """Returns questions in order using the relational models."""
        return self.related_questions.all()

    @property
    def progress(self):
        """Return the progress using normalized Answer models."""
        total_questions = self.related_questions.filter(is_technical=False).count()
        if total_questions == 0:
            return "0/0"
        answered_count = self.related_questions.filter(is_technical=False, answer__isnull=False).count()
        return f"{answered_count}/{total_questions}"

    @property
    def completion_percentage(self):
        """Return completion percentage using normalized models."""
        total_count = self.related_questions.filter(is_technical=False).count()
        if total_count == 0:
            return 0
        answered_count = self.related_questions.filter(is_technical=False, answer__isnull=False).count()
        return round((answered_count / total_count) * 100, 1)

    @property
    def tech_progress(self):
        """Return tech progress using normalized models."""
        total_count = self.related_questions.filter(is_technical=True).count()
        if total_count == 0:
            return "0/0"
        answered_count = self.related_questions.filter(is_technical=True, answer__isnull=False).count()
        return f"{answered_count}/{total_count}"

    @property
    def tech_completion_percentage(self):
        """Return tech completion percentage using normalized models."""
        total_count = self.related_questions.filter(is_technical=True).count()
        if total_count == 0:
            return 0
        answered_count = self.related_questions.filter(is_technical=True, answer__isnull=False).count()
        return round((answered_count / total_count) * 100, 1)

    class Meta:
        ordering = ["-created_at"]
