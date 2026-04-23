import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_service import AIService

@patch("app.services.ai_service.requests.post")
def test_select_relevant_projects_mock(mock_post):
    # Mock the API response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "[0, 2]"}}
        ]
    }
    mock_post.return_value = mock_response

    ai_service = AIService()
    # Force api_key to test API behavior
    ai_service.api_key = "test_key"
    
    projects = [
        {"title": "Proj A"},
        {"title": "Proj B"},
        {"title": "Proj C"}
    ]
    
    result = ai_service.select_relevant_projects(projects, "We need Python", "Python Dev")
    
    assert len(result) == 2
    assert result[0]["title"] == "Proj A"
    assert result[1]["title"] == "Proj C"

@patch("app.services.ai_service.requests.post")
def test_generate_followup_email_mock(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "<p>Following up on my application.</p>"}}
        ]
    }
    mock_post.return_value = mock_response

    ai_service = AIService()
    ai_service.api_key = "test_key"

    result = ai_service.generate_followup_email(
        original_subject="Application",
        job_title="Dev",
        company_name="Tech Corp",
        followup_count=1,
        user_name="John",
        days_since_sent=5
    )
    
    assert "<p>Following up on my application.</p>" in result
