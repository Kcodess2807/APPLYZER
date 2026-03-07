"""
Pydantic schemas for User model validation.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    professional_summary: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    professional_summary: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response data."""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserWithProjects(UserResponse):
    """User response with related projects."""
    projects: List["ProjectResponse"] = []