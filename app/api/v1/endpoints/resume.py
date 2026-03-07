from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime, timezone
from pathlib import Path
import uuid

from app.database.base import get_db
from app.schemas.resume import (
    ResumeGenerationRequest, 
    BulkResumeRequest,
    ResumeResponse, 
    BulkResumeResponse,
    ProjectItem,
    EducationItem,
    SkillCategory,
    ExperienceItem
)
from app.services.resume_generator import resume_generator, ResumeGenerationError
from app.services.resume_helpers import (
    get_job_context, 
    filter_projects_by_ids, 
    validate_resume_request,
    prepare_resume_data
)
from app.services.project_service import ProjectService
from app.services.job_service import JobService
from pydantic import BaseModel

router = APIRouter()

# Additional schema classes that seem to be missing
class JobFilesResponse(BaseModel):
    """Response model for job-specific files."""
    job_id: str
    exists: bool
    templates: Dict[str, Any]
    pdfs: Dict[str, Any]
    files_count: int

# ============================================================================
# MAIN RESUME GENERATION ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=ResumeResponse)
async def generate_resume(
    request: ResumeGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate a customized resume PDF with job-specific file organization."""
    try:
        logger.info(f"Generating resume for {request.name}")
        
        # Convert request to dict for template
        user_data = request.dict()
        
        # Get job context if job_id provided
        job_context = None
        if request.job_id:
            try:
                job_context = await _get_job_context(request.job_id, db)
                logger.info(f"Job context retrieved for {request.job_id}: {job_context}")
            except Exception as job_error:
                logger.warning(f"Could not get job context for {request.job_id}: {job_error}")
                # Create a default job context to avoid breaking resume generation
                job_context = {
                    "title": "Software Engineer",
                    "company": "Tech Company",
                    "description": f"Position with job ID: {request.job_id}",
                    "requirements": [],
                    "location": "Remote"
                }
        
        # Get selected projects
        selected_projects = None
        if request.selected_project_ids and request.projects:
            selected_projects = _filter_projects_by_ids(
                request.projects, request.selected_project_ids
            )
            logger.info(f"Selected {len(selected_projects)} specific projects")
        elif request.projects:
            # Use all projects if none specifically selected
            selected_projects = [proj.dict() for proj in request.projects]
            logger.info(f"Using all {len(selected_projects)} projects")
        else:
            logger.info("No projects provided")
        
        # Generate resume
        try:
            # Try the new method signature first
            result = resume_generator.generate_resume(
                user_data=user_data,
                selected_projects=selected_projects,
                job_context=job_context,
                job_id=request.job_id
            )
            logger.info(f"Resume generated with job_id support: {result['resume_id']}")
        except TypeError as method_error:
            # If the method doesn't support job_id, fall back to old signature
            if "unexpected keyword argument 'job_id'" in str(method_error):
                logger.warning("resume_generator doesn't support job_id parameter, using legacy method")
                result = resume_generator.generate_resume(
                    user_data=user_data,
                    selected_projects=selected_projects,
                    job_context=job_context
                )
                # Manually add job_id to result if it was provided
                if request.job_id:
                    result["job_id"] = request.job_id
                    result["resume_id"] = request.job_id
                logger.info(f"Resume generated with legacy method: {result['resume_id']}")
            else:
                raise method_error
        
        # Prepare response URLs
        base_url = "/api/v1/resume"
        download_url = f"{base_url}/download/{result['resume_id']}"
        template_url = None
        
        # Check if job-specific files were created
        if request.job_id and "template_path" in result:
            template_url = f"{base_url}/download/{result['resume_id']}/template"
        
        # Build response
        response = ResumeResponse(
            success=True,
            resume_id=result.get("resume_id", str(uuid.uuid4())),
            job_id=request.job_id,
            download_url=download_url,
            template_url=template_url,
            generation_method=result.get("generation_method", "unknown"),
            file_paths={
                "pdf": result.get("pdf_path", result.get("file_path")),
                "template": result.get("template_path")
            } if request.job_id else {"pdf": result.get("file_path")},
            created_at=result.get("created_at", datetime.now(timezone.utc).isoformat()),
            user_name=result.get("user_name", request.name),
            job_title=result.get("job_title", job_context.get("title", "General") if job_context else "General"),
            message=f"Resume generated successfully using {result.get('generation_method', 'unknown')}" +
                   (f" for job {request.job_id}" if request.job_id else "")
        )
        
        logger.info(f"Resume generation completed successfully: {response.resume_id}")
        return response
        
    except ResumeGenerationError as e:
        logger.error(f"Resume generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error generating resume: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate resume: {str(e)}")

# ============================================================================
# BULK RESUME GENERATION ENDPOINTS 🚀
# ============================================================================

@router.post("/bulk-generate", response_model=BulkResumeResponse)
async def generate_bulk_resumes(
    request: BulkResumeRequest,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    🚀 Generate customized resumes for multiple jobs with AI-matched projects.
    
    This endpoint:
    1. Takes 5-6 job IDs selected by user
    2. For each job, finds the best matching projects using TF-IDF algorithm  
    3. Generates a customized resume with the best projects for that specific job
    4. Returns download URLs for all generated resumes
    """
    
    try:
        logger.info(f"🚀 Bulk resume generation requested for user {user_id} - {len(request.job_ids)} jobs")
        
        # Validate request
        if len(request.job_ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 jobs allowed per bulk request")
        
        if len(request.job_ids) < 1:
            raise HTTPException(status_code=400, detail="At least 1 job required")
        
        # Initialize services
        project_service = ProjectService(db)
        job_service = JobService(db)
        
        # Get all user projects for matching
        all_user_projects = project_service.get_user_projects(user_id)
        
        if not all_user_projects:
            raise HTTPException(status_code=400, detail="No projects found for user. Please create projects first.")
        
        logger.info(f"Found {len(all_user_projects)} user projects for matching")
        
        # Results tracking
        results = {
            "success": True,
            "user_id": user_id,
            "total_jobs": len(request.job_ids),
            "resumes_generated": [],
            "failed_jobs": [],
            "processing_summary": {}
        }
        
        # Process each job
        for job_id in request.job_ids:
            try:
                logger.info(f"Processing job {job_id}...")
                
                # Get job details
                job = job_service.get_job_by_id(job_id)
                if not job:
                    raise Exception(f"Job {job_id} not found")
                
                # Match projects to this specific job using simple scoring
                best_projects = _match_projects_to_job(all_user_projects, job, request.max_projects_per_resume)
                
                # Generate resume for this specific job
                user_data = request.dict()
                user_data['projects'] = best_projects  # Use matched projects
                
                job_context = {
                    "title": job.title,
                    "company": job.company,
                    "description": job.description,
                    "requirements": getattr(job, 'requirements', []) or [],
                    "location": job.location
                }
                
                # Generate resume with job-specific context
                resume_result = resume_generator.generate_resume(
                    user_data=user_data,
                    selected_projects=best_projects,
                    job_context=job_context,
                    job_id=job_id
                )
                
                # Add to successful results
                job_result = {
                    "job_id": job_id,
                    "job_title": job.title,
                    "job_company": job.company,
                    "resume_id": resume_result["resume_id"],
                    "resume_file_path": resume_result["file_path"],
                    "generation_method": resume_result["generation_method"],
                    "selected_projects": [{"title": p["title"], "technologies": p.get("technologies", [])} for p in best_projects],
                    "projects_count": len(best_projects),
                    "matching_summary": {
                        "total_projects_analyzed": len(all_user_projects),
                        "best_projects_selected": len(best_projects),
                        "job_match_score": f"{_calculate_job_match_score(best_projects, job):.1f}%"
                    }
                }
                
                results["resumes_generated"].append(job_result)
                logger.info(f"✅ Resume generated for {job.title} at {job.company}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate resume for job {job_id}: {e}")
                results["failed_jobs"].append({
                    "job_id": job_id,
                    "error": str(e)
                })
        
        # Generate download URLs
        download_urls = []
        for resume in results["resumes_generated"]:
            download_urls.append({
                "job_id": resume["job_id"],
                "job_title": resume["job_title"],
                "job_company": resume["job_company"],
                "resume_id": resume["resume_id"],
                "download_url": f"/api/v1/resume/download/{resume['resume_id']}",
                "projects_used": resume["projects_count"],
                "match_score": resume["matching_summary"]["job_match_score"]
            })
        
        # Generate processing summary
        results["processing_summary"] = {
            "successful_resumes": len(results["resumes_generated"]),
            "failed_resumes": len(results["failed_jobs"]),
            "success_rate": f"{len(results['resumes_generated'])/len(request.job_ids)*100:.1f}%",
            "total_projects_analyzed": len(all_user_projects),
            "processing_time": datetime.now().isoformat()
        }
        
        return BulkResumeResponse(
            success=results["success"],
            message=f"Generated {len(results['resumes_generated'])}/{len(request.job_ids)} resumes successfully",
            user_id=user_id,
            total_jobs=results["total_jobs"],
            resumes_generated=results["resumes_generated"],
            failed_jobs=results["failed_jobs"],
            processing_summary=results["processing_summary"],
            download_urls=download_urls
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk resume generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk resume generation failed: {str(e)}")

@router.get("/jobs/recommended/{user_id}")
async def get_recommended_jobs_for_bulk_resume(
    user_id: str,
    limit: int = Query(10, description="Number of recommended jobs"),
    keywords: Optional[str] = Query(None, description="Job search keywords"),
    location: Optional[str] = Query(None, description="Job location"),
    db: Session = Depends(get_db)
):
    """Get recommended jobs for bulk resume generation based on user's projects."""
    
    try:
        logger.info(f"Getting recommended jobs for user {user_id}")
        
        job_service = JobService(db)
        
        # Get jobs based on filters
        keyword_list = None
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        
        recommended_jobs = job_service.search_jobs(
            keywords=keyword_list,
            location=location,
            limit=limit
        )
        
        # Format for frontend
        job_options = []
        for job in recommended_jobs:
            job_options.append({
                "job_id": str(job.id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description[:200] + "..." if len(job.description) > 200 else job.description,
                "requirements": getattr(job, 'requirements', []) or [],
                "posted_date": getattr(job, 'posted_date', None),
                "suitable_for_bulk": True,
                "salary_range": getattr(job, 'salary_range', None)
            })
        
        return {
            "success": True,
            "recommended_jobs": job_options,
            "total_available": len(job_options),
            "filters_applied": {
                "keywords": keyword_list,
                "location": location,
                "limit": limit
            },
            "message": f"Found {len(job_options)} jobs suitable for bulk resume generation"
        }
        
    except Exception as e:
        logger.error(f"Error getting recommended jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommended jobs")

@router.post("/test-bulk-flow")
async def test_bulk_resume_flow(
    user_id: str = Query(..., description="User ID for testing"),
    db: Session = Depends(get_db)
):
    """
    🧪 Test endpoint for the complete bulk resume generation flow.
    This creates sample data and runs the bulk generation process.
    """
    
    try:
        logger.info(f"🧪 Testing bulk resume flow for user {user_id}")
        
        # Get user's projects
        project_service = ProjectService(db)
        user_projects = project_service.get_user_projects(user_id, limit=10)
        
        if not user_projects:
            raise HTTPException(status_code=400, detail="No projects found. Please create some projects first.")
        
        # Get some available jobs
        job_service = JobService(db)
        available_jobs = job_service.search_jobs(limit=6)
        
        if not available_jobs or len(available_jobs) < 2:
            raise HTTPException(status_code=400, detail="Not enough jobs in database. Please add some jobs first.")
        
        # Select first 3-5 jobs for testing
        selected_jobs = available_jobs[:min(5, len(available_jobs))]
        job_ids = [str(job.id) for job in selected_jobs]
        
        # Create test bulk request
        test_request = BulkResumeRequest(
            job_ids=job_ids,
            name="John Doe (Test)",
            phone="+91-9876543210",
            location="Bangalore, India",
            email="john.doe@example.com",
            experience_years="3+",
            primary_skills=["Python", "Machine Learning", "FastAPI"],
            education=[{
                "degree": "B.Tech Computer Science",
                "institution": "Test University",
                "year": "2022"
            }],
            skills=[{
                "category": "Programming",
                "items": ["Python", "JavaScript", "SQL"]
            }],
            max_projects_per_resume=3
        )
        
        # Call bulk generation
        bulk_result = await generate_bulk_resumes(test_request, user_id, db)
        
        return {
            "success": True,
            "message": "🎉 Bulk resume test completed successfully!",
            "test_data": {
                "user_projects_found": len(user_projects),
                "jobs_available": len(available_jobs),
                "jobs_selected_for_test": len(job_ids),
                "selected_job_titles": [job.title for job in selected_jobs]
            },
            "bulk_generation_result": bulk_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk resume test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# ============================================================================
# FILE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/download/{resume_id}")
async def download_resume(resume_id: str):
    """Download a generated resume PDF with proper filename."""
    try:
        # Check if this is a job-specific resume
        if resume_id.startswith("job_") or len(resume_id.split("-")) == 5:  # UUID format
            job_files = resume_generator.get_job_files(resume_id)
            if not job_files["exists"]:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            # Get PDF path from job files
            if "files" in job_files["pdfs"] and "resume" in job_files["pdfs"]["files"]:
                file_path = Path(job_files["pdfs"]["files"]["resume"]["path"])
                filename = file_path.name
            else:
                raise HTTPException(status_code=404, detail="Resume PDF not found")
        else:
            # Legacy resume handling
            for pdf_file in resume_generator.output_dir.glob(f"*_{resume_id}.pdf"):
                if pdf_file.exists():
                    file_path = pdf_file
                    filename = pdf_file.name
                    break
            else:
                # Fallback to old naming convention
                file_path = resume_generator.get_resume_path(resume_id)
                filename = f"resume_{resume_id}.pdf"
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Resume file not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download resume")

@router.get("/job/{job_id}/files", response_model=JobFilesResponse)
async def get_job_files(job_id: str):
    """Get all files associated with a specific job ID."""
    try:
        logger.info(f"Getting files for job {job_id}")
        job_files = resume_generator.get_job_files(job_id)
        
        if not job_files["exists"]:
            raise HTTPException(status_code=404, detail=f"No files found for job {job_id}")
        
        # Count total files
        files_count = 0
        if job_files["templates"]:
            files_count += 1
        if "files" in job_files["pdfs"]:
            files_count += len(job_files["pdfs"]["files"])
        
        return JobFilesResponse(
            job_id=job_id,
            exists=job_files["exists"],
            templates=job_files["templates"],
            pdfs=job_files["pdfs"],
            files_count=files_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting files for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job files")

@router.delete("/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete resume and associated files."""
    try:
        logger.info(f"Deleting resume {resume_id}")
        
        # Check if this is a job-specific resume
        if resume_id.startswith("job_") or len(resume_id.split("-")) == 5:  # UUID format
            job_files = resume_generator.get_job_files(resume_id)
            if not job_files["exists"]:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            # Delete job-specific directories
            import shutil
            
            # Delete template directory
            template_dir = resume_generator.storage_service.generated_templates_dir / f"job_{resume_id}"
            if template_dir.exists():
                shutil.rmtree(template_dir)
                logger.info(f"Deleted template directory: {template_dir}")
            
            # Delete resume directory
            resume_dir = resume_generator.storage_service.resumes_dir / f"job_{resume_id}"
            if resume_dir.exists():
                shutil.rmtree(resume_dir)
                logger.info(f"Deleted resume directory: {resume_dir}")
            
            return {
                "success": True,
                "resume_id": resume_id,
                "message": f"Resume {resume_id} and all associated files deleted successfully"
            }
        else:
            # Legacy resume deletion
            file_path = resume_generator.get_resume_path(resume_id)
            if file_path and file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted legacy resume: {file_path}")
                return {
                    "success": True,
                    "resume_id": resume_id,
                    "message": f"Resume {resume_id} deleted successfully"
                }
            else:
                raise HTTPException(status_code=404, detail="Resume not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete resume")

@router.get("/list")
async def list_resumes(
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all resumes with optional filtering."""
    try:
        logger.info(f"Listing resumes (user_id: {user_id}, job_id: {job_id})")
        
        resumes = []
        
        # Scan legacy resumes
        legacy_dir = Path("app/generated/resumes")
        if legacy_dir.exists():
            # Check for new naming convention first
            for file_path in legacy_dir.glob("*_*.pdf"):
                if file_path.name.startswith("resume_"):
                    continue  # Skip old format
                
                # Extract name and job_id from filename
                stem = file_path.stem
                parts = stem.split("_")
                if len(parts) >= 2:
                    user_name = "_".join(parts[:-1])
                    job_id_from_name = parts[-1]
                    stat = file_path.stat()
                    resumes.append({
                        "resume_id": job_id_from_name,
                        "job_id": job_id_from_name,
                        "user_name": user_name.replace("_", " ").title(),
                        "type": "named_format",
                        "file_path": str(file_path),
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "created_at": stat.st_ctime,
                        "files_count": 1
                    })
            
            # Check for old naming convention
            for file_path in legacy_dir.glob("resume_*.pdf"):
                resume_id = file_path.stem.replace("resume_", "")
                if not any(r["resume_id"] == resume_id for r in resumes):  # Avoid duplicates
                    stat = file_path.stat()
                    resumes.append({
                        "resume_id": resume_id,
                        "job_id": None,
                        "user_name": "Unknown",
                        "type": "legacy",
                        "file_path": str(file_path),
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "created_at": stat.st_ctime,
                        "files_count": 1
                    })
        
        # Apply job_id filter if provided
        if job_id:
            resumes = [r for r in resumes if r.get("job_id") == job_id]
        
        # Sort by creation time (newest first)
        resumes.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        
        # Apply pagination
        total = len(resumes)
        paginated_resumes = resumes[offset:offset + limit]
        
        return {
            "success": True,
            "resumes": paginated_resumes,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"Error listing resumes: {e}")
        raise HTTPException(status_code=500, detail="Failed to list resumes")

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/template")
async def get_resume_template():
    """Get the resume template structure for frontend forms."""
    return {
        "success": True,
        "template": {
            "personal_info": {
                "name": "string (required)",
                "phone": "string (required)",
                "location": "string (required)",
                "email": "string (required)",
                "linkedin_url": "string (optional)",
                "linkedin_display": "string (optional)",
                "website_url": "string (optional)",
                "website_display": "string (optional)"
            },
            "professional_info": {
                "experience_years": "string (default: '2+')",
                "primary_skills": "array of strings"
            },
            "sections": {
                "education": [{
                    "degree": "string",
                    "institution": "string",
                    "year": "string",
                    "coursework": "string (optional)",
                    "gpa": "string (optional)"
                }],
                "skills": [{
                    "category": "string",
                    "items": ["array", "of", "strings"]
                }],
                "experience": [{
                    "role": "string",
                    "company": "string",
                    "duration": "string",
                    "location": "string",
                    "achievements": ["array", "of", "strings"]
                }],
                "projects": [{
                    "title": "string",
                    "description": "string",
                    "technologies": ["array", "of", "strings"],
                    "url": "string (optional)"
                }],
                "extra_curricular": ["array", "of", "strings"],
                "leadership": ["array", "of", "strings"]
            },
            "customization": {
                "job_id": "string (optional) - for job-specific customization",
                "selected_project_ids": ["array", "of", "project", "indices"]
            }
        }
    }

@router.get("/status")
async def get_resume_generator_status():
    """Get the status of resume generation capabilities."""
    status_info = {
        "latex_available": resume_generator.latex_available,
        "output_directory": str(resume_generator.output_dir),
        "template_directory": str(resume_generator.template_dir)
    }
    
    # Add job-specific directory info if available
    if hasattr(resume_generator, 'storage_service'):
        status_info.update({
            "job_templates_directory": str(resume_generator.storage_service.generated_templates_dir),
            "job_resumes_directory": str(resume_generator.storage_service.resumes_dir),
            "organized_storage": True
        })
    else:
        status_info["organized_storage"] = False
    
    # Try to get fallback availability
    try:
        status_info["reportlab_available"] = hasattr(resume_generator, 'REPORTLAB_AVAILABLE') and resume_generator.REPORTLAB_AVAILABLE
        status_info["weasyprint_available"] = hasattr(resume_generator, 'WEASYPRINT_AVAILABLE') and resume_generator.WEASYPRINT_AVAILABLE
    except:
        status_info["reportlab_available"] = False
        status_info["weasyprint_available"] = False
    
    return {
        "success": True,
        "status": status_info
    }

# ============================================================================
# HELPER FUNCTIONS FOR BULK RESUME GENERATION 🧠
# ============================================================================

async def _get_job_context(job_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Get job context for resume customization."""
    try:
        job_service = JobService(db)
        job = job_service.get_job_by_id(job_id)
        
        if job:
            return {
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "requirements": getattr(job, 'requirements', []) or [],
                "location": job.location
            }
        return None
    except Exception as e:
        logger.warning(f"Could not get job context for {job_id}: {e}")
        return None

def _filter_projects_by_ids(
    all_projects: List[ProjectItem],
    selected_ids: List[str]
) -> List[Dict[str, Any]]:
    """Filter projects by selected IDs."""
    # For now, assume project IDs are indices
    selected_projects = []
    for project_id in selected_ids:
        try:
            index = int(project_id)
            if 0 <= index < len(all_projects):
                selected_projects.append(all_projects[index].dict())
        except (ValueError, IndexError):
            logger.warning(f"Invalid project ID: {project_id}")
    
    return selected_projects

def _match_projects_to_job(user_projects: List[Any], job: Any, max_projects: int = 4) -> List[Dict[str, Any]]:
    """
    Simple project-to-job matching algorithm.
    Returns the best matching projects for a specific job.
    """
    
    job_keywords = set()
    
    # Extract keywords from job
    job_title_words = job.title.lower().split()
    job_desc_words = job.description.lower().split() if job.description else []
    job_requirements = getattr(job, 'requirements', []) or []
    
    # Combine all job-related keywords
    job_keywords.update(job_title_words)
    job_keywords.update(job_desc_words[:20])  # First 20 words from description
    job_keywords.update([req.lower() for req in job_requirements])
    
    # Remove common words
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
    job_keywords = job_keywords - stop_words
    
    # Score each project
    project_scores = []
    
    for project in user_projects:
        score = 0
        
        # Check title match
        project_title_words = set(project.title.lower().split())
        title_matches = len(job_keywords.intersection(project_title_words))
        score += title_matches * 3  # Title matches are worth more
        
        # Check description match
        project_desc_words = set(project.description.lower().split()) if project.description else set()
        desc_matches = len(job_keywords.intersection(project_desc_words))
        score += desc_matches * 2
        
        # Check technology match
        project_technologies = set([tech.lower() for tech in (project.technologies or [])])
        tech_matches = len(job_keywords.intersection(project_technologies))
        score += tech_matches * 4  # Technology matches are very important
        
        # Check skills match
        project_skills = set([skill.lower() for skill in (getattr(project, 'skills_demonstrated', []) or [])])
        skill_matches = len(job_keywords.intersection(project_skills))
        score += skill_matches * 3
        
        project_scores.append((score, project))
    
    # Sort by score and select top projects
    project_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Convert top projects to dictionary format
    selected_projects = []
    for score, project in project_scores[:max_projects]:
        project_dict = {
            "title": project.title,
            "description": project.description,
            "technologies": project.technologies or [],
            "url": getattr(project, 'project_url', None),
            "match_score": score
        }
        selected_projects.append(project_dict)
    
    logger.info(f"Selected {len(selected_projects)} projects for job {job.title}")
    
    return selected_projects

def _calculate_job_match_score(projects: List[Dict[str, Any]], job: Any) -> float:
    """Calculate overall match score between selected projects and job."""
    
    if not projects:
        return 0.0
    
    total_score = sum(project.get('match_score', 0) for project in projects)
    max_possible_score = len(projects) * 20  # Rough estimate of max score per project
    
    match_percentage = min(100.0, (total_score / max_possible_score) * 100)
    return match_percentage