import uuid

from django.db import models


class ParsedResume(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    original_file = models.FileField(upload_to='resumes/')
    parsed_text = models.TextField(blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Resume(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local_path = models.CharField(max_length=512)  # e.g. "resumes/123e4567-e89b-12d3-a456-426614174000.pdf"
    keywords = models.JSONField(default=list)  # stores like ["python", "django"]
    target_job = models.CharField(max_length=255, blank=True, null=True)
    questions = models.JSONField(default=list)  # stores like ["Why choose python?", "Describe a team project"]
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    grammar_results = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.id} ({self.status})"

    class Meta:
        ordering = ['-uploaded_at']


# NOT in use.
class TargetJob(models.Model):
    """
    Model to store user's target job preferences
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)  # e.g. "Software Engineer"
    location = models.CharField(max_length=255)  # e.g. "Remote" or "San Francisco, CA"
    salary_range = models.CharField(max_length=100)  # e.g. "80k-100k" or "$80,000 - $100,000"
    tags = models.JSONField(default=list)  # e.g. ["python", "django", "rest"]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.location}"

    class Meta:
        ordering = ['-created_at']
