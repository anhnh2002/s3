#!/usr/bin/env python3
"""
Simple test script for the S3-like Storage API
"""
import requests
import io

# API base URL
BASE_URL = "http://49.213.89.191:8005"


def test_upload_file():
    """Test file upload"""
    print("Testing file upload...")
    
    # Create a test file
    test_content = b"This is a test file content for the S3-like storage API."
    files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
    
    response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Upload successful!")
        print(f"  File ID: {data['file_id']}")
        print(f"  URL: {data['url']}")
        print(f"  Size: {data['size']} bytes")
        return data['file_id']
    else:
        print(f"✗ Upload failed: {response.text}")
        return None

def test_download_file(file_id):
    """Test file download"""
    print(f"\nTesting file download for {file_id}...")
    
    response = requests.get(f"{BASE_URL}/files/{file_id}")
    
    if response.status_code == 200:
        print("✓ Download successful!")
        print(f"  Content: {response.content[:50]}...")
    else:
        print(f"✗ Download failed: {response.text}")

def main():
    print("=" * 50)
    print("S3-like Storage API - Test Suite")
    print("=" * 50)
    
    
    # Test upload
    file_id = test_upload_file()
    
    if file_id:
        test_download_file(file_id)
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to the API.")
        print("  Make sure the service is running: docker-compose up -d")
    except Exception as e:
        print(f"✗ Error: {e}")

