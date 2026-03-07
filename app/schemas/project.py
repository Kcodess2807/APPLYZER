"""Pydantic schemas for Project — GitHub-synced, LLM-enriched."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class ProjectResponse(BaseModel):
    """Full project response from DB."""
    id: uuid.UUID
    profile_id: str
    github_repo_name: str
    github_repo_url: str
    primary_language: Optional[str] = None
    github_topics: List[str] = []
    github_stars: Optional[int] = 0
    github_updated_at: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []
    features: List[str] = []
    resume_bullets: List[str] = []
    category: Optional[str] = None
    skills_demonstrated: List[str] = []
    is_featured: bool = True
    last_synced_at: Optional[datetime] = None
    llm_processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectFeatureToggle(BaseModel):
    """Toggle whether a project appears on resumes."""
    is_featured: bool


class SyncProjectsResponse(BaseModel):
    """Response from a GitHub sync operation."""
    synced: int
    skipped: int
    failed: int
    total_repos: int
    message: str