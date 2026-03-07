"""
Database models package.
Import all models here to ensure they are registered with SQLAlchemy.
"""

from app.models.profile import Profile
from app.models.project import Project
from app.models.job import Job
from app.models.application import Application

__all__ = ["Profile", "Project", "Job", "Application"]