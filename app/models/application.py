"""Application model — tracks every sent job application."""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign keys
    profile_id = Column(String(50), ForeignKey("profiles.id"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)

    # Batch processing tracking
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Generated content paths
    resume_path = Column(String(255), nullable=True)
    cover_letter_path = Column(String(255), nullable=True)
    cover_letter = Column(Text, nullable=True)

    # Email content
    email_subject = Column(String(255), nullable=True)
    email_body = Column(Text, nullable=True)

    # Gmail tracking
    gmail_message_id = Column(String(255), nullable=True, index=True)
    gmail_thread_id = Column(String(255), nullable=True, index=True)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Reply tracking
    reply_received = Column(Boolean, nullable=False, default=False)
    reply_received_at = Column(DateTime(timezone=True), nullable=True)

    # Follow-up tracking
    followup_count = Column(Integer, nullable=False, default=0)
    last_followup_at = Column(DateTime(timezone=True), nullable=True)

    # Google Sheets tracking
    sheets_row_id = Column(String(50), nullable=True)

    # Status: pending | docs_ready | sent | replied | no_response | follow_up_sent | send_failed | rejected
    status = Column(String(50), nullable=False, default="pending", index=True)

    # Human-in-the-loop approval tracking
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    response_received_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_scheduled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="applications")
    job = relationship("Job", back_populates="applications")

    def __repr__(self):
        return f"<Application(id={self.id}, profile_id={self.profile_id}, job_id={self.job_id}, status={self.status})>"