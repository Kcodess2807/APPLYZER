"""
Pydantic schemas for Application model validation.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class ApplicationBase(BaseModel):
    """Base application schema with common fields."""
    job_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    resume_path: Optional[str] = None
    cover_letter: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    status: str = "pending"


class ApplicationCreate(ApplicationBase):
    """Schema for creating a new application."""
    pass


class ApplicationUpdate(BaseModel):
    """Schema for updating application information."""
    status: Optional[str] = None
    resume_path: Optional[str] = None
    cover_letter: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    sent_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    follow_up_scheduled_at: Optional[datetime] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response data."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    sent_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    follow_up_scheduled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ApplicationWithDetails(ApplicationResponse):
    """Application response with job and user details."""
    job: "JobResponse"
    user: "UserResponse"


class BulkApplyRequest(BaseModel):
    """Request schema for applying to multiple stored jobs at once."""
    user_id: str
    job_ids: List[str]
    email_tone: str = "professional"
    send_gap_minutes: int = 7  # Minutes between emails to avoid spam filters


class GeneratedApplicationInfo(BaseModel):
    """Per-job result from Phase 1 document generation."""
    job_id: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    success: bool
    selected_projects: Optional[List[str]] = None
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    output_dir: Optional[str] = None
    error: Optional[str] = None


class BulkApplyResponse(BaseModel):
    """Response returned immediately after Phase 1 (generation) completes."""
    batch_id: str
    status: str
    total_jobs: int
    docs_generated: int
    send_gap_minutes: int
    generated: List[GeneratedApplicationInfo]
    message: str