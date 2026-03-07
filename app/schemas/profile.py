"""Pydantic schemas for user profile aggregation."""
from pydantic import BaseModel
from typing import List

from app.schemas.user import UserResponse
from app.schemas.skill import SkillResponse
from app.schemas.education import EducationResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.project import ProjectResponse


class CompleteProfileResponse(BaseModel):
    """Complete user profile with all related data."""
    user: UserResponse
    skills: List[SkillResponse]
    education: List[EducationResponse]
    experiences: List[ExperienceResponse]
    projects: List[ProjectResponse]
