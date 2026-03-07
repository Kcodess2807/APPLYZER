"""Experience model for user work history."""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class Experience(Base):
    __tablename__ = "experiences"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Experience information
    role = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    duration = Column(String(100), nullable=False)  # e.g., "Jan 2020 - Dec 2022"
    
    # Achievements and responsibilities
    achievements = Column(ARRAY(String), nullable=False, default=[])
    
    # Display order
    display_order = Column(Integer, nullable=True, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="experiences")
    
    def __repr__(self):
        return f"<Experience(id={self.id}, role={self.role}, company={self.company})>"
