"""Pydantic schemas for Profile — covers identity, skills, education, and experience."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


# ── Inline schemas for JSONB fields ───────────────────────────────────────────

class SkillCategory(BaseModel):
    category: str
    items: List[str]


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: str
    coursework: Optional[str] = None


class ExperienceItem(BaseModel):
    role: str
    company: str
    location: str
    duration: str
    achievements: List[str] = []


# ── Profile schemas ────────────────────────────────────────────────────────────

class ProfileBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    github_username: Optional[str] = None
    professional_summary: Optional[str] = None
    experience_years: Optional[str] = None
    skills: List[SkillCategory] = []
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    github_username: Optional[str] = None
    professional_summary: Optional[str] = None
    experience_years: Optional[str] = None
    skills: Optional[List[SkillCategory]] = None
    education: Optional[List[EducationItem]] = None
    experience: Optional[List[ExperienceItem]] = None


class ProfileResponse(ProfileBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileSummary(BaseModel):
    """Lightweight profile completeness summary."""
    profile_id: str
    full_name: str
    email: str
    github_username: Optional[str]
    completeness_score: int
    has_skills: bool
    has_education: bool
    has_experience: bool
    has_projects: bool
    projects_synced: int
