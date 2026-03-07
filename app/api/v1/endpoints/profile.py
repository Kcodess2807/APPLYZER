"""User profile management - comprehensive endpoint for all user data."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from loguru import logger

from app.database.base import get_db
from app.services.profile_service import ProfileService
from app.schemas.profile import CompleteProfileResponse
from app.schemas.user import UserResponse
from app.schemas.skill import SkillResponse
from app.schemas.education import EducationResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.project import ProjectResponse

router = APIRouter()


@router.get("/{user_id}", response_model=CompleteProfileResponse)
async def get_complete_profile(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Get complete user profile including:
    - Basic user information
    - Skills
    - Education
    - Work experience
    - Projects
    """
    try:
        logger.info(f"Fetching complete profile for user {user_id}")

        profile = ProfileService(db).get_complete_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        return CompleteProfileResponse(
            user=UserResponse.from_orm(profile["user"]),
            skills=[SkillResponse.from_orm(s) for s in profile["skills"]],
            education=[EducationResponse.from_orm(e) for e in profile["education"]],
            experiences=[ExperienceResponse.from_orm(exp) for exp in profile["experiences"]],
            projects=[ProjectResponse.from_orm(p) for p in profile["projects"]],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching complete profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.get("/{user_id}/summary")
async def get_profile_summary(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get a summary of user profile completeness."""
    try:
        svc = ProfileService(db)

        user = svc.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        skills_count = len(svc.get_skills(user_id))
        education_count = len(svc.get_education(user_id))
        experience_count = len(svc.get_experiences(user_id))
        project_count = len(svc.get_projects(user_id))

        completeness_score = 0
        if user.full_name:
            completeness_score += 20
        if user.email:
            completeness_score += 20
        if skills_count > 0:
            completeness_score += 20
        if education_count > 0:
            completeness_score += 20
        if experience_count > 0 or project_count > 0:
            completeness_score += 20

        return {
            "user_id": str(user_id),
            "full_name": user.full_name,
            "email": user.email,
            "completeness_score": completeness_score,
            "counts": {
                "skills": skills_count,
                "education": education_count,
                "experiences": experience_count,
                "projects": project_count,
            },
            "missing_sections": [
                section
                for section, count in [
                    ("skills", skills_count),
                    ("education", education_count),
                    ("experience", experience_count),
                    ("projects", project_count),
                ]
                if count == 0
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")
