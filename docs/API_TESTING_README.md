# Django API Testing Scripts

This directory contains two scripts to test all Django APIs for the Jobify project:

## Scripts Available

### 1. Bash Script (`test_django_apis.sh`)

- Uses curl commands
- Works on any system with bash and curl
- Saves responses to JSON files
- Color-coded output

### 2. Python Script (`test_django_apis.py`)

- Uses Python requests library
- More detailed error handling
- JSON parsing and formatting
- Requires Python 3.6+

## Usage

### Quick Start

```bash
# Run the bash version (recommended for servers)
./test_django_apis.sh

# Run the Python version (recommended for development)
python3 test_django_apis.py
```

### Configuration

Edit the `BASE_URL` variable in either script:

```bash
# For production server
BASE_URL="http://115.29.170.231"

# For local testing
BASE_URL="http://localhost:8000"
```

### What the scripts test

Both scripts automatically use a realistic professional resume PDF for testing:

1. **Upload Resume** - Uses `backend/test/fixtures/professional_resume.pdf` (or creates minimal PDF if not found)
   - Success case with realistic resume
   - No file error case
   - Invalid file type error case
2. **Get Keywords** - Valid doc_id, missing doc_id, invalid doc_id
3. **Target Job** - Valid data, missing fields, invalid doc_id
4. **Get Interview Questions** - Valid doc_id, missing doc_id
5. **Debug Endpoint** - Server configuration info
6. **User Signup** - New user registration

### Output

Both scripts provide:

- ✅ Green checkmarks for passing tests
- ❌ Red X marks for failing tests
- 📄 Response data saved to files
- 📊 Final summary with pass/fail counts

### Response Files

The scripts save API responses to files like:

- `response_upload_resume_success.json`
- `response_get_keywords_valid.json`
- `response_target_job_valid.json`

### Example Output

```
🚀 Starting Django API Tests for Jobify
Base URL: http://115.29.170.231

===========================================
Testing: Upload Resume - Success
===========================================
✅ PASS: POST /api/v1/upload-resume/ (valid PDF) (Status: 201)
📋 Extracted doc_id: 12f4f5a8-9d20-43a6-8104-0b03cfd56ab3

===========================================
Testing: Get Keywords - Valid doc_id
===========================================
✅ PASS: POST /api/v1/get-keywords/ (valid doc_id) (Status: 200)

📊 TEST SUMMARY
✅ Passed: 12
❌ Failed: 0
📋 Total:  12
🎉 All tests passed!
```

### Prerequisites

For the Python script:

```bash
pip install requests
```

For the bash script:

```bash
# Usually pre-installed on most systems
curl --version
```

### Troubleshooting

1. **Connection errors**: Check if your Django server is running
2. **404 errors**: Verify the BASE_URL is correct
3. **Permission denied**: Run `chmod +x test_django_apis.sh`
4. **Python import errors**: Install requests with `pip install requests`

### Running on Server

```bash
# SSH into your server
ssh root@115.29.170.231

# Navigate to project directory
cd Jobify

# Run the bash script (no additional dependencies)
./test_django_apis.sh

# Or run the Python script (if requests is installed)
python3 test_django_apis.py
```

## Integration with CI/CD

You can use these scripts in your deployment pipeline:

```bash
# In your deployment script
./test_django_apis.sh
if [ $? -eq 0 ]; then
    echo "All API tests passed, deployment successful"
else
    echo "API tests failed, rolling back deployment"
    exit 1
fi
```
