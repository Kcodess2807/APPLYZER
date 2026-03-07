"""Test script for job application with document generation."""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def test_single_job_application(user_id: str):
    """Test sending a single job application with documents."""
    print("=" * 60)
    print("Testing Single Job Application with Documents")
    print("=" * 60)
    
    application_data = {
        "user_id": user_id,
        "job_title": "Senior Full-Stack Engineer",
        "company": "TechCorp Inc",
        "job_description": """
        We are looking for a Senior Full-Stack Engineer to join our team.
        
        Requirements:
        - 5+ years of experience with React and Node.js
        - Strong experience with microservices architecture
        - Experience with cloud platforms (AWS/GCP)
        - Database design and optimization (PostgreSQL, MongoDB)
        - Real-time systems and WebSocket implementation
        
        Responsibilities:
        - Design and implement scalable web applications
        - Lead technical discussions and code reviews
        - Mentor junior developers
        - Collaborate with product team on feature development
        """,
        "hr_email": "hr@techcorp.example.com",
        "generate_documents": True,
        "email_tone": "professional"
    }
    
    print(f"\nJob: {application_data['job_title']}")
    print(f"Company: {application_data['company']}")
    print(f"Generate Documents: {application_data['generate_documents']}")
    print("\nSending application...")
    
    response = requests.post(
        f"{BASE_URL}/bulk-email/send-job-application",
        json=application_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Application sent successfully!")
        print(f"\nDetails:")
        print(json.dumps(result, indent=2))
        
        if result.get('details', {}).get('attachments'):
            print(f"\nAttachments:")
            for attachment in result['details']['attachments']:
                print(f"  - {attachment}")
        
        if result.get('details', {}).get('selected_projects'):
            print(f"\nSelected Projects:")
            for project in result['details']['selected_projects']:
                print(f"  - {project}")
        
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_bulk_job_applications(user_id: str):
    """Test sending bulk job applications."""
    print("\n" + "=" * 60)
    print("Testing Bulk Job Applications with Documents")
    print("=" * 60)
    
    bulk_data = {
        "user_id": user_id,
        "generate_documents": True,
        "email_tone": "professional",
        "jobs": [
            {
                "title": "Backend Engineer",
                "company": "StartupXYZ",
                "description": "Looking for backend engineer with Python and FastAPI experience",
                "hr_email": "jobs@startupxyz.example.com"
            },
            {
                "title": "Full-Stack Developer",
                "company": "InnovateCo",
                "description": "Full-stack developer needed for React and Node.js projects",
                "hr_email": "careers@innovateco.example.com"
            }
        ]
    }
    
    print(f"\nNumber of jobs: {len(bulk_data['jobs'])}")
    print(f"Generate Documents: {bulk_data['generate_documents']}")
    print("\nJobs:")
    for job in bulk_data['jobs']:
        print(f"  - {job['title']} at {job['company']}")
    
    print("\nSending bulk applications...")
    
    response = requests.post(
        f"{BASE_URL}/bulk-email/send-bulk-job-applications",
        json=bulk_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Bulk applications processed!")
        print(f"\nSummary:")
        print(f"  Total Sent: {result.get('total_sent', 0)}")
        print(f"  Failed: {result.get('failed', 0)}")
        
        if result.get('results'):
            print(f"\nSuccessful Applications:")
            for app in result['results']:
                print(f"  ✓ {app.get('email')}")
                if app.get('attachments'):
                    print(f"    Attachments: {', '.join(app['attachments'])}")
        
        if result.get('errors'):
            print(f"\nFailed Applications:")
            for error in result['errors']:
                print(f"  ✗ {error.get('job')} at {error.get('company')}: {error.get('error')}")
        
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_simple_bulk_email():
    """Test simple bulk email without documents (original functionality)."""
    print("\n" + "=" * 60)
    print("Testing Simple Bulk Email (No Documents)")
    print("=" * 60)
    
    email_data = {
        "recipients": [
            "test1@example.com",
            "test2@example.com"
        ],
        "subject": "Test Email from ApplyBot",
        "body": "<p>This is a test email without attachments.</p><p>Testing the original bulk email functionality.</p>"
    }
    
    print(f"\nRecipients: {len(email_data['recipients'])}")
    print(f"Subject: {email_data['subject']}")
    print("\nSending emails...")
    
    response = requests.post(
        f"{BASE_URL}/bulk-email/send-bulk-emails",
        json=email_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Emails sent!")
        print(f"\nSummary:")
        print(f"  Total Sent: {result.get('total_sent', 0)}")
        print(f"  Failed: {result.get('failed', 0)}")
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("JOB APPLICATION WITH DOCUMENTS - TEST SUITE")
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
    
    # Get user ID
    print("\nGetting test user...")
    users_response = requests.get(f"{BASE_URL}/users/?limit=1")
    if users_response.status_code == 200:
        users = users_response.json()
        if users:
            user_id = users[0]['id']
            print(f"✓ Using user: {users[0]['full_name']} ({user_id})")
        else:
            print("✗ No users found. Please create a user first.")
            return
    else:
        print("✗ Could not fetch users")
        return
    
    # Test 1: Simple bulk email (original functionality)
    test_simple_bulk_email()
    
    # Test 2: Single job application with documents
    print("\n" + "=" * 60)
    print("NOTE: The following tests will generate documents")
    print("=" * 60)
    input("\nPress Enter to continue with document generation tests...")
    
    test_single_job_application(user_id)
    
    # Test 3: Bulk job applications
    print("\n" + "=" * 60)
    input("\nPress Enter to test bulk job applications...")
    
    test_bulk_job_applications(user_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\nNew Features Available:")
    print("  1. ✓ Send job applications with auto-generated documents")
    print("  2. ✓ AI-selected relevant projects for each job")
    print("  3. ✓ Auto-generated resume and cover letter")
    print("  4. ✓ Personalized email body (cold DM)")
    print("  5. ✓ Bulk job applications with documents")
    print("  6. ✓ All emails tracked in Google Sheets")
    print("\nAPI Endpoints:")
    print(f"  - POST {BASE_URL}/bulk-email/send-job-application")
    print(f"  - POST {BASE_URL}/bulk-email/send-bulk-job-applications")
    print(f"  - POST {BASE_URL}/bulk-email/send-bulk-emails (original)")
    print("\nGenerated Files Location:")
    print("  - uploads/applications/")
    print("\nView API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
