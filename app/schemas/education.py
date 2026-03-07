"""Pydantic schemas for Education model validation."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class EducationBase(BaseModel):
    """Base education schema."""
    degree: str
    institution: str
    year: str
    coursework: Optional[str] = None
    display_order: int = 0


class EducationCreate(EducationBase):
    """Schema for creating a new education entry."""
    pass


class EducationUpdate(BaseModel):
    """Schema for updating education information."""
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    coursework: Optional[str] = None
    display_order: Optional[int] = None


class EducationResponse(EducationBase):
    """Schema for education response data."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
