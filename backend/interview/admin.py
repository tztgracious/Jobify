from django.contrib import admin

from .models.interview_session import InterviewSession


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_job', 'resume_status', 'answer_type', 'progress', 'tech_progress', 'completion_percentage', 'tech_completion_percentage', 'is_completed', 'uploaded_at', 'created_at')
    list_filter = ('resume_status', 'answer_type', 'is_completed', 'uploaded_at', 'created_at')
    search_fields = ('id', 'target_job', 'resume_local_path')
    readonly_fields = ('id', 'uploaded_at', 'created_at', 'updated_at', 'progress', 'completion_percentage', 'tech_progress', 'tech_completion_percentage')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'target_job', 'answer_type', 'resume_status', 'question_status', 'is_completed')
        }),
        ('Resume Fields', {
            'fields': ('resume_local_path', 'keywords', 'grammar_results')
        }),
        ('Technical Interview', {
            'fields': ('tech_questions', 'tech_answers', 'tech_feedback')
        }),
        ('General Interview', {
            'fields': ('questions', 'answers', 'feedback')
        }),
        ('Progress Tracking', {
            'fields': ('progress', 'completion_percentage', 'tech_progress', 'tech_completion_percentage')
        }),
        ('Metadata', {
            'fields': ('uploaded_at', 'created_at', 'updated_at')
        }),
    )
