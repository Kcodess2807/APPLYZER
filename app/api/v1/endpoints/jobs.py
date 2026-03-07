"""
Job management endpoints with RemoteOK integration.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger
import uuid

from app.database.base import get_db
from app.services.job_service import JobService
from app.schemas.job import JobResponse

router = APIRouter()


class JobFetchRequest(BaseModel):
    """Request model for job fetching."""
    keywords: Optional[List[str]] = None
    limit_per_source: int = 50


@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    keywords: Optional[str] = Query(None, description="Comma-separated job search keywords"),
    location: Optional[str] = Query(None, description="Job location filter"),
    company: Optional[str] = Query(None, description="Company name filter"),
    limit: int = Query(20, description="Number of jobs to return"),
    offset: int = Query(0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """Get jobs with filtering and pagination."""
    logger.info(f"Get jobs endpoint called with keywords: {keywords}, location: {location}")
    
    try:
        job_service = JobService(db)
        
        # Parse keywords
        keyword_list = None
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        
        # Search jobs
        jobs = job_service.search_jobs(
            keywords=keyword_list,
            location=location,
            company=company,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Found {len(jobs)} jobs matching criteria")
        return jobs
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to search jobs")


@router.post("/fetch")
async def fetch_jobs(
    request: JobFetchRequest = JobFetchRequest(),
    db: Session = Depends(get_db)
):
    """Trigger job fetching from external APIs."""
    logger.info(f"Fetch jobs endpoint called with keywords: {request.keywords}")
    
    try:
        job_service = JobService(db)
        
        # Fetch and store jobs
        results = await job_service.fetch_and_store_jobs(
            keywords=request.keywords,
            limit_per_source=request.limit_per_source
        )
        
        logger.info(f"Job fetch completed: {results['new_jobs']} new jobs")
        
        return {
            "success": True,
            "message": f"Fetched {results['total_fetched']} jobs, {results['new_jobs']} new, {results['updated_jobs']} updated",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@router.get("/statistics")
async def get_job_statistics(db: Session = Depends(get_db)):
    """Get job database statistics."""
    try:
        job_service = JobService(db)
        stats = job_service.get_job_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting job statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/sources")
async def get_job_sources():
    """Get information about available job sources."""
    try:
        from app.services.job_source_config import job_source_manager
        
        sources_info = job_source_manager.get_source_info()
        enabled_sources = job_source_manager.get_enabled_source_names()
        
        return {
            "success": True,
            "enabled_sources": enabled_sources,
            "available_sources": sources_info
        }
        
    except Exception as e:
        logger.error(f"Error getting job sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job sources")


@router.post("/sources/{source_id}/toggle")
async def toggle_job_source(source_id: str, enable: bool = True):
    """Enable or disable a job source."""
    try:
        from app.services.job_source_config import job_source_manager
        
        if enable:
            success = job_source_manager.enable_source(source_id)
            action = "enabled"
        else:
            success = job_source_manager.disable_source(source_id)
            action = "disabled"
        
        if success:
            return {
                "success": True,
                "message": f"Job source '{source_id}' {action} successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Job source '{source_id}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling job source: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle job source")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get job details by ID."""
    logger.info(f"Get job {job_id} endpoint called")
    
    try:
        job_service = JobService(db)
        job = job_service.get_job_by_id(str(job_id))
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")