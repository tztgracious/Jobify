# Secure Video Cleanup Endpoint Documentation

## Overview

The `cleanup_all_videos` endpoint is a **destructive operation** that removes ALL video files from the server's media directories. It includes multiple security layers to prevent accidental or malicious use.

```bash
curl -k -X POST https://115.29.170.231/api/v1/cleanup-all-videos/ \
  -H "Content-Type: application/json" \
  -d '{
    "confirmation_token": "CONFIRM_DELETE_ALL_VIDEOS_2025",
    "confirm_action": "DELETE_ALL_VIDEO_DATA"
  }'
```

## Endpoint Details

- **URL**: `/api/v1/cleanup-all-videos/`
- **Method**: POST
- **Purpose**: Remove all video files from media directories (for testing/development cleanup)

## Security Measures

### 1. Environment Restriction

- **Only works when `DEBUG=True`** (development/testing mode)
- Automatically blocked in production environments
- Returns `403 Forbidden` if attempted in production

### 2. Authentication Requirements

- **Confirmation Token**: Must provide correct `confirmation_token`
- **Action Confirmation**: Must provide `confirm_action` field
- Returns `401 Unauthorized` for invalid tokens
- Returns `400 Bad Request` for missing confirmations

### 3. Comprehensive Logging

- Logs all access attempts (successful and failed)
- Records IP address and User-Agent
- Tracks file operations and directory processing
- Provides detailed audit trail

### 4. Detailed Response

- Returns statistics of operations performed
- Shows files removed, failed operations, directories processed
- Provides timestamps for audit purposes

## Video File Types Supported

The endpoint removes video files with the following extensions:
- `.mp4` - MPEG-4 Video
- `.avi` - Audio Video Interleave
- `.mov` - QuickTime Movie
- `.mkv` - Matroska Video
- `.webm` - WebM Video
- `.m4v` - iTunes Video
- `.3gp` - 3GPP Multimedia
- `.flv` - Flash Video

## Directories Cleaned

The endpoint processes the following directories:
- `media/videos/` - General video uploads
- `media/interview_videos/` - Interview video answers

## Request Format

```json
{
  "confirmation_token": "CONFIRM_DELETE_ALL_VIDEOS_2025",
  "confirm_action": "DELETE_ALL_VIDEO_DATA"
}
```

## Response Format

### Success Response (200 OK)

```json
{
  "success": true,
  "operation": "cleanup_all_videos",
  "timestamp": 1642694400.0,
  "statistics": {
    "total_files_before": 25,
    "directories_processed": 2,
    "files_removed": 25,
    "files_failed": 0,
    "cleanup_errors": []
  },
  "message": "Video cleanup operation completed"
}
```

### Partial Success Response (206 Partial Content)

```json
{
  "success": false,
  "operation": "cleanup_all_videos",
  "timestamp": 1642694400.0,
  "statistics": {
    "total_files_before": 20,
    "directories_processed": 2,
    "files_removed": 18,
    "files_failed": 2,
    "cleanup_errors": ["Failed to remove video file corrupted_video.mp4: Permission denied"]
  },
  "message": "Video cleanup completed with errors"
}
```

### Error Responses

#### Production Environment (403 Forbidden)

```json
{
  "success": false,
  "error": "This operation is only allowed in development mode"
}
```

#### Invalid Token (401 Unauthorized)

```json
{
  "success": false,
  "error": "Invalid confirmation token required for this destructive operation"
}
```

#### Missing Confirmation (400 Bad Request)

```json
{
  "success": false,
  "error": "Must confirm action with 'DELETE_ALL_VIDEO_DATA'"
}
```

## Usage Examples

### Using curl

```bash
# This will work in development (DEBUG=True)
curl -X POST http://localhost:8000/api/v1/cleanup-all-videos/ \
  -H "Content-Type: application/json" \
  -d '{
    "confirmation_token": "CONFIRM_DELETE_ALL_VIDEOS_2025",
    "confirm_action": "DELETE_ALL_VIDEO_DATA"
  }'
```

### Using Python requests

```python
import requests

# Development environment
data = {
    "confirmation_token": "CONFIRM_DELETE_ALL_VIDEOS_2025",
    "confirm_action": "DELETE_ALL_VIDEO_DATA"
}

response = requests.post(
    "http://localhost:8000/api/v1/cleanup-all-videos/",
    json=data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## Security Best Practices

### 1. Token Management

- Change the confirmation token periodically
- Use a complex, unpredictable token
- Never expose tokens in client-side code
- Set custom token via environment variable `DELETE_ALL_VIDEOS_TOKEN`

### 2. Access Control

- Only provide access to authorized developers
- Use in controlled testing environments only
- Monitor usage through logs

### 3. Testing Strategy

- Use only in development/testing environments
- Create test video files before cleanup operations
- Verify backups exist before running in any environment

### 4. Monitoring

- Monitor `jobify.log` for cleanup operations
- Set up alerts for unauthorized access attempts
- Regular audit of cleanup operations

## Logging Details

The endpoint logs the following information:

- Request timestamp and IP address
- User-Agent string
- All security check results
- File operations (success/failure)
- Directory processing status
- Final operation statistics

Example log entries:

```
2025-01-15 10:30:00 - jobify - WARNING - cleanup_all_videos:445 - === CLEANUP ALL VIDEOS REQUEST STARTED ===
2025-01-15 10:30:00 - jobify - INFO - cleanup_all_videos:447 - Request IP: 127.0.0.1
2025-01-15 10:30:00 - jobify - WARNING - cleanup_all_videos:470 - === STARTING DESTRUCTIVE VIDEO CLEANUP OPERATION ===
2025-01-15 10:30:01 - jobify - WARNING - cleanup_all_videos:550 - === VIDEO CLEANUP OPERATION COMPLETED ===
```

## Testing

Create a test script to verify:

1. Security measures are working
2. Proper error handling
3. Successful cleanup operations
4. Production environment blocking
5. Video file type detection

## Environment Variables

- `DELETE_ALL_VIDEOS_TOKEN`: Custom confirmation token (defaults to "CONFIRM_DELETE_ALL_VIDEOS_2025")

## Important Notes

⚠️ **WARNING**: This is a destructive operation that cannot be undone!

- Always backup video data before using
- Only use in development/testing environments
- Verify `DEBUG=True` in settings before testing
- Monitor logs for security events
- Change tokens regularly for security
- Ensure proper file permissions in media directories

## Differences from Resume Cleanup

Unlike the resume cleanup endpoint, this video cleanup endpoint:
- Does not modify database records (videos are stored as files only)
- Processes multiple directories (`videos/` and `interview_videos/`)
- Handles multiple video file formats
- Focuses purely on file system cleanup
- Returns directory processing statistics

## Related Endpoints

- `/api/v1/cleanup-all-resumes/` - Removes all resume files and database entries
- `/api/v1/upload-video/` - Uploads video files for interview answers
- `/api/v1/submit-interview-answer/` - Submits video answers to interview questions
