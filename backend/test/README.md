# API Integration Tests

This directory contains pytest-based integration tests for the Jobify API endpoints.

## Files

- `test_api_integration.py` - Main integration test suite
- `test_resume_flow.py` - Existing Django unit tests
- `test_server_apis.py` - Existing server API tests
- `fixtures/` - Test data files (PDFs, etc.)

## Running the Tests

### Prerequisites

1. Make sure the Django server is running on the configured URL
2. Install pytest dependencies:
   ```bash
   pip install pytest pytest-django requests
   ```

### Run All Tests

```bash
# From the project root directory
pytest backend/test/

# Or with more verbose output
pytest -v backend/test/
```

### Run Specific Test Files

```bash
# Run only integration tests
pytest backend/test/test_api_integration.py

# Run only unit tests
pytest backend/test/test_resume_flow.py
```

### Run Specific Test Methods

```bash
# Run a specific test method
pytest backend/test/test_api_integration.py::TestAPIIntegration::test_upload_resume_success

# Run tests matching a pattern
pytest -k "upload" backend/test/
```

### Run with Markers

```bash
# Run only integration tests
pytest -m integration backend/test/

# Skip slow tests
pytest -m "not slow" backend/test/
```

## Configuration

### Server URL

Edit the `BASE_URL` in `test_api_integration.py` to match your server:

```python
BASE_URL = "https://115.29.170.231"  # Production server
# BASE_URL = "http://localhost:8000"  # Local development
```

### SSL Configuration

For self-signed certificates, set:

```python
VERIFY_SSL = False
```

For production with valid certificates:

```python
VERIFY_SSL = True
```

## Test Features

### Test Structure

- **Fixtures**: Shared test setup and teardown
- **Class-based**: Organized test methods in classes
- **Retry Logic**: Automatic retry for async operations
- **Response Parsing**: Handles both JSON and HTML responses
- **Error Handling**: Comprehensive error reporting

### Test Coverage

The integration tests cover:

1. **Debug Endpoint** - Server status and configuration
2. **Resume Upload** - File upload with validation
3. **Keyword Extraction** - Resume processing and keyword extraction
4. **Target Job** - Job preference setting
5. **Interview Questions** - Question generation
6. **Error Handling** - Invalid inputs and edge cases

### Test Data

Tests use PDF files from the `fixtures/` directory:
- `professional_resume.pdf` - Primary test file
- Fallback: Minimal PDF generated on-the-fly

## Output

### Success Output

```
================================= test session starts =================================
backend/test/test_api_integration.py::TestAPIIntegration::test_debug_endpoint PASSED
backend/test/test_api_integration.py::TestAPIIntegration::test_upload_resume_success PASSED
backend/test/test_api_integration.py::TestAPIIntegration::test_get_keywords_valid PASSED
================================== 10 passed in 45.2s ==================================
```

### Failure Output

```
================================== FAILURES ==================================
_______ TestAPIIntegration.test_upload_resume_success _______

    def test_upload_resume_success(self, api_tester):
        response = requests.post(f"{api_tester.base_url}/api/v1/upload-resume/", ...)
>       assert response.status_code == 201
E       assert 500 == 201

backend/test/test_api_integration.py:123: AssertionError
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check server URL and network connectivity
2. **SSL Errors**: Verify SSL configuration
3. **Timeout Errors**: Increase timeout in pytest configuration
4. **File Not Found**: Ensure test fixtures exist

### Debug Mode

Run with more verbose output:

```bash
pytest -v -s backend/test/test_api_integration.py
```

### Specific Test Debugging

```bash
# Run single test with full output
pytest -v -s backend/test/test_api_integration.py::TestAPIIntegration::test_upload_resume_success
```
