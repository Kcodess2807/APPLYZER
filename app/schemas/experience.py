"""Pydantic schemas for Experience model validation."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class ExperienceBase(BaseModel):
    """Base experience schema."""
    role: str
    company: str
    location: str
    duration: str
    achievements: List[str]
    display_order: int = 0


class ExperienceCreate(ExperienceBase):
    """Schema for creating a new experience entry."""
    pass


class ExperienceUpdate(BaseModel):
    """Schema for updating experience information."""
    role: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    duration: Optional[str] = None
    achievements: Optional[List[str]] = None
    display_order: Optional[int] = None


class ExperienceResponse(ExperienceBase):
    """Schema for experience response data."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
