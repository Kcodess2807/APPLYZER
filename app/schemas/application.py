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
    profile_id: str
    reply_received: bool = False
    followup_count: int = 0
    created_at: datetime
    sent_at: Optional[datetime] = None
    email_sent_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    follow_up_scheduled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationWithDetails(ApplicationResponse):
    """Application response with job details."""
    job: "JobResponse"


class BulkApplyRequest(BaseModel):
    """Request schema for applying to multiple stored jobs at once."""
    profile_id: str
    job_ids: List[str]
    email_tone: str = "professional"
    send_gap_minutes: int = 7  # Minutes between emails to avoid spam filters


class QuickJobTarget(BaseModel):
    """A single job target provided inline (no pre-seeded DB record needed)."""
    title: str
    company: str
    description: str
    hr_email: str
    location: Optional[str] = "Remote"


class QuickApplyRequest(BaseModel):
    """Apply to multiple jobs by providing JDs directly — no pre-seeded job IDs needed."""
    user_id: str
    jobs: List[QuickJobTarget]
    send_gap_minutes: int = 7


class GeneratedApplicationInfo(BaseModel):
    """Per-job result from Phase 1 document generation."""
    application_id: Optional[str] = None
    job_id: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    hr_email: Optional[str] = None
    success: bool
    selected_projects: Optional[List[str]] = None
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    output_dir: Optional[str] = None
    email_subject: Optional[str] = None
    email_body_preview: Optional[str] = None  # First 500 chars for review
    cover_letter_preview: Optional[str] = None  # First 500 chars for review
    error: Optional[str] = None


class BulkApplyResponse(BaseModel):
    """Response returned immediately after Phase 1 (generation) completes.
    Emails are NOT sent yet — call POST /batches/{batch_id}/approve to send.
    """
    batch_id: str
    status: str
    total_jobs: int
    docs_generated: int
    send_gap_minutes: int
    generated: List[GeneratedApplicationInfo]
    message: str
    review_url: Optional[str] = None  # Convenience link for human review


class BatchApplicationPreview(BaseModel):
    """Full preview of one application inside a batch for human review."""
    application_id: str
    job_id: str
    job_title: str
    company: str
    hr_email: Optional[str]
    status: str
    email_subject: Optional[str]
    email_body: Optional[str]
    cover_letter_preview: Optional[str]
    resume_path: Optional[str]
    cover_letter_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BatchReviewResponse(BaseModel):
    """Full batch preview returned for human review."""
    batch_id: str
    total: int
    pending_approval: int
    applications: List[BatchApplicationPreview]


class BatchApproveRequest(BaseModel):
    """Optional per-application overrides when approving."""
    application_ids: Optional[List[str]] = None  # None = approve all in batch
    send_gap_minutes: int = 7


class BatchRejectRequest(BaseModel):
    application_ids: Optional[List[str]] = None  # None = reject all in batch
    reason: Optional[str] = None