#!/usr/bin/env python3
"""
Test script for the secure cleanup_all_resumes endpoint

This script demonstrates the security measures and proper usage.
"""

import json

import requests

# Configuration
# BASE_URL = "http://localhost:8000"  # Use local development server
BASE_URL = "https://115.29.170.231"  # This will be BLOCKED in production

# SSL Configuration
VERIFY_SSL = False


def test_cleanup_all_resumes():
    """Test the secure cleanup endpoint with proper authentication"""

    print("🧪 Testing cleanup_all_resumes endpoint")
    print("=" * 50)

    # Test 1: Try without any parameters (should fail)
    print("\n1. Testing without parameters:")
    response = requests.post(
        f"{BASE_URL}/api/v1/cleanup-all-resumes/", verify=VERIFY_SSL
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 2: Try with wrong token (should fail)
    print("\n2. Testing with wrong token:")
    data = {
        "confirmation_token": "WRONG_TOKEN",
        "confirm_action": "DELETE_ALL_RESUME_DATA",
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/cleanup-all-resumes/", data=data, verify=VERIFY_SSL
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 3: Try with correct token but wrong confirmation (should fail)
    print("\n3. Testing with correct token but wrong confirmation:")
    data = {
        "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
        "confirm_action": "WRONG_ACTION",
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/cleanup-all-resumes/", data=data, verify=VERIFY_SSL
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 4: Try with correct parameters (should succeed in DEBUG mode)
    print("\n4. Testing with correct parameters:")
    data = {
        "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
        "confirm_action": "DELETE_ALL_RESUME_DATA",
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/cleanup-all-resumes/", data=data, verify=VERIFY_SSL
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    print("\n" + "=" * 50)
    print("✅ Test completed!")


def demonstrate_production_security():
    """Demonstrate how the endpoint is blocked in production"""

    print("\n🔒 Production Security Test")
    print("=" * 50)
    print("Note: If you test this against a production server with DEBUG=False,")
    print("it will be blocked regardless of the correct token.")

    # This would be blocked in production
    production_url = "https://115.29.170.231"  # Example production URL
    data = {
        "confirmation_token": "CONFIRM_DELETE_ALL_RESUMES_2025",
        "confirm_action": "DELETE_ALL_RESUME_DATA",
    }

    try:
        response = requests.post(
            f"{production_url}/api/v1/cleanup-all-resumes/",
            data=data,
            verify=VERIFY_SSL,
        )
        print(f"Production Status: {response.status_code}")
        print(f"Production Response: {response.json()}")
    except Exception as e:
        print(f"Production test failed (expected): {e}")


if __name__ == "__main__":
    print("🚀 Secure Cleanup Endpoint Test")
    print("This endpoint removes ALL resume files and database entries!")
    print("It has multiple security layers to prevent accidental or malicious use.")

    # Show security measures
    print("\n🔐 Security Measures:")
    print("1. Only works in DEBUG mode (development/testing)")
    print("2. Requires correct confirmation token")
    print("3. Requires additional confirmation action")
    print("4. Comprehensive logging of all operations")
    print("5. IP and User-Agent logging for audit trail")

    # Ask for confirmation
    response = input("\nDo you want to proceed with the test? (yes/no): ")
    if response.lower() in ["yes", "y"]:
        test_cleanup_all_resumes()
        demonstrate_production_security()
    else:
        print("Test cancelled.")
