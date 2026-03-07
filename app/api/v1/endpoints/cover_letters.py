"""
Cover Letter API Endpoints

Provides REST API for cover letter generation:
- Individual generation for specific jobs
- Bulk generation for multiple jobs
- Download and retrieval endpoints
- ZIP download for bulk operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from loguru import logger
import uuid

from app.database.base import get_db
from app.services.cover_letter_generator import cover_letter_generator, CoverLetterGenerationError

router = APIRouter()


class CoverLetterGenerateRequest(BaseModel):
    user_id: uuid.UUID
    resume_summary: Optional[str] = None
    # User details for cover letter generation
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_location: Optional[str] = None
    experience_years: Optional[str] = "2+"
    primary_skills: Optional[List[str]] = ["Software Development"]
    selected_projects: Optional[List[Dict[str, Any]]] = []


class CoverLetterResponse(BaseModel):
    success: bool
    cover_letter_id: str
    content: str
    download_url: str
    generation_method: str
    message: str


class BulkCoverLetterRequest(BaseModel):
    """Request model for bulk cover letter generation."""
    user_id: uuid.UUID
    job_ids: List[uuid.UUID]
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_location: Optional[str] = None
    experience_years: Optional[str] = "2+"
    primary_skills: Optional[List[str]] = ["Software Development"]
    selected_projects: Optional[List[Dict[str, Any]]] = []


class BulkCoverLetterResponse(BaseModel):
    """Response model for bulk cover letter generation."""
    success: bool
    total_requested: int
    total_generated: int
    total_failed: int
    execution_time_seconds: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


@router.post("/{job_id}", response_model=CoverLetterResponse)
async def generateCoverLetter(
    job_id: uuid.UUID, 
    request: CoverLetterGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate cover letter for specific job ID."""
    logger.info(f"Generating cover letter for job {job_id} by user {request.user_id}")
    
    try:
        # Fetch job details from database
        job_data = await _get_job_from_database(str(job_id), db)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Prepare user data
        user_data = {
            "name": request.user_name or "User",
            "email": request.user_email or "user@example.com",
            "phone": request.user_phone or "+1(555) 123-4567",
            "location": request.user_location or "Location",
            "experience_years": request.experience_years,
            "primary_skills": request.primary_skills
        }
        
        # Generate cover letter using the service
        result = cover_letter_generator.generate_cover_letter(
            job_data=job_data,
            user_data=user_data,
            selected_projects=request.selected_projects
        )
        
        return CoverLetterResponse(
            success=True,
            cover_letter_id=result["cover_letter_id"],
            content=result["content"],
            download_url=f"/api/v1/cover-letters/{result['cover_letter_id']}/download",
            generation_method=result["generation_method"],
            message=f"Cover letter generated using {result['generation_method']}"
        )
        
    except CoverLetterGenerationError as e:
        logger.error(f"Cover letter generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate cover letter")


@router.get("/{cover_letter_id}")
async def getCoverLetter(cover_letter_id: str):
    """Fetch specific cover letter content."""
    logger.info(f"Getting cover letter {cover_letter_id}")
    
    try:
        file_path = cover_letter_generator.get_cover_letter_path(cover_letter_id)
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Cover letter not found")
        
        content = file_path.read_text(encoding='utf-8')
        
        return {
            "success": True,
            "cover_letter_id": cover_letter_id,
            "content": content,
            "download_url": f"/api/v1/cover-letters/{cover_letter_id}/download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cover letter {cover_letter_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cover letter")


@router.get("/{cover_letter_id}/download")
async def downloadCoverLetter(cover_letter_id: str):
    """Download specific cover letter file."""
    logger.info(f"Downloading cover letter {cover_letter_id}")
    
    try:
        file_path = cover_letter_generator.get_cover_letter_path(cover_letter_id)
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Cover letter not found")
        
        return FileResponse(
            path=str(file_path),
            filename=f"cover_letter_{cover_letter_id}.txt",
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading cover letter {cover_letter_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download cover letter")


@router.post("/bulk", response_model=BulkCoverLetterResponse)
async def generate_bulk_cover_letters(
    request: BulkCoverLetterRequest,
    db: Session = Depends(get_db)
):
    """Generate cover letters for multiple jobs in bulk."""
    import time
    import asyncio
    
    start_time = time.time()
    logger.info(f"Bulk generating cover letters for {len(request.job_ids)} jobs by user {request.user_id}")
    
    try:
        # Prepare user data once
        user_data = {
            "name": request.user_name or "User",
            "email": request.user_email or "user@example.com",
            "phone": request.user_phone or "+1(555) 123-4567",
            "location": request.user_location or "Location",
            "experience_years": request.experience_years,
            "primary_skills": request.primary_skills
        }
        
        results = []
        errors = []
        
        # Process each job
        for job_id in request.job_ids:
            try:
                # Fetch job details
                job_data = await _get_job_from_database(str(job_id), db)
                if not job_data:
                    errors.append({
                        "job_id": str(job_id),
                        "error": "Job not found",
                        "error_type": "not_found"
                    })
                    continue
                
                # Generate cover letter
                result = cover_letter_generator.generate_cover_letter(
                    job_data=job_data,
                    user_data=user_data,
                    selected_projects=request.selected_projects
                )
                
                results.append({
                    "job_id": str(job_id),
                    "job_title": job_data["title"],
                    "company": job_data["company"],
                    "cover_letter_id": result["cover_letter_id"],
                    "download_url": f"/api/v1/cover-letters/{result['cover_letter_id']}/download",
                    "generation_method": result["generation_method"],
                    "status": "success"
                })
                
                logger.info(f"Generated cover letter for job {job_id} - {job_data['title']} at {job_data['company']}")
                
            except Exception as e:
                logger.error(f"Failed to generate cover letter for job {job_id}: {e}")
                errors.append({
                    "job_id": str(job_id),
                    "error": str(e),
                    "error_type": "generation_failed"
                })
        
        execution_time = time.time() - start_time
        
        return BulkCoverLetterResponse(
            success=True,
            total_requested=len(request.job_ids),
            total_generated=len(results),
            total_failed=len(errors),
            execution_time_seconds=round(execution_time, 2),
            results=results,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Bulk cover letter generation failed: {e}")
        raise HTTPException(status_code=500, detail="Bulk generation failed")


@router.post("/generate")
async def generate_cover_letter_general(
    job_title: str = Query(..., description="Job title"),
    company: str = Query(..., description="Company name"),
    user_name: str = Query(..., description="User's full name"),
    user_email: str = Query(..., description="User's email"),
    user_phone: str = Query("+1(555) 123-4567", description="User's phone"),
    user_location: str = Query("Location", description="User's location"),
    experience_years: str = Query("2+", description="Years of experience"),
    primary_skills: str = Query("Software Development", description="Comma-separated skills"),
    job_description: str = Query("", description="Job description"),
    requirements: str = Query("", description="Comma-separated requirements")
):
    """Generate cover letter with query parameters (simplified endpoint)."""
    try:
        # Parse skills and requirements
        skills_list = [skill.strip() for skill in primary_skills.split(",")]
        requirements_list = [req.strip() for req in requirements.split(",") if req.strip()]
        
        # Prepare data
        job_data = {
            "title": job_title,
            "company": company,
            "description": job_description,
            "requirements": requirements_list
        }
        
        user_data = {
            "name": user_name,
            "email": user_email,
            "phone": user_phone,
            "location": user_location,
            "experience_years": experience_years,
            "primary_skills": skills_list
        }
        
        # Generate cover letter
        result = cover_letter_generator.generate_cover_letter(
            job_data=job_data,
            user_data=user_data,
            selected_projects=[]
        )
        
        return {
            "success": True,
            "cover_letter_id": result["cover_letter_id"],
            "content": result["content"],
            "download_url": f"/api/v1/cover-letters/{result['cover_letter_id']}/download",
            "generation_method": result["generation_method"]
        }
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate cover letter")


@router.post("/bulk/download")
async def download_bulk_cover_letters(
    cover_letter_ids: List[str] = Query(..., description="List of cover letter IDs to download")
):
    """Download multiple cover letters as a ZIP file."""
    import zipfile
    import tempfile
    import os
    from fastapi.responses import FileResponse
    
    try:
        logger.info(f"Creating bulk download for {len(cover_letter_ids)} cover letters")
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                
                valid_files = 0
                for cover_letter_id in cover_letter_ids:
                    file_path = cover_letter_generator.get_cover_letter_path(cover_letter_id)
                    
                    if file_path and file_path.exists():
                        # Add file to ZIP with a descriptive name
                        content = file_path.read_text(encoding='utf-8')
                        
                        # Try to extract job title from content for filename
                        lines = content.split('\n')
                        company_line = next((line for line in lines if 'Dear' in line or 'Company' in line), '')
                        
                        filename = f"cover_letter_{cover_letter_id}.txt"
                        if company_line:
                            # Extract company name for better filename
                            try:
                                company = company_line.split()[-1].replace(',', '').replace(':', '')
                                filename = f"cover_letter_{company}_{cover_letter_id[:8]}.txt"
                            except:
                                pass
                        
                        zip_file.writestr(filename, content)
                        valid_files += 1
                
                if valid_files == 0:
                    raise HTTPException(status_code=404, detail="No valid cover letters found")
            
            # Return ZIP file
            return FileResponse(
                path=temp_zip.name,
                filename=f"cover_letters_bulk_{len(cover_letter_ids)}_files.zip",
                media_type="application/zip"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk download: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bulk download")


async def _get_job_from_database(job_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Fetch job details from database."""
    try:
        from app.services.job_service import JobService
        
        job_service = JobService(db)
        job = job_service.get_job_by_id(job_id)
        
        if job:
            return {
                "title": job.title,
                "company": job.company,
                "description": job.description or "",
                "requirements": job.requirements or [],
                "location": job.location
            }
        return None
        
    except Exception as e:
        logger.warning(f"Could not fetch job {job_id} from database: {e}")
        return None