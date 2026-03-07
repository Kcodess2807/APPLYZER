"""Job model — stores fetched job listings."""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Job information
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True, index=True)
    salary_range = Column(String(100), nullable=True)

    # Structured requirements + parsed tech stack for TF-IDF matching
    requirements = Column(ARRAY(String), nullable=False, default=list)
    technologies = Column(ARRAY(String), nullable=False, default=list)

    # Contact and source
    application_email = Column(String(255), nullable=True)
    job_url = Column(String(500), nullable=True)
    source = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)

    # Timestamps
    posted_date = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, company={self.company})>"