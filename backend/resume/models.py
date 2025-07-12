from django.db import models
import uuid

class ParsedResume(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    original_file = models.FileField(upload_to='resumes/')
    parsed_text = models.TextField(blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local_path = models.CharField(max_length=512)  # e.g. "resumes/123e4567-e89b-12d3-a456-426614174000.pdf"
    keywords = models.JSONField(default=list)      # stores like ["python", "django"]
    target_job = models.CharField(max_length=255, blank=True, null=True)
    questions = models.JSONField(default=list)     # stores like ["Why choose python?", "Describe a team project"]
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume {self.id}"

    class Meta:
        ordering = ['-uploaded_at']
