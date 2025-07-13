from django.contrib import admin
from .models import ParsedResume, Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'local_path', 'uploaded_at', 'target_job')
    list_filter = ('uploaded_at', 'target_job')
    search_fields = ('id', 'target_job')
    readonly_fields = ('id', 'uploaded_at')
    
    def has_add_permission(self, request):
        # Prevent manual creation through admin - should be uploaded via API
        return False

@admin.register(ParsedResume)
class ParsedResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('user__email',)
