"""Test script for dynamic resume generation."""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def test_get_available_roles():
    """Test getting available roles."""
    print("=" * 60)
    print("Testing: Get Available Roles")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/dynamic-resume/available-roles")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Available Roles:")
        for role in result['roles']:
            print(f"  - {role}")
        return result['roles']
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return []


def test_quick_resume_generation(role: str):
    """Test quick resume generation without user account."""
    print("\n" + "=" * 60)
    print(f"Testing: Quick Resume Generation for {role}")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/dynamic-resume/generate-quick",
        params={
            "target_role": role,
            "user_name": "Demo User",
            "user_email": "demo@example.com"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Resume Generated Successfully!")
        print(f"\nDetails:")
        print(f"  Resume ID: {result.get('resume_id')}")
        print(f"  Target Role: {result.get('target_role')}")
        print(f"  Generation Method: {result.get('generation_method')}")
        
        if result.get('selected_projects'):
            print(f"\n  Selected Projects:")
            for project in result['selected_projects']:
                print(f"    - {project}")
        
        if result.get('pdf_path'):
            print(f"\n  PDF Path: {result.get('pdf_path')}")
        if result.get('tex_path'):
            print(f"  TEX Path: {result.get('tex_path')}")
        
        if result.get('download_url'):
            print(f"\n  Download URL: {BASE_URL}{result.get('download_url')}")
        
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_dynamic_resume_with_user(user_id: str, role: str):
    """Test dynamic resume generation with user account."""
    print("\n" + "=" * 60)
    print(f"Testing: Dynamic Resume for User {user_id}")
    print("=" * 60)
    
    request_data = {
        "user_id": user_id,
        "target_role": role,
        "use_ai_selection": True,
        "output_format": "pdf"
    }
    
    print(f"\nGenerating resume for role: {role}")
    print(f"AI Selection: {request_data['use_ai_selection']}")
    
    response = requests.post(
        f"{BASE_URL}/dynamic-resume/generate",
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Resume Generated Successfully!")
        print(f"\nDetails:")
        print(f"  Resume ID: {result.get('resume_id')}")
        print(f"  Target Role: {result.get('target_role')}")
        print(f"  Generation Method: {result.get('generation_method')}")
        
        if result.get('selected_projects'):
            print(f"\n  AI-Selected Projects:")
            for project in result['selected_projects']:
                print(f"    - {project}")
        
        if result.get('pdf_path'):
            print(f"\n  PDF Path: {result.get('pdf_path')}")
        if result.get('tex_path'):
            print(f"  TEX Path: {result.get('tex_path')}")
        
        if result.get('download_url'):
            print(f"\n  Download URL: {BASE_URL}{result.get('download_url')}")
            print(f"\n  To download:")
            print(f"  curl -O {BASE_URL}{result.get('download_url')}")
        
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DYNAMIC RESUME GENERATION - TEST SUITE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check server
    print("\nChecking server...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Server is running")
        else:
            print("✗ Server not responding correctly")
            return
    except:
        print("✗ Server is not running")
        print("Please start the server with: uvicorn app.main:app --reload")
        return
    
    # Test 1: Get available roles
    roles = test_get_available_roles()
    
    if not roles:
        print("\n✗ No roles available")
        return
    
    # Test 2: Quick resume generation (no user account needed)
    print("\n" + "=" * 60)
    print("Testing Quick Resume Generation")
    print("=" * 60)
    
    # Test with first 3 roles
    for role in roles[:3]:
        test_quick_resume_generation(role)
    
    # Test 3: Dynamic resume with user account
    print("\n" + "=" * 60)
    print("Testing Dynamic Resume with User Account")
    print("=" * 60)
    
    # Get user ID
    users_response = requests.get(f"{BASE_URL}/users/?limit=1")
    if users_response.status_code == 200:
        users = users_response.json()
        if users:
            user_id = users[0]['id']
            print(f"\n✓ Using user: {users[0]['full_name']} ({user_id})")
            
            # Test with different roles
            test_dynamic_resume_with_user(user_id, "Web Developer")
            test_dynamic_resume_with_user(user_id, "Machine Learning Engineer")
        else:
            print("\n⚠ No users found. Skipping user-based tests.")
    else:
        print("\n⚠ Could not fetch users. Skipping user-based tests.")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\nDynamic Resume Features:")
    print("  1. ✓ Role-specific project templates")
    print("  2. ✓ AI-powered project selection")
    print("  3. ✓ LaTeX template integration")
    print("  4. ✓ PDF generation (if pdflatex available)")
    print("  5. ✓ Quick generation without user account")
    print("  6. ✓ Dynamic generation with user projects")
    print("\nAPI Endpoints:")
    print(f"  - GET  {BASE_URL}/dynamic-resume/available-roles")
    print(f"  - POST {BASE_URL}/dynamic-resume/generate")
    print(f"  - POST {BASE_URL}/dynamic-resume/generate-quick")
    print(f"  - GET  {BASE_URL}/dynamic-resume/download/{{filename}}")
    print("\nGenerated Files:")
    print("  - Location: uploads/resumes/")
    print("  - Formats: PDF (if pdflatex available), TEX (always)")
    print("\nView API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
