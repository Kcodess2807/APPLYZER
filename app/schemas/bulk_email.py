"""Schemas for bulk email operations."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime


class BulkEmailRequest(BaseModel):
    """Request schema for bulk email sending."""
    recipients: List[EmailStr]
    subject: str
    body: str
    company_name: Optional[str] = None
    job_role: Optional[str] = None


class EmailTrackingResponse(BaseModel):
    """Response schema for email tracking."""
    email: str
    subject: str
    thread_id: str
    status: str
    sent_at: str
    message_id: str


class BulkEmailResponse(BaseModel):
    """Response schema for bulk email operation."""
    success: bool
    total_sent: int
    failed: int
    results: List[EmailTrackingResponse]
    errors: Optional[List[dict]] = None


