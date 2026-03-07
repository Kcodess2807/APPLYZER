"""Service layer for Profile CRUD operations."""
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileService:
    """All profile database operations — single-row read/write."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, profile_id: str) -> Optional[Profile]:
        """Fetch a profile by ID. Returns None if not found."""
        return self.db.query(Profile).filter(Profile.id == str(profile_id)).first()

    def get_by_email(self, email: str) -> Optional[Profile]:
        """Fetch a profile by email. Returns None if not found."""
        return self.db.query(Profile).filter(Profile.email == email).first()

    def get_all(self, limit: int = 50, offset: int = 0) -> List[Profile]:
        """List all profiles with pagination."""
        return self.db.query(Profile).offset(offset).limit(limit).all()

    def create(self, data: ProfileCreate) -> Profile:
        """Create and persist a new profile. Raises ValueError if email already exists."""
        if self.get_by_email(data.email):
            raise ValueError(f"Profile with email {data.email} already exists")

        profile = Profile(
            id=str(uuid.uuid4()),
            email=data.email,
            full_name=data.full_name,
            phone=data.phone,
            location=data.location,
            linkedin_url=data.linkedin_url,
            github_url=data.github_url,
            github_username=data.github_username,
            professional_summary=data.professional_summary,
            experience_years=data.experience_years,
            skills=[s.dict() for s in data.skills],
            education=[e.dict() for e in data.education],
            experience=[exp.dict() for exp in data.experience],
        )

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"Profile created: {profile.id}")
        return profile

    def update(self, profile_id: str, data: ProfileUpdate) -> Optional[Profile]:
        """Update a profile. Returns None if not found."""
        profile = self.get_by_id(profile_id)
        if not profile:
            return None

        for key, value in data.dict(exclude_unset=True).items():
            if key in ("skills", "education", "experience") and value is not None:
                setattr(profile, key, [item.dict() for item in value])
            else:
                setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"Profile updated: {profile_id}")
        return profile

    def delete(self, profile_id: str) -> bool:
        """Delete a profile. Returns False if not found."""
        profile = self.get_by_id(profile_id)
        if not profile:
            return False

        self.db.delete(profile)
        self.db.commit()
        logger.info(f"Profile deleted: {profile_id}")
        return True

    def get_profile_as_dict(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Return profile data as plain dicts ready for resume/email generation.
        Projects are NOT included here — callers inject them per-job.
        """
        profile = self.get_by_id(profile_id)
        if not profile:
            return None

        skills = profile.skills or []
        return {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location or "City, State",
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "github_username": profile.github_username,
            "professional_summary": profile.professional_summary,
            "experience_years": profile.experience_years or "2+",
            "primary_skills": skills[0]["items"][:3] if skills else [],
            "skills": skills,
            "education": profile.education or [],
            "experience": profile.experience or [],
            "extra_curricular": [],
            "leadership": [],
        }
