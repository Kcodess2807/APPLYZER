"""Experience management endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
import uuid

from app.database.base import get_db
from app.models.experience import Experience
from app.schemas.experience import ExperienceCreate, ExperienceUpdate, ExperienceResponse

router = APIRouter()


@router.post("/", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    experience_data: ExperienceCreate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new work experience entry for a user."""
    try:
        logger.info(f"Creating experience entry for user {user_id}")
        
        new_experience = Experience(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            role=experience_data.role,
            company=experience_data.company,
            location=experience_data.location,
            duration=experience_data.duration,
            achievements=experience_data.achievements,
            display_order=experience_data.display_order
        )
        
        db.add(new_experience)
        db.commit()
        db.refresh(new_experience)
        
        logger.info(f"✅ Experience entry created: {new_experience.id}")
        return new_experience
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating experience: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create experience: {str(e)}")


@router.get("/", response_model=List[ExperienceResponse])
async def get_experiences(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all work experience entries for a user."""
    try:
        logger.info(f"Fetching experiences for user {user_id}")
        
        experiences = db.query(Experience).filter(
            Experience.user_id == uuid.UUID(user_id)
        ).order_by(Experience.display_order).all()
        
        return experiences
        
    except Exception as e:
        logger.error(f"Error fetching experiences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch experiences: {str(e)}")


@router.get("/{experience_id}", response_model=ExperienceResponse)
async def get_experience(
    experience_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific experience entry by ID."""
    try:
        experience = db.query(Experience).filter(
            Experience.id == uuid.UUID(experience_id),
            Experience.user_id == uuid.UUID(user_id)
        ).first()
        
        if not experience:
            raise HTTPException(status_code=404, detail="Experience entry not found")
        
        return experience
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching experience: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch experience: {str(e)}")


@router.put("/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: str,
    experience_data: ExperienceUpdate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update a work experience entry."""
    try:
        experience = db.query(Experience).filter(
            Experience.id == uuid.UUID(experience_id),
            Experience.user_id == uuid.UUID(user_id)
        ).first()
        
        if not experience:
            raise HTTPException(status_code=404, detail="Experience entry not found")
        
        update_dict = experience_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(experience, key, value)
        
        db.commit()
        db.refresh(experience)
        
        logger.info(f"✅ Experience updated: {experience_id}")
        return experience
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating experience: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update experience: {str(e)}")


@router.delete("/{experience_id}")
async def delete_experience(
    experience_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a work experience entry."""
    try:
        experience = db.query(Experience).filter(
            Experience.id == uuid.UUID(experience_id),
            Experience.user_id == uuid.UUID(user_id)
        ).first()
        
        if not experience:
            raise HTTPException(status_code=404, detail="Experience entry not found")
        
        db.delete(experience)
        db.commit()
        
        logger.info(f"✅ Experience deleted: {experience_id}")
        return {"success": True, "message": "Experience entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting experience: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete experience: {str(e)}")
