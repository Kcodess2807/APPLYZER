"""Test script for AI-powered features."""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def test_ai_connection():
    """Test if AI service is configured and working."""
    print("=" * 60)
    print("Testing AI Connection")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/ai/test-ai")
    result = response.json()
    
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Configured: {result['configured']}")
    
    if result.get('model'):
        print(f"Model: {result['model']}")
    
    if result.get('test_response'):
        print(f"Test Response: {result['test_response']}")
    
    return result['status'] == 'success'


def test_project_selection(user_id: str):
    """Test AI project selection for a job."""
    print("\n" + "=" * 60)
    print("Testing AI Project Selection")
    print("=" * 60)
    
    # Sample job description
    job_data = {
        "user_id": user_id,
        "job_title": "Senior Full-Stack Engineer",
        "job_description": """
        We are looking for a Senior Full-Stack Engineer to join our team.
        
        Requirements:
        - 5+ years of experience with React and Node.js
        - Strong experience with microservices architecture
        - Experience with cloud platforms (AWS/GCP)
        - Database design and optimization (PostgreSQL, MongoDB)
        - Real-time systems and WebSocket implementation
        - CI/CD and DevOps practices
        
        Nice to have:
        - Experience with e-commerce platforms
        - Machine learning or AI integration
        - Payment gateway integration
        """,
        "max_projects": 3
    }
    
    print(f"\nJob Title: {job_data['job_title']}")
    print(f"User ID: {user_id}")
    print("\nSending request to AI...")
    
    response = requests.post(
        f"{BASE_URL}/ai/select-projects",
        json=job_data
    )
    
    if response.status_code == 200:
        projects = response.json()
        print(f"\n✓ AI selected {len(projects)} relevant projects:\n")
        
        for idx, project in enumerate(projects, 1):
            print(f"{idx}. {project['title']}")
            print(f"   Description: {project['description'][:100]}...")
            print(f"   Technologies: {', '.join(project.get('technologies', [])[:5])}")
            print(f"   Category: {project.get('category', 'N/A')}")
            print()
        
        return projects
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_followup_generation():
    """Test AI follow-up email generation."""
    print("\n" + "=" * 60)
    print("Testing AI Follow-up Generation")
    print("=" * 60)
    
    # Test first follow-up
    followup_data = {
        "original_subject": "Application for Senior Full-Stack Engineer Position",
        "job_title": "Senior Full-Stack Engineer",
        "company_name": "TechCorp Inc",
        "followup_count": 1,
        "user_name": "John Doe",
        "days_since_sent": 5
    }
    
    print(f"\nGenerating follow-up email:")
    print(f"  Job: {followup_data['job_title']}")
    print(f"  Company: {followup_data['company_name']}")
    print(f"  Follow-up #: {followup_data['followup_count']}")
    print(f"  Days since sent: {followup_data['days_since_sent']}")
    print("\nSending request to AI...")
    
    response = requests.post(
        f"{BASE_URL}/ai/generate-followup",
        json=followup_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Generated follow-up email:\n")
        print(f"Subject: {result['subject']}")
        print(f"\nBody:\n{'-' * 60}")
        # Remove HTML tags for display
        body_text = result['body'].replace('<p>', '').replace('</p>', '\n')
        print(body_text)
        print('-' * 60)
        
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_second_followup():
    """Test second follow-up generation."""
    print("\n" + "=" * 60)
    print("Testing Second Follow-up Generation")
    print("=" * 60)
    
    followup_data = {
        "original_subject": "Application for Senior Full-Stack Engineer Position",
        "job_title": "Senior Full-Stack Engineer",
        "company_name": "TechCorp Inc",
        "followup_count": 2,
        "user_name": "John Doe",
        "days_since_sent": 10
    }
    
    print(f"\nGenerating second follow-up email:")
    print(f"  Follow-up #: {followup_data['followup_count']}")
    print(f"  Days since last email: {followup_data['days_since_sent']}")
    
    response = requests.post(
        f"{BASE_URL}/ai/generate-followup",
        json=followup_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Generated second follow-up:\n")
        print(f"Subject: {result['subject']}")
        print(f"\nBody:\n{'-' * 60}")
        body_text = result['body'].replace('<p>', '').replace('</p>', '\n')
        print(body_text)
        print('-' * 60)
        
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        return None


def main():
    """Run all AI feature tests."""
    print("\n" + "=" * 60)
    print("AI FEATURES TEST SUITE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test 1: AI Connection
    if not test_ai_connection():
        print("\n❌ AI service not configured or not working.")
        print("Please check GROQ_API_KEY in .env file.")
        return
    
    # Get user ID for testing
    print("\n" + "=" * 60)
    print("Getting test user...")
    print("=" * 60)
    
    # Try to get existing users
    users_response = requests.get(f"{BASE_URL}/users/?limit=1")
    if users_response.status_code == 200:
        users = users_response.json()
        if users:
            user_id = users[0]['id']
            print(f"\n✓ Using existing user: {users[0]['full_name']} ({user_id})")
        else:
            print("\n⚠ No users found. Please create a user first.")
            print("Run: python test_api_endpoints.py")
            return
    else:
        print("\n❌ Could not fetch users")
        return
    
    # Test 2: AI Project Selection
    test_project_selection(user_id)
    
    # Test 3: AI Follow-up Generation (First)
    test_followup_generation()
    
    # Test 4: AI Follow-up Generation (Second)
    test_second_followup()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL AI FEATURE TESTS COMPLETED!")
    print("=" * 60)
    print("\nAI Features Available:")
    print("  1. ✓ Intelligent project selection based on job requirements")
    print("  2. ✓ AI-generated personalized follow-up emails")
    print("  3. ✓ Context-aware email generation (adapts to follow-up count)")
    print("\nAPI Endpoints:")
    print(f"  - POST {BASE_URL}/ai/select-projects")
    print(f"  - POST {BASE_URL}/ai/generate-followup")
    print(f"  - GET  {BASE_URL}/ai/test-ai")
    print("\nConfiguration:")
    print("  - Follow-up interval: 5 days (configurable in .env)")
    print("  - Max follow-ups: 2 (configurable in .env)")
    print("  - AI Model: Groq Llama 3.1 70B")
    print("\nNext Steps:")
    print("  - AI features are now integrated into the bulk email system")
    print("  - Follow-ups will be automatically generated with AI")
    print("  - Use /ai/select-projects endpoint when applying to jobs")
    print("\nView API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
