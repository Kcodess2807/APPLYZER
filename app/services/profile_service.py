"""Service layer for aggregating a user's complete profile data."""
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.user import User
from app.models.skill import Skill
from app.models.education import Education
from app.models.experience import Experience
from app.models.project import Project
from app.services.project_service import ProjectService


class ProfileService:
    """Centralizes all profile-level data fetching across the application."""

    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: str) -> Optional[User]:
        """Fetch a single user. Returns None if not found."""
        return self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()

    def get_skills(self, user_id: str):
        """Fetch skills ordered by display_order."""
        return (
            self.db.query(Skill)
            .filter(Skill.user_id == uuid.UUID(user_id))
            .order_by(Skill.display_order)
            .all()
        )

    def get_education(self, user_id: str):
        """Fetch education entries ordered by display_order."""
        return (
            self.db.query(Education)
            .filter(Education.user_id == uuid.UUID(user_id))
            .order_by(Education.display_order)
            .all()
        )

    def get_experiences(self, user_id: str):
        """Fetch experience entries ordered by display_order."""
        return (
            self.db.query(Experience)
            .filter(Experience.user_id == uuid.UUID(user_id))
            .order_by(Experience.display_order)
            .all()
        )

    def get_projects(self, user_id: str):
        """Fetch all projects for a user."""
        project_service = ProjectService(self.db)
        return project_service.get_user_projects(user_id)

    def get_complete_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Return all profile data aggregated in a single dict.

        Returns None if the user does not exist.
        """
        user = self.get_user(user_id)
        if not user:
            return None

        skills = self.get_skills(user_id)
        education = self.get_education(user_id)
        experiences = self.get_experiences(user_id)
        projects = self.get_projects(user_id)

        logger.info(f"Fetched complete profile for user {user_id}")

        return {
            "user": user,
            "skills": skills,
            "education": education,
            "experiences": experiences,
            "projects": projects,
        }

    def get_profile_as_dict(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Return the profile formatted as plain dicts, ready for resume/email generation.

        Returns None if the user does not exist.
        """
        user = self.get_user(user_id)
        if not user:
            return None

        skills = self.get_skills(user_id)
        education = self.get_education(user_id)
        experiences = self.get_experiences(user_id)
        projects = self.get_projects(user_id)

        skills_data = [{"category": s.category, "items": s.items} for s in skills]
        education_data = [
            {
                "degree": e.degree,
                "institution": e.institution,
                "year": e.year,
                "coursework": e.coursework,
            }
            for e in education
        ]
        experience_data = [
            {
                "role": exp.role,
                "company": exp.company,
                "location": exp.location,
                "duration": exp.duration,
                "achievements": exp.achievements,
            }
            for exp in experiences
        ]
        projects_data = [
            {
                "title": p.title,
                "description": p.description,
                "technologies": p.technologies or [],
                "achievements": p.achievements or [],
                "project_url": p.project_url,
            }
            for p in projects
        ]

        return {
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "location": getattr(user, "location", "City, State"),
            "linkedin_url": user.linkedin_url,
            "github_url": user.github_url,
            "website_url": getattr(user, "website_url", None),
            "experience_years": "5+",
            "primary_skills": skills_data[0]["items"][:3] if skills_data else ["Python", "JavaScript"],
            "skills": skills_data,
            "education": education_data,
            "experience": experience_data,
            "extra_curricular": [],
            "leadership": [],
            "projects": projects_data,
        }
