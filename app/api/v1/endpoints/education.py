"""Education management endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
import uuid

from app.database.base import get_db
from app.models.education import Education
from app.schemas.education import EducationCreate, EducationUpdate, EducationResponse

router = APIRouter()


@router.post("/", response_model=EducationResponse, status_code=201)
async def create_education(
    education_data: EducationCreate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new education entry for a user."""
    try:
        logger.info(f"Creating education entry for user {user_id}")
        
        new_education = Education(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            degree=education_data.degree,
            institution=education_data.institution,
            year=education_data.year,
            coursework=education_data.coursework,
            display_order=education_data.display_order
        )
        
        db.add(new_education)
        db.commit()
        db.refresh(new_education)
        
        logger.info(f"✅ Education entry created: {new_education.id}")
        return new_education
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating education: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create education: {str(e)}")


@router.get("/", response_model=List[EducationResponse])
async def get_education(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all education entries for a user."""
    try:
        logger.info(f"Fetching education for user {user_id}")
        
        education = db.query(Education).filter(
            Education.user_id == uuid.UUID(user_id)
        ).order_by(Education.display_order).all()
        
        return education
        
    except Exception as e:
        logger.error(f"Error fetching education: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch education: {str(e)}")


@router.get("/{education_id}", response_model=EducationResponse)
async def get_education_by_id(
    education_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific education entry by ID."""
    try:
        education = db.query(Education).filter(
            Education.id == uuid.UUID(education_id),
            Education.user_id == uuid.UUID(user_id)
        ).first()
        
        if not education:
            raise HTTPException(status_code=404, detail="Education entry not found")
        
        return education
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching education: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch education: {str(e)}")


@router.put("/{education_id}", response_model=EducationResponse)
async def update_education(
    education_id: str,
    education_data: EducationUpdate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update an education entry."""
    try:
        education = db.query(Education).filter(
            Education.id == uuid.UUID(education_id),
            Education.user_id == uuid.UUID(user_id)
        ).first()
        
        if not education:
            raise HTTPException(status_code=404, detail="Education entry not found")
        
        update_dict = education_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(education, key, value)
        
        db.commit()
        db.refresh(education)
        
        logger.info(f"✅ Education updated: {education_id}")
        return education
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating education: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update education: {str(e)}")


@router.delete("/{education_id}")
async def delete_education(
    education_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete an education entry."""
    try:
        education = db.query(Education).filter(
            Education.id == uuid.UUID(education_id),
            Education.user_id == uuid.UUID(user_id)
        ).first()
        
        if not education:
            raise HTTPException(status_code=404, detail="Education entry not found")
        
        db.delete(education)
        db.commit()
        
        logger.info(f"✅ Education deleted: {education_id}")
        return {"success": True, "message": "Education entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting education: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete education: {str(e)}")
