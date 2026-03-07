"""Skill model for user profile management."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Skill(Base):
    __tablename__ = "skills"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Skill information
    category = Column(String(100), nullable=False)  # e.g., "Technical Skills", "Soft Skills"
    items = Column(ARRAY(String), nullable=False, default=[])  # List of skills in this category
    
    # Display order
    display_order = Column(Integer, nullable=True, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="skills")
    
    def __repr__(self):
        return f"<Skill(id={self.id}, category={self.category}, user_id={self.user_id})>"
