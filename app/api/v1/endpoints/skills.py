"""Skills management endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
import uuid

from app.database.base import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate, SkillResponse

router = APIRouter()


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(
    skill_data: SkillCreate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new skill category for a user."""
    try:
        logger.info(f"Creating skill category '{skill_data.category}' for user {user_id}")
        
        new_skill = Skill(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            category=skill_data.category,
            items=skill_data.items,
            display_order=skill_data.display_order
        )
        
        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)
        
        logger.info(f"✅ Skill category created: {new_skill.id}")
        return new_skill
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating skill: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create skill: {str(e)}")


@router.get("/", response_model=List[SkillResponse])
async def get_skills(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all skills for a user."""
    try:
        logger.info(f"Fetching skills for user {user_id}")
        
        skills = db.query(Skill).filter(
            Skill.user_id == uuid.UUID(user_id)
        ).order_by(Skill.display_order).all()
        
        return skills
        
    except Exception as e:
        logger.error(f"Error fetching skills: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch skills: {str(e)}")


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific skill category by ID."""
    try:
        skill = db.query(Skill).filter(
            Skill.id == uuid.UUID(skill_id),
            Skill.user_id == uuid.UUID(user_id)
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        return skill
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skill: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch skill: {str(e)}")


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update a skill category."""
    try:
        skill = db.query(Skill).filter(
            Skill.id == uuid.UUID(skill_id),
            Skill.user_id == uuid.UUID(user_id)
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        update_dict = skill_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(skill, key, value)
        
        db.commit()
        db.refresh(skill)
        
        logger.info(f"✅ Skill updated: {skill_id}")
        return skill
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating skill: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update skill: {str(e)}")


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a skill category."""
    try:
        skill = db.query(Skill).filter(
            Skill.id == uuid.UUID(skill_id),
            Skill.user_id == uuid.UUID(user_id)
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        db.delete(skill)
        db.commit()
        
        logger.info(f"✅ Skill deleted: {skill_id}")
        return {"success": True, "message": "Skill deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting skill: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete skill: {str(e)}")
