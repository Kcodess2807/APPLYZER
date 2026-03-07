"""Quick test script to verify API endpoints are working."""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print(f"✓ Health check: {response.status_code}")
    print(f"  Response: {response.json()}")
    return response.status_code == 200

def test_create_user():
    """Test user creation."""
    user_data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "full_name": "Test User",
        "phone": "+1234567890",
        "linkedin_url": "https://linkedin.com/in/testuser",
        "professional_summary": "Test user for API testing"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    print(f"\n✓ Create user: {response.status_code}")
    
    if response.status_code == 201:
        user = response.json()
        print(f"  User ID: {user['id']}")
        return user['id']
    else:
        print(f"  Error: {response.text}")
        return None

def test_add_skill(user_id):
    """Test adding skills."""
    skill_data = {
        "category": "Technical Skills",
        "items": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "display_order": 0
    }
    
    response = requests.post(
        f"{BASE_URL}/skills/",
        params={"user_id": user_id},
        json=skill_data
    )
    print(f"\n✓ Add skill: {response.status_code}")
    if response.status_code == 201:
        skill = response.json()
        print(f"  Skill ID: {skill['id']}")
        return skill['id']
    else:
        print(f"  Error: {response.text}")
        return None

def test_add_education(user_id):
    """Test adding education."""
    education_data = {
        "degree": "Bachelor of Computer Science",
        "institution": "Test University",
        "year": "2018 - 2022",
        "coursework": "Data Structures, Algorithms, Machine Learning",
        "display_order": 0
    }
    
    response = requests.post(
        f"{BASE_URL}/education/",
        params={"user_id": user_id},
        json=education_data
    )
    print(f"\n✓ Add education: {response.status_code}")
    if response.status_code == 201:
        education = response.json()
        print(f"  Education ID: {education['id']}")
        return education['id']
    else:
        print(f"  Error: {response.text}")
        return None

def test_add_experience(user_id):
    """Test adding experience."""
    experience_data = {
        "role": "Software Engineer",
        "company": "Test Corp",
        "location": "San Francisco, CA",
        "duration": "Jan 2022 - Present",
        "achievements": [
            "Led development of major feature",
            "Improved system performance by 40%",
            "Mentored junior developers"
        ],
        "display_order": 0
    }
    
    response = requests.post(
        f"{BASE_URL}/experiences/",
        params={"user_id": user_id},
        json=experience_data
    )
    print(f"\n✓ Add experience: {response.status_code}")
    if response.status_code == 201:
        experience = response.json()
        print(f"  Experience ID: {experience['id']}")
        return experience['id']
    else:
        print(f"  Error: {response.text}")
        return None

def test_add_project(user_id):
    """Test adding project."""
    project_data = {
        "title": "Test E-commerce Platform",
        "description": "Built a scalable e-commerce platform with microservices architecture",
        "technologies": ["React", "Node.js", "MongoDB", "AWS"],
        "category": "Web Development",
        "project_url": "https://github.com/test/project",
        "skills_demonstrated": ["Full-stack development", "Cloud deployment"],
        "achievements": ["Handled 10K+ daily users", "99.9% uptime"],
        "keywords": ["ecommerce", "scalable"]
    }
    
    response = requests.post(
        f"{BASE_URL}/projects/",
        params={"user_id": user_id},
        json=project_data
    )
    print(f"\n✓ Add project: {response.status_code}")
    if response.status_code == 201:
        project = response.json()
        print(f"  Project ID: {project['id']}")
        return project['id']
    else:
        print(f"  Error: {response.text}")
        return None

def test_get_profile(user_id):
    """Test getting complete profile."""
    response = requests.get(f"{BASE_URL}/profile/{user_id}")
    print(f"\n✓ Get complete profile: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"  User: {profile['user']['full_name']}")
        print(f"  Skills: {len(profile['skills'])} categories")
        print(f"  Education: {len(profile['education'])} entries")
        print(f"  Experiences: {len(profile['experiences'])} entries")
        print(f"  Projects: {len(profile['projects'])} entries")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_get_profile_summary(user_id):
    """Test getting profile summary."""
    response = requests.get(f"{BASE_URL}/profile/{user_id}/summary")
    print(f"\n✓ Get profile summary: {response.status_code}")
    
    if response.status_code == 200:
        summary = response.json()
        print(f"  Completeness: {summary['completeness_score']}%")
        print(f"  Counts: {summary['counts']}")
        if summary['missing_sections']:
            print(f"  Missing: {summary['missing_sections']}")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_send_followups():
    """Test sending follow-up emails."""
    print("\n" + "=" * 60)
    print("Testing Bulk Email Follow-ups Endpoint")
    print("=" * 60)
    
    response = requests.post(f"{BASE_URL}/bulk-email/send-followups")
    print(f"\n✓ Send follow-ups: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  Success: {result.get('success')}")
        print(f"  Message: {result.get('message')}")
        
        details = result.get('details', {})
        print(f"  Sent: {details.get('sent', 0)}")
        print(f"  Errors: {details.get('errors', 0)}")
        print(f"  Timestamp: {details.get('timestamp', 'N/A')}")
        
        config = result.get('config', {})
        print(f"  Config:")
        print(f"    - Follow-up interval: {config.get('followup_interval_days', 'N/A')} days")
        print(f"    - Max follow-ups: {config.get('max_followup_count', 'N/A')}")
        
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        return
    
    # Create user
    user_id = test_create_user()
    if not user_id:
        print("\n❌ Failed to create user")
        return
    
    # Add profile data
    test_add_skill(user_id)
    test_add_education(user_id)
    test_add_experience(user_id)
    test_add_project(user_id)
    
    # Get complete profile
    test_get_profile(user_id)
    test_get_profile_summary(user_id)
    
    # Test bulk email follow-ups
    test_send_followups()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print(f"\nTest User ID: {user_id}")
    print(f"View in Swagger: http://localhost:8000/docs")
    print(f"Get profile: {BASE_URL}/profile/{user_id}")


if __name__ == "__main__":
    main()
