"""
Database models package.
Import all models here to ensure they are registered with SQLAlchemy.
"""

from app.models.user import User
from app.models.project import Project
from app.models.job import Job
from app.models.application import Application
from app.models.skill import Skill
from app.models.education import Education
from app.models.experience import Experience

# Export all models
__all__ = ["User", "Project", "Job", "Application", "Skill", "Education", "Experience"]