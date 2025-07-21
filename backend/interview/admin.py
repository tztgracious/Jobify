from django.contrib import admin

from .models import InterviewSession


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_job', 'status', 'answer_type', 'progress', 'completion_percentage', 'is_completed', 'uploaded_at', 'created_at')
    list_filter = ('status', 'answer_type', 'is_completed', 'uploaded_at', 'created_at')
    search_fields = ('id', 'target_job', 'local_path')
    readonly_fields = ('id', 'uploaded_at', 'created_at', 'updated_at', 'progress', 'completion_percentage')
    readonly_fields = ('id', 'created_at', 'updated_at', 'progress', 'completion_percentage')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'resume', 'doc_id', 'is_completed')
        }),
        ('Interview Content', {
            'fields': ('questions', 'answers', 'feedback')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'progress', 'completion_percentage')
        }),
    )
