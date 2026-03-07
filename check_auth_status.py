"""Quick script to check authentication status."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_sheets_auth():
    """Check Sheets authentication."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sheets/status", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def check_token_file():
    """Check if token file exists."""
    return os.path.exists('credentials/sheets_token.json')

def main():
    print("=" * 60)
    print("AUTHENTICATION STATUS CHECK")
    print("=" * 60)
    print()
    
    # Check server
    print("1. FastAPI Server:")
    if check_server():
        print("   ✓ Running")
    else:
        print("   ✗ Not running")
        print("   Start with: uvicorn app.main:app --reload")
    print()
    
    # Check token file
    print("2. Token File:")
    if check_token_file():
        print("   ✓ credentials/sheets_token.json exists")
    else:
        print("   ✗ credentials/sheets_token.json not found")
    print()
    
    # Check API status
    print("3. API Authentication Status:")
    status = check_sheets_auth()
    if status:
        if status.get('authenticated'):
            print("   ✓ Authenticated")
            print()
            print("=" * 60)
            print("✓ ALL CHECKS PASSED!")
            print("=" * 60)
            print()
            print("You can now run:")
            print("  python initialize_email_tracking.py")
        else:
            print("   ✗ Not authenticated")
            print()
            print("Run: python authenticate_sheets.py")
    else:
        print("   ✗ Could not check (server not running?)")
    print()

if __name__ == "__main__":
    main()
