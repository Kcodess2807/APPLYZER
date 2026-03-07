"""Projects endpoints — GitHub sync and feature toggle."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from loguru import logger

from app.database.base import get_db
from app.services.project_service import ProjectService
from app.schemas.project import ProjectResponse, ProjectFeatureToggle, SyncProjectsResponse

router = APIRouter()


@router.post("/sync", response_model=SyncProjectsResponse)
async def sync_github_projects(
    profile_id: str = Query(..., description="Profile ID"),
    github_username: str = Query(..., description="GitHub username"),
    db: Session = Depends(get_db),
):
    """Fetch all public GitHub repos, enrich with LLM, and upsert to DB."""
    try:
        return ProjectService(db).sync_projects(profile_id, github_username)
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    profile_id: str = Query(..., description="Profile ID"),
    featured_only: bool = Query(False, description="Return only featured projects"),
    db: Session = Depends(get_db),
):
    """List synced projects for a profile."""
    return ProjectService(db).get_user_projects(profile_id, featured_only=featured_only)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    profile_id: str = Query(..., description="Profile ID"),
    db: Session = Depends(get_db),
):
    """Get a single project by ID."""
    project = ProjectService(db).get_project_by_id(project_id, profile_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}/featured", response_model=ProjectResponse)
async def toggle_featured(
    project_id: str,
    body: ProjectFeatureToggle,
    profile_id: str = Query(..., description="Profile ID"),
    db: Session = Depends(get_db),
):
    """Show or hide a project on generated resumes."""
    project = ProjectService(db).toggle_featured(project_id, profile_id, body.is_featured)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
