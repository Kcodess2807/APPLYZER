from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ProjectItem(BaseModel):
    title: str
    description: Optional[str] = ""
    technologies: Optional[List[str]] = []
    url: Optional[str] = None
    achievements: Optional[List[str]] = []


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: str
    coursework: Optional[str] = None
    gpa: Optional[str] = None


class SkillCategory(BaseModel):
    category: str
    items: List[str]


class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: str
    location: Optional[str] = ""
    achievements: Optional[List[str]] = []


class ResumeGenerationRequest(BaseModel):
    name: str
    phone: str
    location: str
    email: str
    linkedin_url: Optional[str] = None
    linkedin_display: Optional[str] = None
    website_url: Optional[str] = None
    website_display: Optional[str] = None
    experience_years: Optional[str] = "2+"
    primary_skills: Optional[List[str]] = []
    education: Optional[List[EducationItem]] = []
    skills: Optional[List[SkillCategory]] = []
    experience: Optional[List[ExperienceItem]] = []
    projects: Optional[List[ProjectItem]] = []
    selected_project_ids: Optional[List[str]] = None
    job_id: Optional[str] = None
    extra_curricular: Optional[List[str]] = []
    leadership: Optional[List[str]] = []


class BulkResumeRequest(BaseModel):
    job_ids: List[str]
    name: str
    phone: str
    location: str
    email: str
    linkedin_url: Optional[str] = None
    linkedin_display: Optional[str] = None
    website_url: Optional[str] = None
    website_display: Optional[str] = None
    experience_years: Optional[str] = "2+"
    primary_skills: Optional[List[str]] = []
    education: Optional[List[EducationItem]] = []
    skills: Optional[List[SkillCategory]] = []
    experience: Optional[List[ExperienceItem]] = []
    projects: Optional[List[ProjectItem]] = []
    max_projects_per_resume: int = 4


class ResumeResponse(BaseModel):
    success: bool
    resume_id: str
    job_id: Optional[str] = None
    download_url: str
    template_url: Optional[str] = None
    generation_method: str
    file_paths: Optional[Dict[str, Any]] = None
    created_at: str
    user_name: str
    job_title: str
    message: str


class BulkResumeResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    total_jobs: int
    resumes_generated: List[Dict[str, Any]]
    failed_jobs: List[Dict[str, Any]]
    processing_summary: Dict[str, Any]
    download_urls: List[Dict[str, Any]]
