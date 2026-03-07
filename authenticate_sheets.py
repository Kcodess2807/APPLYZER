"""Authenticate Google Sheets using the existing API endpoint."""
import os
import sys
import webbrowser
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

def check_server_running():
    """Check if FastAPI server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_auth_status():
    """Check if Sheets is already authenticated."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sheets/status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get('authenticated', False)
    except:
        pass
    return False

def get_auth_url():
    """Get the authorization URL."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sheets/authenticate", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('authorization_url')
    except Exception as e:
        print(f"Error getting auth URL: {e}")
    return None

def main():
    """Guide user through Sheets authentication."""
    print("=" * 60)
    print("GOOGLE SHEETS AUTHENTICATION")
    print("=" * 60)
    print()
    
    # Check if server is running
    print("Checking if FastAPI server is running...")
    if not check_server_running():
        print("✗ FastAPI server is not running")
        print()
        print("Please start the server first:")
        print("  uvicorn app.main:app --reload")
        print()
        print("Then run this script again.")
        return
    
    print("✓ FastAPI server is running")
    print()
    
    # Check if already authenticated
    if check_auth_status():
        print("✓ Google Sheets is already authenticated!")
        print()
        response = input("Do you want to re-authenticate? (y/n): ")
        if response.lower() != 'y':
            print()
            print("You can now run:")
            print("  python initialize_email_tracking.py")
            return
        print()
    
    # Get authorization URL
    print("Getting authorization URL...")
    auth_url = get_auth_url()
    
    if not auth_url:
        print("✗ Could not get authorization URL")
        print()
        print("Please check:")
        print("  1. Server is running: uvicorn app.main:app --reload")
        print("  2. credentials/sheets_credentials.json exists")
        print("  3. Check server logs for errors")
        return
    
    print("✓ Authorization URL obtained")
    print()
    print("=" * 60)
    print("AUTHENTICATION STEPS")
    print("=" * 60)
    print()
    print("1. A browser window will open")
    print("2. Sign in with your Google account")
    print("3. Grant permissions to access Google Sheets")
    print("4. You'll be redirected back to the app")
    print("5. Look for 'Google Sheets authenticated' message")
    print()
    
    response = input("Ready to authenticate? (y/n): ")
    if response.lower() != 'y':
        print()
        print("To authenticate later, visit:")
        print(f"  {auth_url}")
        return
    
    print()
    print("Opening browser...")
    webbrowser.open(auth_url)
    
    print()
    print("Waiting for authentication...")
    print("(This may take a few seconds)")
    print()
    
    # Wait and check for authentication
    for i in range(30):
        time.sleep(1)
        if check_auth_status():
            print()
            print("=" * 60)
            print("✓ AUTHENTICATION SUCCESSFUL!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Run: python initialize_email_tracking.py")
            print("  2. This will create the EmailTracking sheet")
            print("  3. Then you can start sending bulk emails!")
            print()
            return
    
    print()
    print("Authentication is taking longer than expected.")
    print()
    print("Please check:")
    print("  1. Did you complete the authentication in the browser?")
    print("  2. Check the server logs for any errors")
    print("  3. Try running this script again")
    print()
    print("Or manually check status:")
    print(f"  curl {API_BASE_URL}/api/v1/sheets/status")

if __name__ == "__main__":
    main()
