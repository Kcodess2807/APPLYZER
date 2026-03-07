"""Profile summary and completeness endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from loguru import logger

from app.database.base import get_db
from app.services.profile_service import ProfileService
from app.services.project_service import ProjectService
from app.schemas.profile import ProfileSummary

router = APIRouter()


@router.get("/{profile_id}/summary", response_model=ProfileSummary)
async def get_profile_summary(
    profile_id: str,
    db: Session = Depends(get_db),
):
    """Get profile completeness summary."""
    try:
        profile = ProfileService(db).get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        projects_synced = len(ProjectService(db).get_user_projects(profile_id))

        score = 0
        if profile.full_name:
            score += 20
        if profile.email:
            score += 20
        if profile.skills:
            score += 20
        if profile.education:
            score += 20
        if profile.experience or projects_synced:
            score += 20

        return ProfileSummary(
            profile_id=str(profile.id),
            full_name=profile.full_name,
            email=profile.email,
            github_username=profile.github_username,
            completeness_score=score,
            has_skills=bool(profile.skills),
            has_education=bool(profile.education),
            has_experience=bool(profile.experience),
            has_projects=projects_synced > 0,
            projects_synced=projects_synced,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
