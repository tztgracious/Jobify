from django.db import models

class ParsedResume(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    original_file = models.FileField(upload_to='resumes/')
    parsed_text = models.TextField(blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
