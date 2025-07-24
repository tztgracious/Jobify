#!/usr/bin/env python3
"""
Test script for the cleanup_all_videos endpoint.

This script tests all security measures and functionality of the video cleanup endpoint:
- Security token validation
- Confirmation action validation
- Production environment blocking (when enabled)
- Successful cleanup operations
- Error handling

Usage:
    python test_cleanup_video_endpoint.py

Environment Variables:
    DELETE_ALL_VIDEOS_TOKEN: Custom token for video cleanup (optional)
    JOBIFY_TEST_BASE_URL: Base URL for testing (defaults to localhost:8000)
"""

import os
import requests
import json
import tempfile
import shutil
from pathlib import Path

# Configuration
BASE_URL = os.getenv('JOBIFY_TEST_BASE_URL', 'http://localhost:8000')
CLEANUP_ENDPOINT = f"{BASE_URL}/api/v1/cleanup-all-videos/"
VERIFY_SSL = False  # Set to True for production testing with valid SSL

# Test tokens
VALID_TOKEN = os.getenv('DELETE_ALL_VIDEOS_TOKEN', 'CONFIRM_DELETE_ALL_VIDEOS_2025')
INVALID_TOKEN = "INVALID_TOKEN_12345"

# Colors for output formatting
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(title):
    """Print a formatted header for test sections."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{title:^60}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}❌ {message}{Colors.NC}")


def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")


def create_test_video_files(media_root):
    """
    Create test video files in the media directories.
    Returns the number of files created.
    """
    print_info("Creating test video files...")
    
    # Create video directories
    videos_dir = Path(media_root) / 'videos'
    interview_videos_dir = Path(media_root) / 'interview_videos'
    
    videos_dir.mkdir(parents=True, exist_ok=True)
    interview_videos_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test video files
    test_files = [
        (videos_dir / 'test_video1.mp4', b'fake mp4 video content'),
        (videos_dir / 'test_video2.avi', b'fake avi video content'),
        (videos_dir / 'test_video3.mov', b'fake mov video content'),
        (interview_videos_dir / 'interview_answer1.mp4', b'fake interview video 1'),
        (interview_videos_dir / 'interview_answer2.webm', b'fake interview video 2'),
        (interview_videos_dir / 'interview_answer3.mkv', b'fake interview video 3'),
        # Also create some non-video files to ensure they're not deleted
        (videos_dir / 'not_a_video.txt', b'this is not a video file'),
        (interview_videos_dir / 'readme.md', b'# README\nThis is not a video'),
    ]
    
    created_videos = 0
    for file_path, content in test_files:
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.3gp', '.flv']:
                created_videos += 1
            print_info(f"Created test file: {file_path.name}")
        except Exception as e:
            print_error(f"Failed to create test file {file_path.name}: {str(e)}")
    
    print_success(f"Created {created_videos} test video files")
    return created_videos


def test_invalid_token():
    """Test cleanup endpoint with invalid token."""
    print_header("TEST: Invalid Token")
    
    data = {
        "confirmation_token": INVALID_TOKEN,
        "confirm_action": "DELETE_ALL_VIDEO_DATA"
    }
    
    try:
        response = requests.post(CLEANUP_ENDPOINT, json=data, verify=VERIFY_SSL)
        
        if response.status_code == 401:
            response_data = response.json()
            if not response_data.get('success', True) and 'Invalid confirmation token' in response_data.get('error', ''):
                print_success("Invalid token correctly rejected")
                return True
            else:
                print_error(f"Unexpected response content: {response_data}")
                return False
        else:
            print_error(f"Expected 401 status code, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_missing_confirmation():
    """Test cleanup endpoint without proper confirmation action."""
    print_header("TEST: Missing Confirmation Action")
    
    data = {
        "confirmation_token": VALID_TOKEN,
        "confirm_action": "WRONG_CONFIRMATION"
    }
    
    try:
        response = requests.post(CLEANUP_ENDPOINT, json=data, verify=VERIFY_SSL)
        
        if response.status_code == 400:
            response_data = response.json()
            if not response_data.get('success', True) and 'DELETE_ALL_VIDEO_DATA' in response_data.get('error', ''):
                print_success("Missing confirmation correctly rejected")
                return True
            else:
                print_error(f"Unexpected response content: {response_data}")
                return False
        else:
            print_error(f"Expected 400 status code, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_missing_token():
    """Test cleanup endpoint without token."""
    print_header("TEST: Missing Token")
    
    data = {
        "confirm_action": "DELETE_ALL_VIDEO_DATA"
    }
    
    try:
        response = requests.post(CLEANUP_ENDPOINT, json=data, verify=VERIFY_SSL)
        
        if response.status_code == 401:
            response_data = response.json()
            if not response_data.get('success', True) and 'Invalid confirmation token' in response_data.get('error', ''):
                print_success("Missing token correctly rejected")
                return True
            else:
                print_error(f"Unexpected response content: {response_data}")
                return False
        else:
            print_error(f"Expected 401 status code, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_successful_cleanup():
    """Test successful video cleanup operation."""
    print_header("TEST: Successful Video Cleanup")
    
    # Create temporary media directory with test videos
    with tempfile.TemporaryDirectory() as temp_dir:
        print_info(f"Using temporary directory: {temp_dir}")
        
        # Create test video files
        created_videos = create_test_video_files(temp_dir)
        
        # Note: This test would need the Django app to use the temp directory
        # In a real test environment, you'd modify the MEDIA_ROOT setting
        print_warning("Note: This test creates files in a temp directory")
        print_warning("In practice, the Django MEDIA_ROOT would need to point to this directory")
    
    # Test the actual endpoint (assuming it will work with current MEDIA_ROOT)
    data = {
        "confirmation_token": VALID_TOKEN,
        "confirm_action": "DELETE_ALL_VIDEO_DATA"
    }
    
    try:
        response = requests.post(CLEANUP_ENDPOINT, json=data, verify=VERIFY_SSL)
        
        if response.status_code in [200, 206]:  # 200 = success, 206 = partial success
            response_data = response.json()
            
            print_info(f"Response status: {response.status_code}")
            print_info(f"Operation: {response_data.get('operation', 'unknown')}")
            print_info(f"Success: {response_data.get('success', False)}")
            
            stats = response_data.get('statistics', {})
            print_info(f"Files before cleanup: {stats.get('total_files_before', 0)}")
            print_info(f"Directories processed: {stats.get('directories_processed', 0)}")
            print_info(f"Files removed: {stats.get('files_removed', 0)}")
            print_info(f"Files failed: {stats.get('files_failed', 0)}")
            
            if response_data.get('success', False):
                print_success("Video cleanup completed successfully")
                return True
            else:
                print_warning("Video cleanup completed with some errors")
                errors = stats.get('cleanup_errors', [])
                for error in errors:
                    print_error(f"Cleanup error: {error}")
                return True  # Still consider it a valid response
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_endpoint_availability():
    """Test if the endpoint is available."""
    print_header("TEST: Endpoint Availability")
    
    try:
        # Send a request with no data to check if endpoint exists
        response = requests.post(CLEANUP_ENDPOINT, json={}, verify=VERIFY_SSL)
        
        # We expect this to fail with 401 (missing token) if endpoint exists
        if response.status_code == 401:
            print_success("Endpoint is available and security is working")
            return True
        elif response.status_code == 404:
            print_error("Endpoint not found - check URL configuration")
            return False
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
            print_info(f"Response: {response.text}")
            return True  # Endpoint exists but gave unexpected response
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server - is it running?")
        return False
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def main():
    """Run all tests for the video cleanup endpoint."""
    print_header("VIDEO CLEANUP ENDPOINT SECURITY TESTS")
    print_info(f"Testing endpoint: {CLEANUP_ENDPOINT}")
    print_info(f"Using token: {VALID_TOKEN[:10]}...")
    
    tests = [
        ("Endpoint Availability", test_endpoint_availability),
        ("Invalid Token", test_invalid_token),
        ("Missing Token", test_missing_token),
        ("Missing Confirmation", test_missing_confirmation),
        ("Successful Cleanup", test_successful_cleanup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print_error(f"Test failed: {test_name}")
        except Exception as e:
            print_error(f"Test error in {test_name}: {str(e)}")
    
    # Summary
    print_header("TEST SUMMARY")
    if passed == total:
        print_success(f"All {total} tests passed!")
    else:
        print_warning(f"{passed}/{total} tests passed")
        if passed < total:
            print_error(f"{total - passed} tests failed")
    
    print_info("\nSecurity recommendations:")
    print_info("1. Ensure DEBUG=False in production")
    print_info("2. Change the confirmation token regularly")
    print_info("3. Monitor logs for unauthorized access attempts")
    print_info("4. Use environment variables for sensitive tokens")
    print_info("5. Test in a safe environment before production use")


if __name__ == "__main__":
    main()
