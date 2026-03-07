"""Pydantic schemas for resume generation endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.profile import EducationItem, ExperienceItem, SkillCategory


class ProjectItem(BaseModel):
    """Project payload used for resume generation."""

    title: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class ResumeGenerationRequest(BaseModel):
    """Request for generating a single customized resume."""

    name: str
    email: EmailStr
    phone: str
    location: str

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    professional_summary: Optional[str] = None
    experience_years: Optional[str] = None

    primary_skills: List[str] = Field(default_factory=list)
    skills: List[SkillCategory] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)

    selected_project_ids: List[str] = Field(default_factory=list)
    job_id: Optional[str] = None


class BulkResumeRequest(ResumeGenerationRequest):
    """Request for generating resumes for multiple jobs."""

    job_ids: List[str] = Field(default_factory=list)
    max_projects_per_resume: int = Field(default=4, ge=1, le=10)


class ResumeResponse(BaseModel):
    """Response for single resume generation."""

    success: bool
    resume_id: str
    job_id: Optional[str] = None
    download_url: str
    template_url: Optional[str] = None
    generation_method: str
    file_paths: Dict[str, Optional[str]] = Field(default_factory=dict)
    created_at: str
    user_name: str
    job_title: str
    message: str


class BulkResumeResponse(BaseModel):
    """Response for bulk resume generation."""

    success: bool
    message: str
    user_id: str
    total_jobs: int
    resumes_generated: List[Dict[str, Any]] = Field(default_factory=list)
    failed_jobs: List[Dict[str, Any]] = Field(default_factory=list)
    processing_summary: Dict[str, Any] = Field(default_factory=dict)
    download_urls: List[Dict[str, Any]] = Field(default_factory=list)
