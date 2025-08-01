import uuid
import os
from django.db import models
from django.conf import settings


class Video(models.Model):
    class VideoType(models.TextChoices):
        INTERVIEW_ANSWER = "interview_answer", "Interview Answer"
        TECH_ANSWER = "tech_answer", "Technical Answer"
        GENERAL = "general", "General"

    class VideoStatus(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Foreign key to InterviewSession
    interview_session = models.ForeignKey(
        'interview.InterviewSession',  # Use string reference to avoid circular imports
        on_delete=models.CASCADE,
        related_name='videos'
    )

    # Video metadata
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)  # Path relative to MEDIA_ROOT
    file_size = models.BigIntegerField(help_text="File size in bytes")
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")

    # Video type and context
    video_type = models.CharField(
        max_length=20,
        choices=VideoType.choices,
        default=VideoType.GENERAL
    )
    question_index = models.IntegerField(
        null=True,
        blank=True,
        help_text="Index of the question this video answers (0-based)"
    )
    question_text = models.TextField(
        blank=True,
        help_text="The question this video is answering"
    )

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=VideoStatus.choices,
        default=VideoStatus.UPLOADED
    )

    # Processing results
    transcription = models.TextField(
        blank=True,
        help_text="Transcribed text from the video"
    )
    analysis_results = models.JSONField(
        default=dict,
        help_text="AI analysis results (sentiment, keywords, etc.)"
    )

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Video {self.original_filename} for Session {self.interview_session.id}"

    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def full_file_path(self):
        """Return full file path including MEDIA_ROOT"""
        return os.path.join(settings.MEDIA_ROOT, self.file_path)

    @property
    def is_processed(self):
        """Check if video has been processed"""
        return self.status == self.VideoStatus.PROCESSED

    def delete(self, *args, **kwargs):
        """Delete the video file when the model is deleted"""
        try:
            if os.path.exists(self.full_file_path):
                os.remove(self.full_file_path)
        except Exception as e:
            # Log the error but don't prevent deletion
            try:
                from jobify_backend.logger import logger
                logger.error(f"Failed to delete video file {self.full_file_path}: {e}")
            except ImportError:
                pass  # Fallback if logger is not available

        super().delete(*args, **kwargs)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=['interview_session', 'video_type']),
            models.Index(fields=['interview_session', 'question_index']),
            models.Index(fields=['status']),
        ]