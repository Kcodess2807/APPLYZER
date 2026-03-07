"""Profile model — single table combining user identity, skills, education, and experience."""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)
    professional_summary = Column(Text, nullable=True)
    experience_years = Column(String(20), nullable=True)

    # Structured profile data stored as JSONB — always read/written as a whole
    # skills:    [{category: str, items: [str]}]
    # education: [{degree, institution, year, coursework}]
    # experience:[{role, company, location, duration, achievements: [str]}]
    skills = Column(JSONB, nullable=False, default=list)
    education = Column(JSONB, nullable=False, default=list)
    experience = Column(JSONB, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Profile(id={self.id}, email={self.email}, name={self.full_name})>"
