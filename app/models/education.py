"""Education model for user academic background."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Education(Base):
    __tablename__ = "education"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Education information
    degree = Column(String(255), nullable=False)  # e.g., "Bachelor of Computer Science"
    institution = Column(String(255), nullable=False)
    year = Column(String(50), nullable=False)  # e.g., "2014 - 2018" or "Expected 2025"
    coursework = Column(String(500), nullable=True)  # Relevant coursework
    
    # Display order
    display_order = Column(Integer, nullable=True, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="education")
    
    def __repr__(self):
        return f"<Education(id={self.id}, degree={self.degree}, institution={self.institution})>"
