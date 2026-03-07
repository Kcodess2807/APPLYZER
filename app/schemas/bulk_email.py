"""Pydantic schemas for bulk email operations."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class BulkEmailRequest(BaseModel):
    """Request for sending bulk emails to multiple recipients."""

    recipients: List[EmailStr] = Field(
        ..., description="List of recipient email addresses"
    )
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body (HTML supported)")


class EmailResult(BaseModel):
    """Result for a single email send operation."""

    email: str
    subject: str
    thread_id: Optional[str] = None
    status: str
    sent_at: str = ""
    message_id: Optional[str] = None


class EmailError(BaseModel):
    """Error information for a failed email send."""

    email: str
    error: str


class BulkEmailResponse(BaseModel):
    """Response for bulk email send operation."""

    success: bool
    total_sent: int
    failed: int
    results: List[EmailResult] = Field(default_factory=list)
    errors: Optional[List[EmailError]] = None
