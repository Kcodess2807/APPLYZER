"""
Pydantic schemas for Job model validation.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class JobBase(BaseModel):
    """Base job schema with common fields."""
    title: str
    company: str
    description: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    requirements: List[str] = []
    application_email: Optional[str] = None
    source: str
    external_id: Optional[str] = None
    posted_date: Optional[datetime] = None


class JobCreate(JobBase):
    """Schema for creating a new job."""
    pass


class JobUpdate(BaseModel):
    """Schema for updating job information."""
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    requirements: Optional[List[str]] = None
    application_email: Optional[str] = None


class JobResponse(JobBase):
    """Schema for job response data."""
    id: uuid.UUID
    fetched_at: datetime
    
    class Config:
        from_attributes = True


class JobFilter(BaseModel):
    """Schema for job filtering parameters."""
    keywords: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    limit: int = 20
    offset: int = 0