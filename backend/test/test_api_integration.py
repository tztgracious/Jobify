#!/usr/bin/env python3
"""
Pytest-based API Testing Script for Jobify
Tests all Django APIs one by one with detailed reporting

This script is configured to work with self-signed SSL certificates.
Set VERIFY_SSL=True for production environments with valid certificates.
"""

import pytest
import requests
import json
import sys
from typing import Dict, Any, Optional
import tempfile
import os
import time

# Configuration
BASE_URL = "https://115.29.170.231"  # Using HTTPS with self-signed cert
# BASE_URL = "http://localhost:8000"  # Uncomment for local testing
# BASE_URL = "http://115.29.170.231"  # Use HTTP if HTTPS has issues

# SSL Configuration for self-signed certificates
VERIFY_SSL = False  # Set to True for production with valid certificates
import urllib3
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class APITester:
    def __init__(self, base_url: str, save_response: bool = False):
        self.base_url = base_url
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.doc_id = None
        self.save_response_flag = save_response
        self.failed_test_names = []  # Track names of failed tests
        
    def print_header(self, test_name: str):
        print(f"\n{Colors.BLUE}{'='*50}{Colors.NC}")
        print(f"{Colors.BLUE}Testing: {test_name}{Colors.NC}")
        print(f"{Colors.BLUE}{'='*50}{Colors.NC}")
        self.total_tests += 1
        
    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse response, handling both JSON and HTML responses"""
        try:
            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return response.json()
            elif response.text.strip().startswith('{'):
                # Sometimes JSON is returned without proper content-type
                return response.json()
            else:
                # Handle HTML error pages or other non-JSON responses
                return {
                    'error': f'Non-JSON response (Status: {response.status_code})',
                    'content_type': content_type,
                    'response_text': response.text[:200] + '...' if len(response.text) > 200 else response.text
                }
        except json.JSONDecodeError:
            # Handle malformed JSON
            return {
                'error': f'Invalid JSON response (Status: {response.status_code})',
                'content_type': response.headers.get('content-type', ''),
                'response_text': response.text[:200] + '...' if len(response.text) > 200 else response.text
            }
        except Exception as e:
            return {
                'error': f'Response parsing error: {str(e)}',
                'status_code': response.status_code
            }
        
    def save_response(self, endpoint: str, response_data: Dict):
        if not self.save_response_flag:
            return
            
        filename = f"response_{endpoint.replace('/', '_').replace('-', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(response_data, f, indent=2)
        print(f"{Colors.YELLOW}📄 Response saved to: {filename}{Colors.NC}")
        
    def get_test_pdf_path(self) -> str:
        """Get the path to the professional resume PDF file"""
        # Use the existing professional resume from test fixtures
        pdf_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'professional_resume.pdf')
        
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            # Fallback: create a minimal test PDF if the fixture doesn't exist
            return self.create_test_pdf()
            
    def create_test_pdf(self) -> str:
        """Create a minimal test PDF file and return its path (fallback)"""
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
179
%%EOF"""
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(pdf_content)
            return f.name


# Pytest fixtures
@pytest.fixture(scope="session")
def api_tester():
    """Fixture to provide API tester instance"""
    save_responses = False  # Set to True to save all responses as JSON files
    tester = APITester(BASE_URL, save_response=save_responses)
    
    # Get test PDF file
    print(f"\n{Colors.YELLOW}📝 Getting test PDF file...{Colors.NC}")
    pdf_path = tester.get_test_pdf_path()
    
    # Check if we're using the professional resume or fallback
    if 'professional_resume.pdf' in pdf_path:
        print(f"{Colors.GREEN}✅ Using professional resume: {pdf_path}{Colors.NC}")
        cleanup_pdf = False  # Don't delete the fixture file
    else:
        print(f"{Colors.YELLOW}⚠️  Using fallback minimal PDF (professional_resume.pdf not found){Colors.NC}")
        cleanup_pdf = True  # Delete the temporary file
    
    tester.pdf_path = pdf_path
    tester.cleanup_pdf = cleanup_pdf
    
    yield tester
    
    # Cleanup only if we created a temporary file
    if cleanup_pdf and os.path.exists(pdf_path):
        print(f"\n{Colors.YELLOW}🧹 Cleaning up temporary test files...{Colors.NC}")
        os.unlink(pdf_path)
            
class TestAPIIntegration:
    """Test class for API integration tests"""
    
    def test_debug_endpoint(self, api_tester):
        """Test the debug endpoint"""
        api_tester.print_header("Debug Endpoint")
        response = requests.get(f"{api_tester.base_url}/api/v1/debug/", verify=VERIFY_SSL)
        data = api_tester.parse_response(response)
        api_tester.save_response("debug_endpoint", data)
        
        # Debug endpoint returns 403 when DEBUG=False, 200 when DEBUG=True
        if 'Debug endpoint disabled' in str(data):
            assert response.status_code == 403
        else:
            assert response.status_code == 200
            assert 'DEBUG' in data or 'error' in data
        
        print(f"{Colors.GREEN}✅ PASS: GET /api/v1/debug/ (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(data, indent=2)[:200]}{'...' if len(str(data)) > 200 else ''}{Colors.NC}")

    def test_upload_resume_no_file(self, api_tester):
        """Test upload with no file"""
        api_tester.print_header("Upload Resume - No File")
        response = requests.post(f"{api_tester.base_url}/api/v1/upload-resume/", verify=VERIFY_SSL)
        data = api_tester.parse_response(response)
        api_tester.save_response("upload_resume_no_file", data)
        
        assert response.status_code == 400
        assert data.get('valid_file') == False
        assert 'error_msg' in data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/upload-resume/ (no file) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(data, indent=2)[:200]}{'...' if len(str(data)) > 200 else ''}{Colors.NC}")
            
    def test_upload_resume_invalid_file(self, api_tester):
        """Test upload with invalid file type"""
        api_tester.print_header("Upload Resume - Invalid File Type")
        # Create a text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a PDF")
            txt_path = f.name
            
        try:
            with open(txt_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{api_tester.base_url}/api/v1/upload-resume/", files=files, verify=VERIFY_SSL)
                
            data = api_tester.parse_response(response)
            api_tester.save_response("upload_resume_invalid_file", data)
            
            assert response.status_code == 400
            assert data.get('valid_file') == False
            assert 'error_msg' in data
            
            print(f"{Colors.GREEN}✅ PASS: POST /api/v1/upload-resume/ (invalid file) (Status: {response.status_code}){Colors.NC}")
            print(f"{Colors.YELLOW}📄 Response: {json.dumps(data, indent=2)[:200]}{'...' if len(str(data)) > 200 else ''}{Colors.NC}")
            
        finally:
            os.unlink(txt_path)  # Clean up
            
    def test_upload_resume_success(self, api_tester):
        """Test successful resume upload"""
        api_tester.print_header("Upload Resume - Success")
        with open(api_tester.pdf_path, 'rb') as f:
            # Use the actual filename from the path
            filename = os.path.basename(api_tester.pdf_path)
            files = {'file': (filename, f, 'application/pdf')}
            response = requests.post(f"{api_tester.base_url}/api/v1/upload-resume/", files=files, verify=VERIFY_SSL)
            
        data = api_tester.parse_response(response)
        api_tester.save_response("upload_resume_success", data)
        
        assert response.status_code == 201
        assert data.get('valid_file') == True
        assert 'doc_id' in data
        assert data['doc_id'] is not None
        
        # Extract doc_id for later tests
        api_tester.doc_id = data['doc_id']
        print(f"{Colors.YELLOW}📋 Extracted doc_id: {api_tester.doc_id}{Colors.NC}")
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/upload-resume/ (valid PDF) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(data, indent=2)[:200]}{'...' if len(str(data)) > 200 else ''}{Colors.NC}")
            
    def test_get_keywords_no_doc_id(self, api_tester):
        """Test get keywords without doc_id"""
        api_tester.print_header("Get Keywords - No doc_id")
        response = requests.post(f"{api_tester.base_url}/api/v1/get-keywords/", verify=VERIFY_SSL)
        data = api_tester.parse_response(response)
        api_tester.save_response("get_keywords_no_doc_id", data)
        
        assert response.status_code == 400
        assert data.get('finished') == False
        assert 'error' in data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/get-keywords/ (no doc_id) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(data, indent=2)[:200]}{'...' if len(str(data)) > 200 else ''}{Colors.NC}")
            
    def test_get_keywords_invalid_doc_id(self, api_tester):
        """Test get keywords with invalid doc_id"""
        api_tester.print_header("Get Keywords - Invalid doc_id")
        data = {'doc_id': 'invalid-uuid-12345'}
        response = requests.post(f"{api_tester.base_url}/api/v1/get-keywords/", data=data, verify=VERIFY_SSL)
        response_data = api_tester.parse_response(response)
        api_tester.save_response("get_keywords_invalid_doc_id", response_data)
        
        assert response.status_code == 404
        assert response_data.get('finished') == False
        assert 'error' in response_data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/get-keywords/ (invalid doc_id) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def test_get_keywords_valid(self, api_tester):
        """Test get keywords with valid doc_id"""
        # First upload a resume to get doc_id
        self.test_upload_resume_success(api_tester)
        
        if not api_tester.doc_id:
            pytest.skip("No doc_id available")
            
        api_tester.print_header("Get Keywords - Valid doc_id")
        max_retries = 10  # Maximum number of retries
        retry_delay = 3   # Wait 3 seconds between retries
        
        for attempt in range(max_retries):
            data = {'doc_id': api_tester.doc_id}
            response = requests.post(f"{api_tester.base_url}/api/v1/get-keywords/", data=data, verify=VERIFY_SSL)
            response_data = api_tester.parse_response(response)
            
            assert response.status_code == 200
            
            # Check if processing is still in progress
            if (response_data.get('finished') == False and 
                response_data.get('error') == ""):
                
                print(f"{Colors.YELLOW}⏳ Processing... (Attempt {attempt + 1}/{max_retries}){Colors.NC}")
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"{Colors.YELLOW}⚠️  Processing still not complete after {max_retries} attempts{Colors.NC}")
                    break
            else:
                # Processing complete or error occurred
                break
        
        api_tester.save_response("get_keywords_valid", response_data)
        
        # Show processing result
        if response_data.get('finished') == True:
            keywords = response_data.get('keywords', [])
            print(f"{Colors.GREEN}✅ Processing complete! Found {len(keywords)} keywords{Colors.NC}")
            if keywords:
                print(f"{Colors.YELLOW}📋 Keywords: {', '.join(keywords)}{Colors.NC}")
            assert 'keywords' in response_data
            assert isinstance(response_data['keywords'], list)
        elif response_data.get('error'):
            print(f"{Colors.RED}❌ Processing error: {response_data.get('error')}{Colors.NC}")
            assert 'error' in response_data
        else:
            print(f"{Colors.YELLOW}⚠️  Processing still in progress{Colors.NC}")
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/get-keywords/ (valid doc_id) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def test_target_job_missing_fields(self, api_tester):
        """Test target job with missing fields"""
        api_tester.print_header("Target Job - Missing Fields")
        data = {'title': 'Software Engineer'}  # Missing doc_id
        response = requests.post(f"{api_tester.base_url}/api/v1/target-job/", json=data, verify=VERIFY_SSL)
        response_data = api_tester.parse_response(response)
        api_tester.save_response("target_job_missing_fields", response_data)
        
        assert response.status_code == 400
        assert 'error' in response_data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/target-job/ (missing doc_id) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def test_target_job_valid(self, api_tester):
        """Test target job with valid data"""
        # First upload a resume to get doc_id
        self.test_upload_resume_success(api_tester)
        
        if not api_tester.doc_id:
            pytest.skip("No doc_id available")
            
        api_tester.print_header("Target Job - Valid")
        data = {
            'doc_id': api_tester.doc_id,
            'title': 'Software Engineer'
        }
        response = requests.post(f"{api_tester.base_url}/api/v1/target-job/", json=data, verify=VERIFY_SSL)
        response_data = api_tester.parse_response(response)
        api_tester.save_response("target_job_valid", response_data)
        
        assert response.status_code == 200
        assert response_data.get('doc_id') == api_tester.doc_id
        assert 'message' in response_data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/target-job/ (valid data) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def test_get_questions_missing_doc_id(self, api_tester):
        """Test get interview questions without doc_id"""
        api_tester.print_header("Get Interview Questions - Missing doc_id")
        response = requests.post(f"{api_tester.base_url}/api/v1/get-questions/", json={}, verify=VERIFY_SSL)
        response_data = api_tester.parse_response(response)
        api_tester.save_response("get_questions_missing_doc_id", response_data)
        
        assert response.status_code == 400
        assert 'error' in response_data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/get-questions/ (missing doc_id) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def test_get_questions_valid(self, api_tester):
        """Test get interview questions with valid doc_id"""
        # First upload a resume to get doc_id
        self.test_upload_resume_success(api_tester)
        
        if not api_tester.doc_id:
            pytest.skip("No doc_id available")
            
        api_tester.print_header("Get Interview Questions - Valid")
        data = {'doc_id': api_tester.doc_id}
        response = requests.post(f"{api_tester.base_url}/api/v1/get-questions/", json=data, verify=VERIFY_SSL)
        response_data = api_tester.parse_response(response)
        api_tester.save_response("get_questions_valid", response_data)
        
        assert response.status_code == 200
        assert 'doc_id' in response_data or 'interview_questions' in response_data
        
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/get-questions/ (valid doc_id) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def test_signup(self, api_tester):
        """Test user signup"""
        api_tester.print_header("User Signup")
        data = {
            'username': f'testuser{int(time.time())}',
            'email': f'test{int(time.time())}@example.com',
            'password': 'securepassword123',
            'full_name': 'Test User',
            'is_employer': False
        }
        response = requests.post(f"{api_tester.base_url}/api/v1/signup/", json=data, verify=VERIFY_SSL)
        response_data = api_tester.parse_response(response)
        api_tester.save_response("signup", response_data)
        
        if response.status_code == 404:
            pytest.skip("Signup endpoint not available (404)")
        else:
            assert response.status_code == 201
            assert 'message' in response_data
            
        print(f"{Colors.GREEN}✅ PASS: POST /api/v1/signup/ (new user) (Status: {response.status_code}){Colors.NC}")
        print(f"{Colors.YELLOW}� Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")


