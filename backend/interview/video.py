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
        
from .models import InterviewSession, Video
from django.core.files.base import ContentFile
import os

def add_video_to_session(session_id, video_file, question_index=None, question_text=""):
    """
    Creates a Video object and associates it with an InterviewSession.

    :param session_id: The UUID of the interview session.
    :param video_file: An uploaded file object (e.g., from request.FILES).
    :param question_index: The index of the question being answered.
    :param question_text: The text of the question being answered.
    :return: The created Video object or None if the session doesn't exist.
    """
    try:
        # 1. Get the parent InterviewSession
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        # Handle case where session is not found
        return None

    # Define where to save the video
    video_dir = os.path.join("videos", str(session.id))
    os.makedirs(os.path.join(settings.MEDIA_ROOT, video_dir), exist_ok=True)
    
    # Create a unique filename
    file_extension = os.path.splitext(video_file.name)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    relative_path = os.path.join(video_dir, unique_filename)
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    # Save the file to the filesystem
    with open(full_path, 'wb+') as destination:
        for chunk in video_file.chunks():
            destination.write(chunk)

    # 2. Create the Video model instance
    new_video = Video.objects.create(
        # 3. Associate it with the session
        interview_session=session,
        
        # 4. Fill in other details
        original_filename=video_file.name,
        file_path=relative_path,
        file_size=video_file.size,
        video_type=Video.VideoType.INTERVIEW_ANSWER, # Or determine this dynamically
        question_index=question_index,
        question_text=question_text,
        status=Video.VideoStatus.UPLOADED
    )
    
    # The video is now created and linked to the session.
    # The .save() is handled by .create()
    
    return new_video

# --- Example Usage (e.g., in a Django view) ---
#
# def upload_video_view(request):
#     session_id = request.POST.get('id')
#     video_file = request.FILES.get('video')
#     
#     if session_id and video_file:
#         video_instance = add_video_to_session(session_id, video_file)
#         if video_instance:
#             return JsonResponse({"message": "Video added successfully!", "video_id": video_instance.id})
#         else:
#             return JsonResponse({"error": "Session not found"}, status=404)
#     
#     return JsonResponse({"error": "Missing session ID or video file"}, status=400)
