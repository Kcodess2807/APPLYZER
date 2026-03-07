"""
Resume-related Pydantic models and schemas.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class EducationItem(BaseModel):
    """Education item model."""
    degree: str
    institution: str
    year: str
    coursework: Optional[str] = None
    gpa: Optional[str] = None


class SkillCategory(BaseModel):
    """Skill category model."""
    category: str
    items: List[str]


class ExperienceItem(BaseModel):
    """Experience item model."""
    role: str
    company: str
    duration: str
    location: str
    achievements: List[str]


class ProjectItem(BaseModel):
    """Project item model."""
    title: str
    description: str
    technologies: Optional[List[str]] = None
    url: Optional[str] = None


class ResumeGenerationRequest(BaseModel):
    """Request model for resume generation."""
    
    # Personal Information
    name: str
    phone: str
    location: str
    email: str
    linkedin_url: Optional[str] = None
    linkedin_display: Optional[str] = None
    website_url: Optional[str] = None
    website_display: Optional[str] = None
    
    # Professional Information
    experience_years: Optional[str] = "2+"
    primary_skills: Optional[List[str]] = ["Software Development"]
    
    # Resume Sections
    education: Optional[List[EducationItem]] = []
    skills: Optional[List[SkillCategory]] = []
    experience: Optional[List[ExperienceItem]] = []
    projects: Optional[List[ProjectItem]] = []
    extra_curricular: Optional[List[str]] = []
    leadership: Optional[List[str]] = []
    
    # Customization
    job_id: Optional[str] = None
    selected_project_ids: Optional[List[str]] = None


class BulkResumeRequest(BaseModel):
    """Request model for bulk resume generation."""
    job_ids: List[str]
    user_profile: ResumeGenerationRequest


class ResumeResponse(BaseModel):
    """Response model for resume generation."""
    success: bool
    resume_id: str
    job_id: Optional[str] = None
    download_url: str
    generation_method: str
    created_at: str
    user_name: str
    job_title: Optional[str] = None
    message: str


class BulkResumeResponse(BaseModel):
    """Response model for bulk resume generation."""
    success: bool
    total_jobs: int
    successful_generations: int
    failed_generations: int
    resumes: List[ResumeResponse]
    errors: List[Dict[str, str]]