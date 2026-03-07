"""Pydantic schemas for Skill model validation."""
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid


class SkillBase(BaseModel):
    """Base skill schema."""
    category: str
    items: List[str]
    display_order: int = 0


class SkillCreate(SkillBase):
    """Schema for creating a new skill category."""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating skill information."""
    category: str = None
    items: List[str] = None
    display_order: int = None


class SkillResponse(SkillBase):
    """Schema for skill response data."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
