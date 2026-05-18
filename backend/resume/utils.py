import os
from django.conf import settings
from jobify_backend.logger import logger

def get_file_size_mb(file_size_bytes):
    """Convert bytes to MB for user display"""
    return round(file_size_bytes / (1024 * 1024), 2)


def check_file_size_with_message(file, max_size_mb=5):
    """Check file size."""
    max_size_bytes = max_size_mb * 1024 * 1024

    if file.size > max_size_bytes:
        current_size = get_file_size_mb(file.size)
        return False, f"File size ({current_size} MB) exceeds limit ({max_size_mb} MB)"

    return True, None
