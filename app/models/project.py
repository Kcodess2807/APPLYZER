"""Project model — GitHub-synced, LLM-enriched. Not user-managed."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    profile_id = Column(String(50), ForeignKey("profiles.id"), nullable=False, index=True)

    # ── Raw GitHub data ────────────────────────────────────────────────────────
    github_repo_name = Column(String(255), nullable=False)
    github_repo_url = Column(String(500), nullable=False)
    primary_language = Column(String(100), nullable=True)
    github_topics = Column(ARRAY(String), nullable=False, default=list)
    github_stars = Column(Integer, nullable=True, default=0)
    github_updated_at = Column(DateTime(timezone=True), nullable=True)

    # ── LLM-enriched resume data ───────────────────────────────────────────────
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tech_stack = Column(ARRAY(String), nullable=False, default=list)
    features = Column(ARRAY(String), nullable=False, default=list)
    resume_bullets = Column(ARRAY(String), nullable=False, default=list)
    category = Column(String(100), nullable=True)
    skills_demonstrated = Column(ARRAY(String), nullable=False, default=list)

    # ── Control fields ─────────────────────────────────────────────────────────
    is_featured = Column(Boolean, nullable=False, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    llm_processed_at = Column(DateTime(timezone=True), nullable=True)
    readme_raw = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    profile = relationship("Profile", back_populates="projects")

    def __repr__(self):
        return f"<Project(id={self.id}, repo={self.github_repo_name}, profile_id={self.profile_id})>"

    def to_dict(self) -> dict:
        """Serialise for use in resume generation, matching, and API responses."""
        return {
            "id": str(self.id),
            "profile_id": str(self.profile_id),
            "github_repo_name": self.github_repo_name,
            "github_repo_url": self.github_repo_url,
            "title": self.title or self.github_repo_name,
            "description": self.description or "",
            "tech_stack": self.tech_stack or [],
            # Aliases used by matchers and resume generator
            "technologies": self.tech_stack or [],
            "achievements": self.resume_bullets or [],
            "features": self.features or [],
            "resume_bullets": self.resume_bullets or [],
            "category": self.category,
            "skills_demonstrated": self.skills_demonstrated or [],
            "project_url": self.github_repo_url,
            "is_featured": self.is_featured,
            "primary_language": self.primary_language,
            "github_stars": self.github_stars or 0,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "llm_processed_at": self.llm_processed_at.isoformat() if self.llm_processed_at else None,
        }
