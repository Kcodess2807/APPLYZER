"""API endpoints for AI-powered features."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database.base import get_db
from app.services.project_service import ProjectService
from app.services.ai_service import AIService
from app.schemas.project import ProjectResponse

router = APIRouter()


class ProjectSelectionRequest(BaseModel):
    """Request model for AI project selection."""
    user_id: str
    job_title: str
    job_description: str
    max_projects: int = 3


class FollowUpRequest(BaseModel):
    """Request model for AI follow-up generation."""
    original_subject: str
    job_title: str
    company_name: str
    followup_count: int = 1
    user_name: str = "Applicant"
    days_since_sent: int = 5


class FollowUpResponse(BaseModel):
    """Response model for follow-up generation."""
    subject: str
    body: str
    followup_count: int


@router.post("/select-projects", response_model=List[ProjectResponse])
async def select_relevant_projects(
    request: ProjectSelectionRequest,
    db: Session = Depends(get_db)
):
    """
    Use AI to select the most relevant projects for a job application.
    
    This endpoint analyzes the job description and user's projects to select
    the most relevant ones that demonstrate the best fit for the role.
    """
    try:
        project_service = ProjectService(db)
        
        selected_projects = project_service.select_relevant_projects_for_job(
            user_id=request.user_id,
            job_description=request.job_description,
            job_title=request.job_title,
            max_projects=request.max_projects
        )
        
        if not selected_projects:
            raise HTTPException(
                status_code=404,
                detail="No projects found for user or AI selection failed"
            )
        
        return selected_projects
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-followup", response_model=FollowUpResponse)
async def generate_followup_email(request: FollowUpRequest):
    """
    Generate a personalized follow-up email using AI.
    
    This endpoint creates a professional, contextual follow-up email
    based on the job details and follow-up count.
    """
    try:
        ai_service = AIService()
        
        # Generate follow-up body
        body = ai_service.generate_followup_email(
            original_subject=request.original_subject,
            job_title=request.job_title,
            company_name=request.company_name,
            followup_count=request.followup_count,
            user_name=request.user_name,
            days_since_sent=request.days_since_sent
        )
        
        # Generate subject
        subject = f"Re: {request.original_subject}"
        
        return FollowUpResponse(
            subject=subject,
            body=body,
            followup_count=request.followup_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-ai")
async def test_ai_connection():
    """Test if AI service is properly configured and working."""
    try:
        ai_service = AIService()
        
        if not ai_service.api_key:
            return {
                "status": "error",
                "message": "GROQ_API_KEY not configured",
                "configured": False
            }
        
        # Test with a simple request
        test_response = ai_service._call_groq_api(
            messages=[
                {
                    "role": "user",
                    "content": "Reply with just the word 'working' if you can read this."
                }
            ],
            temperature=0.1
        )
        
        if test_response:
            return {
                "status": "success",
                "message": "AI service is working correctly",
                "configured": True,
                "model": ai_service.model,
                "test_response": test_response[:100]
            }
        else:
            return {
                "status": "error",
                "message": "AI service configured but API call failed",
                "configured": True
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error testing AI service: {str(e)}",
            "configured": False
        }
