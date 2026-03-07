"""
Pydantic schemas for Project model validation.
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import uuid


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    title: str
    description: str
    project_type: Optional[str] = None
    technologies: List[str] = []
    achievements: List[str] = []
    skills_demonstrated: List[str] = []
    keywords: List[str] = []  # Searchable keywords for better matching
    project_url: Optional[str] = None
    
    
    @validator('technologies', 'achievements')
    def validate_arrays_not_empty(cls, v):
        if not v:
            return []
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating project information."""
    title: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    technologies: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    skills_demonstrated: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    project_url: Optional[str] = None
    


class ProjectResponse(ProjectBase):
    """Schema for project response data."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True