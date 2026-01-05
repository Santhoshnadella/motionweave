import requests
import time
import os
import sys

# Configuration
API_URL = "http://localhost:8000"
TEST_ASSETS_DIR = "tests/assets"

# Ensure we have dummy assets
if not os.path.exists(TEST_ASSETS_DIR):
    os.makedirs(TEST_ASSETS_DIR)
    # Create dummy files
    with open(f"{TEST_ASSETS_DIR}/test_char.png", "wb") as f:
        f.write(os.urandom(1024)) # Dummy bytes
    with open(f"{TEST_ASSETS_DIR}/test_ref.mp4", "wb") as f:
        f.write(os.urandom(1024))

def test_health():
    print("[TEST] Checking API Health...")
    try:
        r = requests.get(f"{API_URL}/docs")
        if r.status_code == 200:
            print("✅ API is UP")
            return True
        else:
            print(f"❌ API returned {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_job_submission():
    print("[TEST] Submitting Job...")
    
    files = {
        'character_image': open(f"{TEST_ASSETS_DIR}/test_char.png", 'rb'),
        'reference_video': open(f"{TEST_ASSETS_DIR}/test_ref.mp4", 'rb')
    }
    data = {
        'config_json': '{"duration": 2, "resolution": "512x512"}'
    }
    
    try:
        r = requests.post(f"{API_URL}/api/v1/jobs/create", files=files, data=data)
        if r.status_code == 200:
            job = r.json()
            print(f"✅ Job Created: {job['id']}")
            return job['id']
        else:
            print(f"❌ Job Submission Failed: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return None

def main():
    if not test_health():
        sys.exit(1)
        
    job_id = test_job_submission()
    if not job_id:
        sys.exit(1)
        
    print("✅ Integration Tests Passed (Mock Mode)")

if __name__ == "__main__":
    main()
