from rest_framework import serializers

from .models import InterviewSession


class InterviewSessionSerializer(serializers.ModelSerializer):
    progress = serializers.ReadOnlyField()

    class Meta:
        model = InterviewSession
        fields = [
            "id",
            "resume",
            "doc_id",
            "questions",
            "answers",
            "feedback",
            "created_at",
            "updated_at",
            "is_completed",
            "progress",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InterviewSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new interview sessions"""

    class Meta:
        model = InterviewSession
        fields = ["resume", "doc_id", "questions"]


class InterviewSessionAnswerSerializer(serializers.ModelSerializer):
    """Serializer for updating answers in interview sessions"""

    class Meta:
        model = InterviewSession
        fields = ["answers", "is_completed"]
