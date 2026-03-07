"""Profile management endpoints (create, read, update, delete)."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from loguru import logger

from app.database.base import get_db
from app.services.profile_service import ProfileService
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter()


@router.post("/", response_model=ProfileResponse, status_code=201)
async def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
):
    """Create a new profile."""
    try:
        return ProfileService(db).create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProfileResponse])
async def list_profiles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all profiles with pagination."""
    return ProfileService(db).get_all(limit=limit, offset=offset)


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: Session = Depends(get_db),
):
    """Get a profile by ID."""
    profile = ProfileService(db).get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    data: ProfileUpdate,
    db: Session = Depends(get_db),
):
    """Update a profile."""
    profile = ProfileService(db).update(profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    db: Session = Depends(get_db),
):
    """Delete a profile and all associated data."""
    deleted = ProfileService(db).delete(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"success": True, "message": f"Profile {profile_id} deleted"}
