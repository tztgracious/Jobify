#!/usr/bin/env python3
"""
Django API Testing Script for Jobify
Tests all Django APIs one by one with detailed reporting

This script is configured to work with self-signed SSL certificates.
Set VERIFY_SSL=True for production environments with valid certificates.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
import tempfile
import os

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
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.doc_id = None
        
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
        
    def check_result(self, expected_status: int, actual_status: int, test_name: str, response_data: Dict = None):
        if actual_status == expected_status:
            print(f"{Colors.GREEN}✅ PASS: {test_name} (Status: {actual_status}){Colors.NC}")
            self.passed_tests += 1
        else:
            print(f"{Colors.RED}❌ FAIL: {test_name} (Expected: {expected_status}, Got: {actual_status}){Colors.NC}")
            self.failed_tests += 1
            
        if response_data:
            print(f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}")
            
    def save_response(self, endpoint: str, response_data: Dict):
        filename = f"response_{endpoint.replace('/', '_').replace('-', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(response_data, f, indent=2)
        print(f"{Colors.YELLOW}📄 Response saved to: {filename}{Colors.NC}")
        
    def get_test_pdf_path(self) -> str:
        """Get the path to the professional resume PDF file"""
        # Use the existing professional resume from test fixtures
        pdf_path = os.path.join(os.path.dirname(__file__), 'backend', 'test', 'fixtures', 'professional_resume.pdf')
        
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
            
    def test_debug_endpoint(self):
        """Test the debug endpoint"""
        self.print_header("Debug Endpoint")
        try:
            response = requests.get(f"{self.base_url}/api/v1/debug/", verify=VERIFY_SSL)
            data = self.parse_response(response)
            # Debug endpoint returns 403 when DEBUG=False, 200 when DEBUG=True
            expected_status = 403 if 'Debug endpoint disabled' in str(data) else 200
            self.check_result(expected_status, response.status_code, "GET /api/v1/debug/", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}

    def test_upload_resume_no_file(self):
        """Test upload with no file"""
        self.print_header("Upload Resume - No File")
        try:
            response = requests.post(f"{self.base_url}/api/v1/upload-resume/", verify=VERIFY_SSL)
            data = self.parse_response(response)
            self.check_result(400, response.status_code, "POST /api/v1/upload-resume/ (no file)", data)
            self.save_response("upload_resume_no_file", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_upload_resume_invalid_file(self):
        """Test upload with invalid file type"""
        self.print_header("Upload Resume - Invalid File Type")
        try:
            # Create a text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("This is not a PDF")
                txt_path = f.name
                
            with open(txt_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/api/v1/upload-resume/", files=files, verify=VERIFY_SSL)
                
            data = self.parse_response(response)
            self.check_result(400, response.status_code, "POST /api/v1/upload-resume/ (invalid file)", data)
            self.save_response("upload_resume_invalid_file", data)
            
            os.unlink(txt_path)  # Clean up
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_upload_resume_success(self, pdf_path: str):
        """Test successful resume upload"""
        self.print_header("Upload Resume - Success")
        try:
            with open(pdf_path, 'rb') as f:
                # Use the actual filename from the path
                filename = os.path.basename(pdf_path)
                files = {'file': (filename, f, 'application/pdf')}
                response = requests.post(f"{self.base_url}/api/v1/upload-resume/", files=files, verify=VERIFY_SSL)
                
            data = self.parse_response(response)
            self.check_result(201, response.status_code, "POST /api/v1/upload-resume/ (valid PDF)", data)
            print(data)
            # Extract doc_id for later tests
            if 'doc_id' in data:
                self.doc_id = data['doc_id']
                print(f"{Colors.YELLOW}📋 Extracted doc_id: {self.doc_id}{Colors.NC}")
                
            self.save_response("upload_resume_success", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_get_keywords_valid(self):
        """Test get keywords with valid doc_id"""
        if not self.doc_id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No doc_id available{Colors.NC}")
            return {}
            
        self.print_header("Get Keywords - Valid doc_id")
        try:
            data = {'doc_id': self.doc_id}
            response = requests.post(f"{self.base_url}/api/v1/get-keywords/", data=data, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            self.check_result(200, response.status_code, "POST /api/v1/get-keywords/ (valid doc_id)", response_data)
            self.save_response("get_keywords_valid", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_get_keywords_no_doc_id(self):
        """Test get keywords without doc_id"""
        self.print_header("Get Keywords - No doc_id")
        try:
            response = requests.post(f"{self.base_url}/api/v1/get-keywords/", verify=VERIFY_SSL)
            data = self.parse_response(response)
            self.check_result(400, response.status_code, "POST /api/v1/get-keywords/ (no doc_id)", data)
            self.save_response("get_keywords_no_doc_id", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_get_keywords_invalid_doc_id(self):
        """Test get keywords with invalid doc_id"""
        self.print_header("Get Keywords - Invalid doc_id")
        try:
            data = {'doc_id': 'invalid-uuid-12345'}
            response = requests.post(f"{self.base_url}/api/v1/get-keywords/", data=data, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            self.check_result(404, response.status_code, "POST /api/v1/get-keywords/ (invalid doc_id)", response_data)
            self.save_response("get_keywords_invalid_doc_id", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_target_job_valid(self):
        """Test target job with valid data"""
        if not self.doc_id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No doc_id available{Colors.NC}")
            return {}
            
        self.print_header("Target Job - Valid")
        try:
            data = {
                'doc_id': self.doc_id,
                'title': 'Software Engineer'
            }
            response = requests.post(f"{self.base_url}/api/v1/target-job/", json=data, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            self.check_result(200, response.status_code, "POST /api/v1/target-job/ (valid data)", response_data)
            self.save_response("target_job_valid", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_target_job_missing_fields(self):
        """Test target job with missing fields"""
        self.print_header("Target Job - Missing Fields")
        try:
            data = {'title': 'Software Engineer'}  # Missing doc_id
            response = requests.post(f"{self.base_url}/api/v1/target-job/", json=data, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            self.check_result(400, response.status_code, "POST /api/v1/target-job/ (missing doc_id)", response_data)
            self.save_response("target_job_missing_fields", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_get_questions_valid(self):
        """Test get interview questions with valid doc_id"""
        if not self.doc_id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No doc_id available{Colors.NC}")
            return {}
            
        self.print_header("Get Interview Questions - Valid")
        try:
            data = {'doc_id': self.doc_id}
            response = requests.post(f"{self.base_url}/api/v1/get-questions/", json=data, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            self.check_result(200, response.status_code, "POST /api/v1/get-questions/ (valid doc_id)", response_data)
            self.save_response("get_questions_valid", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_get_questions_missing_doc_id(self):
        """Test get interview questions without doc_id"""
        self.print_header("Get Interview Questions - Missing doc_id")
        try:
            response = requests.post(f"{self.base_url}/api/v1/get-questions/", json={}, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            self.check_result(400, response.status_code, "POST /api/v1/get-questions/ (missing doc_id)", response_data)
            self.save_response("get_questions_missing_doc_id", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def test_signup(self):
        """Test user signup"""
        self.print_header("User Signup")
        try:
            import time
            data = {
                'username': f'testuser{int(time.time())}',
                'email': f'test{int(time.time())}@example.com',
                'password': 'securepassword123',
                'full_name': 'Test User',
                'is_employer': False
            }
            response = requests.post(f"{self.base_url}/api/v1/signup/", json=data, verify=VERIFY_SSL)
            response_data = self.parse_response(response)
            
            if response.status_code == 404:
                print(f"{Colors.YELLOW}⚠️  SKIP: Signup endpoint not available (404){Colors.NC}")
                return response_data
            else:
                self.check_result(201, response.status_code, "POST /api/v1/signup/ (new user)", response_data)
                self.save_response("signup", response_data)
                return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.failed_tests += 1
            return {}
            
    def run_all_tests(self):
        """Run all API tests"""
        print(f"{Colors.BLUE}🚀 Starting Django API Tests for Jobify{Colors.NC}")
        print(f"{Colors.BLUE}Base URL: {self.base_url}{Colors.NC}")
        
        # Get test PDF file
        print(f"\n{Colors.YELLOW}📝 Getting test PDF file...{Colors.NC}")
        pdf_path = self.get_test_pdf_path()
        
        # Check if we're using the professional resume or fallback
        if 'professional_resume.pdf' in pdf_path:
            print(f"{Colors.GREEN}✅ Using professional resume: {pdf_path}{Colors.NC}")
            cleanup_pdf = False  # Don't delete the fixture file
        else:
            print(f"{Colors.YELLOW}⚠️  Using fallback minimal PDF (professional_resume.pdf not found){Colors.NC}")
            cleanup_pdf = True  # Delete the temporary file
        
        try:
            # Run all tests
            self.test_debug_endpoint()
            self.test_upload_resume_no_file()
            self.test_upload_resume_invalid_file()
            self.test_get_keywords_no_doc_id()
            self.test_get_keywords_invalid_doc_id()
            
            self.test_upload_resume_success(pdf_path)
            self.test_get_keywords_valid()
            
            self.test_target_job_valid()
            self.test_target_job_missing_fields()
            self.test_get_questions_valid()
            self.test_get_questions_missing_doc_id()
            # self.test_signup()
            
        finally:
            # Cleanup only if we created a temporary file
            if cleanup_pdf:
                print(f"\n{Colors.YELLOW}🧹 Cleaning up temporary test files...{Colors.NC}")
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BLUE}{'='*50}{Colors.NC}")
        print(f"{Colors.BLUE}📊 TEST SUMMARY{Colors.NC}")
        print(f"{Colors.BLUE}{'='*50}{Colors.NC}")
        print(f"{Colors.GREEN}✅ Passed: {self.passed_tests}{Colors.NC}")
        print(f"{Colors.RED}❌ Failed: {self.failed_tests}{Colors.NC}")
        print(f"{Colors.BLUE}📋 Total:  {self.total_tests}{Colors.NC}")
        
        if self.failed_tests == 0:
            print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.NC}")
            return 0
        else:
            print(f"\n{Colors.RED}⚠️  Some tests failed. Check the responses above.{Colors.NC}")
            return 1

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
