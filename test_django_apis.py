#!/usr/bin/env python3
"""
Django API Testing Script for Jobify
Tests all Django APIs one by one with detailed reporting

This script is configured to work with self-signed SSL certificates.
Set VERIFY_SSL=True for production environments with valid certificates.
"""

import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, Optional

import requests

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
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


class APITester:
    def __init__(self, base_url: str, save_response: bool = False):
        self.base_url = base_url
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.id = None
        self.save_response_flag = save_response
        self.interview_questions = []  # Store questions for interview tests
        self.tech_questions = []  # Store technical questions for interview tests
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
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                return response.json()
            elif response.text.strip().startswith("{"):
                # Sometimes JSON is returned without proper content-type
                return response.json()
            else:
                # Handle HTML error pages or other non-JSON responses
                return {
                    "error": f"Non-JSON response (Status: {response.status_code})",
                    "content_type": content_type,
                    "response_text": (
                        response.text[:200] + "..."
                        if len(response.text) > 200
                        else response.text
                    ),
                }
        except json.JSONDecodeError:
            # Handle malformed JSON
            return {
                "error": f"Invalid JSON response (Status: {response.status_code})",
                "content_type": response.headers.get("content-type", ""),
                "response_text": (
                    response.text[:200] + "..."
                    if len(response.text) > 200
                    else response.text
                ),
            }
        except Exception as e:
            return {
                "error": f"Response parsing error: {str(e)}",
                "status_code": response.status_code,
            }

    def check_result(
        self,
        expected_status: int,
        actual_status: int,
        test_name: str,
        response_data: Dict = None,
    ):
        if actual_status == expected_status:
            print(
                f"{Colors.GREEN}✅ PASS: {test_name} (Status: {actual_status}){Colors.NC}"
            )
            self.passed_tests += 1
        else:
            print(
                f"{Colors.RED}❌ FAIL: {test_name} (Expected: {expected_status}, Got: {actual_status}){Colors.NC}"
            )
            self.failed_tests += 1
            self.failed_test_names.append(test_name)

        if response_data:
            print(
                f"{Colors.YELLOW}📄 Response: {json.dumps(response_data, indent=2)[:200]}{'...' if len(str(response_data)) > 200 else ''}{Colors.NC}"
            )

    def mark_test_failed(self, test_name: str):
        """Mark a test as failed due to exception"""
        self.failed_tests += 1
        self.failed_test_names.append(f"{test_name} (Exception)")

    def save_response(self, endpoint: str, response_data: Dict):
        if not self.save_response_flag:
            return

        filename = f"response_{endpoint.replace('/', '_').replace('-', '_')}.json"
        with open(filename, "w") as f:
            json.dump(response_data, f, indent=2)
        print(f"{Colors.YELLOW}📄 Response saved to: {filename}{Colors.NC}")

    def get_test_pdf_path(self) -> str:
        """Get the path to the professional resume PDF file"""
        # Use the existing professional resume from test fixtures
        pdf_path = os.path.join(
            os.path.dirname(__file__),
            "backend",
            "test",
            "fixtures",
            "professional_resume.pdf",
        )

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

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
            f.write(pdf_content)
            return f.name

    def test_debug_endpoint(self):
        """Test the debug endpoint"""
        self.print_header("Debug Endpoint")
        try:
            response = requests.get(f"{self.base_url}/api/v1/debug/", verify=VERIFY_SSL)
            data = self.parse_response(response)
            # Debug endpoint returns 403 when DEBUG=False, 200 when DEBUG=True
            expected_status = 403 if "Debug endpoint disabled" in str(data) else 200
            self.check_result(
                expected_status, response.status_code, "GET /api/v1/debug/", data
            )
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("GET /api/v1/debug/")
            return {}

    def test_upload_resume_no_file(self):
        """Test upload with no file"""
        self.print_header("Upload Resume - No File")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/upload-resume/", verify=VERIFY_SSL
            )
            data = self.parse_response(response)
            self.check_result(
                400, response.status_code, "POST /api/v1/upload-resume/ (no file)", data
            )
            self.save_response("upload_resume_no_file", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/upload-resume/ (no file)")
            return {}

    def test_upload_resume_invalid_file(self):
        """Test upload with invalid file type"""
        self.print_header("Upload Resume - Invalid File Type")
        try:
            # Create a text file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write("This is not a PDF")
                txt_path = f.name

            with open(txt_path, "rb") as f:
                files = {"file": ("test.txt", f, "text/plain")}
                response = requests.post(
                    f"{self.base_url}/api/v1/upload-resume/",
                    files=files,
                    verify=VERIFY_SSL,
                )

            data = self.parse_response(response)
            self.check_result(
                400,
                response.status_code,
                "POST /api/v1/upload-resume/ (invalid file)",
                data,
            )
            self.save_response("upload_resume_invalid_file", data)

            os.unlink(txt_path)  # Clean up
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/upload-resume/ (invalid file)")
            return {}

    def test_upload_resume_success(self, pdf_path: str):
        """Test successful resume upload"""
        self.print_header("Upload Resume - Success")
        try:
            with open(pdf_path, "rb") as f:
                # Use the actual filename from the path
                filename = os.path.basename(pdf_path)
                files = {"file": (filename, f, "application/pdf")}
                response = requests.post(
                    f"{self.base_url}/api/v1/upload-resume/",
                    files=files,
                    verify=VERIFY_SSL,
                )

            data = self.parse_response(response)
            self.check_result(
                201,
                response.status_code,
                "POST /api/v1/upload-resume/ (valid PDF)",
                data,
            )
            # Extract id for later tests
            if "id" in data:
                self.id = data["id"]
                print(f"{Colors.YELLOW}📋 Extracted id: {self.id}{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ ERROR: No id in response{Colors.NC}")
                self.mark_test_failed(
                    "POST /api/v1/upload-resume/ (valid PDF) - no id"
                )
            self.save_response("upload_resume_success", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/upload-resume/ (valid PDF)")
            return {}

    def test_get_keywords_valid(self):
        """Test get keywords with valid id"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Get Keywords - Valid id")
        try:
            import time

            max_retries = 10  # Maximum number of retries
            retry_delay = 3  # Wait 3 seconds between retries

            for attempt in range(max_retries):
                data = {"id": self.id}
                response = requests.post(
                    f"{self.base_url}/api/v1/get-keywords/",
                    data=data,
                    verify=VERIFY_SSL,
                )
                response_data = self.parse_response(response)

                # Check if processing is still in progress
                if (
                    response.status_code == 200
                    and response_data.get("finished") == False
                    and response_data.get("error") == ""
                ):

                    print(
                        f"{Colors.YELLOW}⏳ Processing... (Attempt {attempt + 1}/{max_retries}){Colors.NC}"
                    )
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(
                            f"{Colors.YELLOW}⚠️  Processing still not complete after {max_retries} attempts{Colors.NC}"
                        )
                        break
                else:
                    # Processing complete or error occurred
                    break

            self.check_result(
                200,
                response.status_code,
                "POST /api/v1/get-keywords/ (valid id)",
                response_data,
            )

            # Show processing result
            if response_data.get("finished") == True:
                keywords = response_data.get("keywords", [])
                print(
                    f"{Colors.GREEN}✅ Processing complete! Found {len(keywords)} keywords{Colors.NC}"
                )
                if keywords:
                    print(
                        f"{Colors.YELLOW}📋 Keywords: {', '.join(keywords)}{Colors.NC}"
                    )
            elif response_data.get("error"):
                print(
                    f"{Colors.RED}❌ Processing error: {response_data.get('error')}{Colors.NC}"
                )
            else:
                print(f"{Colors.YELLOW}⚠️  Processing still in progress{Colors.NC}")

            self.save_response("get_keywords_valid", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/get-keywords/ (valid id)")
            return {}

    def test_get_keywords_no_id(self):
        """Test get keywords without id"""
        self.print_header("Get Keywords - No id")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/get-keywords/", verify=VERIFY_SSL
            )
            data = self.parse_response(response)
            self.check_result(
                400,
                response.status_code,
                "POST /api/v1/get-keywords/ (no id)",
                data,
            )
            self.save_response("get_keywords_no_id", data)
            return data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/get-keywords/ (no id)")
            return {}

    def test_get_keywords_invalid_id(self):
        """Test get keywords with invalid id"""
        self.print_header("Get Keywords - Invalid id")
        try:
            data = {"id": "invalid-uuid-12345"}
            response = requests.post(
                f"{self.base_url}/api/v1/get-keywords/", data=data, verify=VERIFY_SSL
            )
            response_data = self.parse_response(response)
            self.check_result(
                404,
                response.status_code,
                "POST /api/v1/get-keywords/ (invalid id)",
                response_data,
            )
            self.save_response("get_keywords_invalid_id", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/get-keywords/ (invalid id)")
            return {}

    def test_get_grammar_valid(self):
        """Test get grammar results with valid id"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Get Grammar Results - Valid id")
        try:
            import time

            max_retries = 10  # Maximum number of retries
            retry_delay = 3  # Wait 3 seconds between retries

            for attempt in range(max_retries):
                data = {"id": self.id}
                response = requests.post(
                    f"{self.base_url}/api/v1/get-grammar-results/",
                    json=data,
                    verify=VERIFY_SSL,
                )
                response_data = self.parse_response(response)

                # Check if processing is still in progress
                if (
                    response.status_code == 200
                    and response_data.get("finished") == False
                    and response_data.get("error") == ""
                ):

                    print(
                        f"{Colors.YELLOW}⏳ Grammar analysis processing... (Attempt {attempt + 1}/{max_retries}){Colors.NC}"
                    )
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(
                            f"{Colors.YELLOW}⚠️  Grammar analysis still not complete after {max_retries} attempts{Colors.NC}"
                        )
                        break
                else:
                    # Processing complete or error occurred
                    break

            self.check_result(
                200,
                response.status_code,
                "POST /api/v1/get-grammar-results/ (valid id)",
                response_data,
            )

            # Show processing result
            if response_data.get("finished") == True:
                grammar_check = response_data.get("grammar_check", {})
                if grammar_check and "matches" in grammar_check:
                    matches = grammar_check.get("matches", [])
                    language = grammar_check.get("language", "unknown")
                    print(
                        f"{Colors.GREEN}✅ Grammar analysis complete! Found {len(matches)} issues{Colors.NC}"
                    )
                    print(f"{Colors.YELLOW}🔤 Language: {language}{Colors.NC}")

                    # Show first few grammar issues as preview
                    for i, match in enumerate(matches[:3]):  # Show first 3 matches
                        message = match.get(
                            "shortMessage", match.get("message", "No message")
                        )
                        context = match.get("context", {}).get("text", "No context")
                        print(f"{Colors.YELLOW}  📌 Issue {i+1}: {message}{Colors.NC}")
                        if context != "No context":
                            context_preview = (
                                context[:50] + "..." if len(context) > 50 else context
                            )
                            print(
                                f"{Colors.YELLOW}      Context: {context_preview}{Colors.NC}"
                            )

                    if len(matches) > 3:
                        print(
                            f"{Colors.YELLOW}  ... and {len(matches) - 3} more issues{Colors.NC}"
                        )

                elif grammar_check:
                    print(
                        f"{Colors.GREEN}✅ Grammar analysis complete! No issues found{Colors.NC}"
                    )
                else:
                    print(
                        f"{Colors.GREEN}✅ Grammar analysis complete! No grammar data available{Colors.NC}"
                    )

            elif response_data.get("error"):
                print(
                    f"{Colors.RED}❌ Grammar analysis error: {response_data.get('error')}{Colors.NC}"
                )
            else:
                print(
                    f"{Colors.YELLOW}⚠️  Grammar analysis still in progress{Colors.NC}"
                )

            # Always save the response to grammar_result.json
            # with open("grammar_result.json", "w") as f:
            #     json.dump(response_data, f, indent=2)
            print(
                f"{Colors.BLUE}💾 Grammar results saved to: grammar_result.json{Colors.NC}"
            )

            self.save_response("get_grammar_valid", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/get-grammar-results/ (valid id)")
            return {}

    def test_target_job_valid(self):
        """Test target job with valid data"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Target Job - Valid")
        try:
            data = {"id": self.id, "title": "Software Engineer", "answer_type": "text"}
            response = requests.post(
                f"{self.base_url}/api/v1/target-job/", json=data, verify=VERIFY_SSL
            )
            response_data = self.parse_response(response)
            self.check_result(
                200,
                response.status_code,
                "POST /api/v1/target-job/ (valid data)",
                response_data,
            )
            self.save_response("target_job_valid", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/target-job/ (valid data)")
            return {}

    def test_target_job_missing_fields(self):
        """Test target job with missing fields"""
        self.print_header("Target Job - Missing Fields")
        try:
            data = {"title": "Software Engineer"}  # Missing id
            response = requests.post(
                f"{self.base_url}/api/v1/target-job/", json=data, verify=VERIFY_SSL
            )
            response_data = self.parse_response(response)
            self.check_result(
                400,
                response.status_code,
                "POST /api/v1/target-job/ (missing id)",
                response_data,
            )
            self.save_response("target_job_missing_fields", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/target-job/ (missing id)")
            return {}

    def test_get_questions_valid(self):
        """Test get interview questions with valid id"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Get Interview Questions - Valid")
        try:
            import time

            max_retries = 10  # Maximum number of retries
            retry_delay = 3  # Wait 3 seconds between retries

            for attempt in range(max_retries):
                data = {"id": self.id}
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/get-all-questions/", json=data, verify=VERIFY_SSL
                )
                end = time.time()
                print(
                    f"{Colors.YELLOW}⏱️  Response time: {end - start:.2f} seconds (Attempt {attempt + 1}/{max_retries}){Colors.NC}"
                )
                response_data = self.parse_response(response)
                finished = response_data.get("finished", False)
                # Check if questions generation is still in progress (status 200)
                if not finished:
                    print(
                        f"{Colors.YELLOW}⏳ Questions generation in progress... (Status: 200, Attempt {attempt + 1}/{max_retries}){Colors.NC}"
                    )
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(
                            f"{Colors.YELLOW}⚠️  Questions generation still not complete after {max_retries} attempts{Colors.NC}"
                        )
                        break
                else:
                    # Questions generation complete
                    print(
                        f"{Colors.GREEN}✅ Questions generation complete! (Status: 201){Colors.NC}"
                    )
                    break

            self.check_result(
                200,
                response.status_code,
                "POST /api/v1/get-all-questions/ (valid id)",
                response_data,
            )
            self.save_response("get_questions_valid", response_data)
            self.interview_questions = response_data.get("interview_questions", [])
            self.tech_questions = response_data.get("tech_questions", [])
            if not self.interview_questions:
                print(
                    f"{Colors.YELLOW}⚠️  No questions returned for id: {self.id}{Colors.NC}"
                )
            else:
                print(
                    f"{Colors.GREEN}✅ Retrieved {len(self.interview_questions)} interview questions{Colors.NC}"
                )
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/get-all-questions/ (valid id)")
            return {}

    def test_get_questions_missing_id(self):
        """Test get interview questions without id"""
        self.print_header("Get Interview Questions - Missing id")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/get-questions/", json={}, verify=VERIFY_SSL
            )
            response_data = self.parse_response(response)
            self.check_result(
                400,
                response.status_code,
                "POST /api/v1/get-questions/ (missing id)",
                response_data,
            )
            self.save_response("get_questions_missing_id", response_data)
            return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/get-questions/ (missing id)")
            return {}

    def test_submit_tech_question_valid(self):
        """Test submitting technical question answers"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Submit Technical Question Answers - Valid")
        try:
            # Hardcoded sample answers for testing
            sample_answers = [
                {
                    "id": self.id,
                    "question": self.tech_questions[0],
                    "answer": "I have built several REST APIs using Django and Flask, focusing on best practices like versioning, authentication, and error handling.",
                    "index": 0,
                },
            ]
            successful_submissions = 0
            for i, answer_data in enumerate(sample_answers):
                print(f"{Colors.YELLOW}📝 Submitting answer {i + 1}/1...{Colors.NC}")

                data = sample_answers[i]

                response = requests.post(
                    f"{self.base_url}/api/v1/submit-tech-answer/",
                    json=data,
                    verify=VERIFY_SSL,
                )
                response_data = self.parse_response(response)

                if response.status_code == 200:
                    successful_submissions += 1
                    print(
                        f"{Colors.GREEN}✅ Answer {i + 1} submitted successfully{Colors.NC}"
                    )

                    # Show progress if available
                    if "progress" in response_data:
                        progress = response_data["progress"]
                        print(f"{Colors.YELLOW}📊 Progress: {progress}{Colors.NC}")
                else:
                    print(
                        f"{Colors.RED}❌ Failed to submit answer {i + 1}: Status {response.status_code}{Colors.NC}"
                    )
                    print(
                        f"{Colors.RED}   Error: {response_data.get('error', 'Unknown error')}{Colors.NC}"
                    )
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/submit-tech-question/")
            return {}

    def test_submit_interview_answer(self):
        """Test submitting answers to interview questions"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Submit Interview Answers - Valid")
        try:
            # Hardcoded sample answers for testing
            sample_answers = [
                {
                    "id": self.id,
                    "question": self.interview_questions[0],
                    "answer": "I worked on a web application that processed user resumes and provided interview preparation. This involved building REST APIs, implementing file upload functionality, and integrating with external AI services. The main challenge was handling concurrent file processing and ensuring data consistency.",
                    "index": 0,
                    "answer_type": "text",
                },
                {
                    "id": self.id,
                    "question": self.interview_questions[1],
                    "answer": "I follow a comprehensive approach including writing unit tests, conducting code reviews, using static analysis tools, implementing CI/CD pipelines, and following coding standards. I also practice test-driven development and ensure proper error handling and logging.",
                    "index": 1,
                    "answer_type": "text",
                },
                {
                    "id": self.id,
                    "question": self.interview_questions[2],
                    "answer": "I start by reproducing the issue consistently, then analyze logs and error messages. I use debugging tools to step through the code, isolate the problem area, and test potential solutions. I also document the issue and solution for future reference.",
                    "index": 2,
                    "answer_type": "text",
                },
            ]

            successful_submissions = 0

            for i, answer_data in enumerate(sample_answers):
                print(f"{Colors.YELLOW}📝 Submitting answer {i + 1}/3...{Colors.NC}")

                data = sample_answers[i]

                response = requests.post(
                    f"{self.base_url}/api/v1/submit-interview-answer/",
                    json=data,
                    verify=VERIFY_SSL,
                )
                response_data = self.parse_response(response)

                if response.status_code == 200:
                    successful_submissions += 1
                    print(
                        f"{Colors.GREEN}✅ Answer {i + 1} submitted successfully{Colors.NC}"
                    )

                    # Show progress if available
                    if "progress" in response_data:
                        progress = response_data["progress"]
                        print(f"{Colors.YELLOW}📊 Progress: {progress}{Colors.NC}")
                else:
                    print(
                        f"{Colors.RED}❌ Failed to submit answer {i + 1}: Status {response.status_code}{Colors.NC}"
                    )
                    print(
                        f"{Colors.RED}   Error: {response_data.get('error', 'Unknown error')}{Colors.NC}"
                    )

            # Overall result
            if successful_submissions == len(sample_answers):
                self.check_result(
                    200,
                    200,
                    f"POST /api/v1/submit-answer/ ({successful_submissions}/{len(sample_answers)} answers)",
                    {"success": True},
                )
                print(
                    f"{Colors.GREEN}✅ All {successful_submissions} answers submitted successfully{Colors.NC}"
                )
            else:
                self.mark_test_failed(
                    f"POST /api/v1/submit-answer/ ({successful_submissions}/{len(sample_answers)} answers)"
                )
                print(
                    f"{Colors.RED}❌ Only {successful_submissions}/{len(sample_answers)} answers submitted successfully{Colors.NC}"
                )

            self.save_response(
                "submit_answers",
                {"submitted": successful_submissions, "total": len(sample_answers)},
            )
            return {"submitted": successful_submissions, "total": len(sample_answers)}

        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/submit-answer/")
            return {}

    def test_get_feedback(self):
        """Test getting feedback on submitted answers"""
        if not self.id:
            print(f"{Colors.YELLOW}⚠️  SKIP: No id available{Colors.NC}")
            return {}

        self.print_header("Get Feedback - Valid")
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/feedback/",
                json={"id": self.id, "answer_type": "text"},
                verify=VERIFY_SSL,
            )
            end = time.time()
            print(
                f"{Colors.YELLOW}⏱️  Response time: {end - start:.2f} seconds{Colors.NC}"
            )

            response_data = self.parse_response(response)
            self.check_result(
                200,
                response.status_code,
                "POST /api/v1/feedback/ (valid id)",
                response_data,
            )

            # Display feedback information
            if response.status_code == 200 and "feedbacks" in response_data:
                feedbacks = response_data["feedbacks"]

                # Count individual question feedback
                question_feedback_count = len(
                    [k for k in feedbacks.keys() if "feedback" in k and k != "summary"]
                )
                print(
                    f"{Colors.GREEN}✅ Received feedback for {question_feedback_count} questions{Colors.NC}"
                )

                # Show summary if available
                if "summary" in feedbacks:
                    summary = feedbacks["summary"]
                    preview = summary[:150] + "..." if len(summary) > 150 else summary
                    print(f"{Colors.YELLOW}📝 Summary preview: {preview}{Colors.NC}")

                # Show first question feedback as example
                for key, feedback in feedbacks.items():
                    if "question_" in key and "feedback" in key:
                        preview = (
                            feedback[:100] + "..." if len(feedback) > 100 else feedback
                        )
                        print(
                            f"{Colors.YELLOW}💬 Sample feedback: {preview}{Colors.NC}"
                        )
                        break

            elif response.status_code == 200:
                print(
                    f"{Colors.YELLOW}⚠️  Feedback retrieved but format unexpected{Colors.NC}"
                )
            else:
                print(f"{Colors.RED}❌ Failed to retrieve feedback{Colors.NC}")

            self.save_response("get_feedback", response_data)
            return response_data

        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("GET /api/v1/feedback/")
            return {}

    def test_signup(self):
        """Test user signup"""
        self.print_header("User Signup")
        try:
            import time

            data = {
                "username": f"testuser{int(time.time())}",
                "email": f"test{int(time.time())}@example.com",
                "password": "securepassword123",
                "full_name": "Test User",
                "is_employer": False,
            }
            response = requests.post(
                f"{self.base_url}/api/v1/signup/", json=data, verify=VERIFY_SSL
            )
            response_data = self.parse_response(response)

            if response.status_code == 404:
                print(
                    f"{Colors.YELLOW}⚠️  SKIP: Signup endpoint not available (404){Colors.NC}"
                )
                return response_data
            else:
                self.check_result(
                    201,
                    response.status_code,
                    "POST /api/v1/signup/ (new user)",
                    response_data,
                )
                self.save_response("signup", response_data)
                return response_data
        except Exception as e:
            print(f"{Colors.RED}❌ ERROR: {e}{Colors.NC}")
            self.mark_test_failed("POST /api/v1/signup/ (new user)")
            return {}

    def run_all_tests(self):
        """Run all API tests"""
        print(f"{Colors.BLUE}🚀 Starting Django API Tests for Jobify{Colors.NC}")
        print(f"{Colors.BLUE}Base URL: {self.base_url}{Colors.NC}")

        # Get test PDF file
        print(f"\n{Colors.YELLOW}📝 Getting test PDF file...{Colors.NC}")
        pdf_path = self.get_test_pdf_path()

        # Check if we're using the professional resume or fallback
        if "professional_resume.pdf" in pdf_path:
            print(f"{Colors.GREEN}✅ Using professional resume: {pdf_path}{Colors.NC}")
            cleanup_pdf = False  # Don't delete the fixture file
        else:
            print(
                f"{Colors.YELLOW}⚠️  Using fallback minimal PDF (professional_resume.pdf not found){Colors.NC}"
            )
            cleanup_pdf = True  # Delete the temporary file

        try:
            # Run all tests
            self.test_debug_endpoint()
            # self.test_upload_resume_no_file()
            # self.test_upload_resume_invalid_file()
            # self.test_get_keywords_no_id()
            # self.test_get_keywords_invalid_id()

            self.test_upload_resume_success(pdf_path)
            self.test_get_keywords_valid()
            self.test_get_grammar_valid()
            # self.test_target_job_missing_fields()
            # self.test_get_questions_missing_id()
            self.test_target_job_valid()
            # Interview workflow tests
            self.test_get_questions_valid()
            self.test_submit_tech_question_valid()
            self.test_submit_interview_answer()
            self.test_get_feedback()

            # self.test_signup()

        finally:
            # Cleanup only if we created a temporary file
            if cleanup_pdf:
                print(
                    f"\n{Colors.YELLOW}🧹 Cleaning up temporary test files...{Colors.NC}"
                )
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

        # Show failed tests if any
        if self.failed_test_names:
            print(f"\n{Colors.RED}❌ FAILED TESTS:{Colors.NC}")
            for i, test_name in enumerate(self.failed_test_names, 1):
                print(f"{Colors.RED}  {i}. {test_name}{Colors.NC}")

        if self.failed_tests == 0:
            print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.NC}")
            return 0
        else:
            print(
                f"\n{Colors.RED}⚠️  {self.failed_tests} test(s) failed. See details above.{Colors.NC}"
            )
            return 1


if __name__ == "__main__":
    # Configuration options
    SAVE_RESPONSES = False  # Set to True to save all responses as JSON files

    tester = APITester(BASE_URL, save_response=SAVE_RESPONSES)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
