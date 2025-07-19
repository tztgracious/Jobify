from django.contrib import admin

from .models import InterviewSession


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'resume', 'doc_id', 'progress', 'completion_percentage', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'created_at')
    search_fields = ('doc_id', 'resume__id')
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
