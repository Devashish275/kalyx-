import requests
import sys
import uuid
import os

# Adjust path to import from app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.routers.auth import hash_password, verify_password

BASE_URL = "http://localhost:8000/api"

def run_audit():
    print("=== STARTING AUTHENTICATION AUDIT ===")

    # 0. Direct Password Hashing/Verification Type Audit (Failure Reproduction)
    print("\n0. Direct Password Hashing & Verification Type Safety Test:")
    plain_pw = "SuperSecurePass123!"
    
    # Hash password to string
    hashed_str = hash_password(plain_pw)
    print(f"   Generated hash (str): {hashed_str} (Type: {type(hashed_str)})")
    
    # Verify with string hash (should succeed)
    verify_str_result = verify_password(plain_pw, hashed_str)
    print(f"   Verification with str hash: {verify_str_result}")
    
    # Simulate DB returning bytes (common with PostgreSQL on Render)
    hashed_bytes = hashed_str.encode('utf-8')
    print(f"   Simulating DB returned bytes hash: {hashed_bytes} (Type: {type(hashed_bytes)})")
    
    # Verify with bytes hash (will fail/return False before the fix due to .encode('utf-8') on bytes)
    verify_bytes_result = verify_password(plain_pw, hashed_bytes)
    print(f"   Verification with bytes hash: {verify_bytes_result}")
    
    if not verify_bytes_result:
        print("   [REPRODUCED FAILURE] verify_password failed when hashed password is bytes!")
    else:
        print("   [SUCCESS] verify_password succeeded when hashed password is bytes!")

    # 1. Signup Flow
    unique_suffix = str(uuid.uuid4())[:8]
    email = f"audit_{unique_suffix}@stanford.edu"
    username = f"audituser_{unique_suffix}"
    password = "MySecurePassword123!"
    full_name = "Audit User"

    signup_payload = {
        "email": email,
        "username": username,
        "password": password,
        "full_name": full_name
    }
    print(f"\n1. Attempting Signup with email={email}, username={username}...")
    try:
        r = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload)
        print(f"   Signup response status: {r.status_code}")
        if r.status_code != 200:
            print(f"   Signup failed: {r.text}")
            sys.exit(1)
        data = r.json()
        print("   Signup successful! Received Token.")
        assert "access_token" in data
        assert data["user"]["email"] == email
        assert data["user"]["username"] == username
    except Exception as e:
        print(f"   Signup exception: {e}")
        sys.exit(1)

    # 2. Login Flow - by Email
    login_payload_email = {
        "username_or_email": email,
        "password": password
    }
    print(f"\n2. Attempting Login by EMAIL={email}...")
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_payload_email)
        print(f"   Login (Email) response status: {r.status_code}")
        if r.status_code != 200:
            print(f"   Login failed: {r.text}")
        else:
            data = r.json()
            print("   Login by Email successful!")
            assert "access_token" in data
    except Exception as e:
        print(f"   Login by Email exception: {e}")

    # 3. Login Flow - by Username
    login_payload_username = {
        "username_or_email": username,
        "password": password
    }
    print(f"\n3. Attempting Login by USERNAME={username}...")
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_payload_username)
        print(f"   Login (Username) response status: {r.status_code}")
        if r.status_code != 200:
            print(f"   Login failed: {r.text}")
        else:
            data = r.json()
            print("   Login by Username successful!")
            assert "access_token" in data
    except Exception as e:
        print(f"   Login by Username exception: {e}")

    # 4. Login Flow - Case Insensitive / Whitespace
    login_payload_case = {
        "username_or_email": f"  {username.upper()}  ",
        "password": password
    }
    print(f"\n4. Attempting Login by UPPERCASE & WHITESPACE USERNAME='  {username.upper()}  '...")
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_payload_case)
        print(f"   Login (Case/Whitespace) response status: {r.status_code}")
        if r.status_code != 200:
            print(f"   Login failed: {r.text}")
        else:
            data = r.json()
            print("   Login by Case/Whitespace successful!")
            assert "access_token" in data
    except Exception as e:
        print(f"   Login by Case/Whitespace exception: {e}")

if __name__ == "__main__":
    run_audit()
