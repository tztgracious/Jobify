# Secure Cleanup Endpoint Documentation

## Overview

The `cleanup_all_resumes` endpoint is a **destructive operation** that removes ALL resume files from the media directory and ALL resume database entries. It includes multiple security layers to prevent accidental or malicious use.

```bash
curl -k -X POST https://115.29.170.231/api/v1/cleanup-all-resumes/ \
  -H "Content-Type: application/json" \
  -d '{
    "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
    "confirm_action": "DELETE_ALL_RESUME_DATA"
  }'
```

## Endpoint Details

- **URL**: `/api/v1/cleanup-all-resumes/`
- **Method**: POST
- **Purpose**: Remove all resume files and database entries (for testing/development cleanup)

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
- Tracks file and database operations
- Provides detailed audit trail

### 4. Detailed Response

- Returns statistics of operations performed
- Shows files removed, failed operations, database records affected
- Provides timestamps for audit purposes

## Request Format

```json
{
  "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
  "confirm_action": "DELETE_ALL_RESUME_DATA"
}
```

## Response Format

### Success Response (200 OK)

```json
{
  "success": true,
  "operation": "cleanup_all_resumes",
  "timestamp": 1642694400.0,
  "statistics": {
    "total_resumes_before": 15,
    "total_files_before": 12,
    "files_removed": 12,
    "files_failed": 0,
    "db_records_removed": 15,
    "db_errors": []
  },
  "message": "Cleanup operation completed"
}
```

### Partial Success Response (206 Partial Content)

```json
{
  "success": false,
  "operation": "cleanup_all_resumes",
  "timestamp": 1642694400.0,
  "statistics": {
    "total_resumes_before": 10,
    "total_files_before": 8,
    "files_removed": 7,
    "files_failed": 1,
    "db_records_removed": 10,
    "db_errors": ["Some database error"]
  },
  "message": "Cleanup completed with errors"
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
  "error": "Must confirm action with 'DELETE_ALL_RESUME_DATA'"
}
```

## Usage Examples

### Using curl

```bash
# This will work in development (DEBUG=True)
curl -X POST http://localhost:8000/api/v1/cleanup-all-resumes/ \
  -H "Content-Type: application/json" \
  -d '{
    "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
    "confirm_action": "DELETE_ALL_RESUME_DATA"
  }'
```

### Using Python requests

```python
import requests

# Development environment
data = {
    "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
    "confirm_action": "DELETE_ALL_RESUME_DATA"
}

response = requests.post(
    "http://localhost:8000/api/v1/cleanup-all-resumes/",
    data=data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## Security Best Practices

### 1. Token Management

- Change the confirmation token periodically
- Use a complex, unpredictable token
- Never expose tokens in client-side code

### 2. Access Control

- Only provide access to authorized developers
- Use in controlled testing environments only
- Monitor usage through logs

### 3. Testing Strategy

- Use only in development/testing environments
- Create test data before cleanup operations
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
- Database operations
- Final operation statistics

Example log entries:

```
2025-01-15 10:30:00 - jobify - WARNING - cleanup_all_resumes:385 - === CLEANUP ALL RESUMES REQUEST STARTED ===
2025-01-15 10:30:00 - jobify - INFO - cleanup_all_resumes:387 - Request IP: 127.0.0.1
2025-01-15 10:30:00 - jobify - WARNING - cleanup_all_resumes:410 - === STARTING DESTRUCTIVE CLEANUP OPERATION ===
2025-01-15 10:30:01 - jobify - WARNING - cleanup_all_resumes:470 - === CLEANUP OPERATION COMPLETED ===
```

## Testing

Use the provided test script (`test_cleanup_endpoint.py`) to verify:

1. Security measures are working
2. Proper error handling
3. Successful cleanup operations
4. Production environment blocking

## Important Notes

⚠️ **WARNING**: This is a destructive operation that cannot be undone!

- Always backup data before using
- Only use in development/testing environments
- Verify `DEBUG=True` in settings before testing
- Monitor logs for security events
- Change tokens regularly for security
