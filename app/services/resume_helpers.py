"""
Helper functions for resume generation and processing.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from app.schemas.resume import ProjectItem


def filter_projects_by_ids(
    all_projects: List[ProjectItem], 
    selected_ids: List[str]
) -> List[Dict[str, Any]]:
    """Filter projects by selected IDs."""
    selected_projects = []
    
    for i, project_id in enumerate(selected_ids):
        try:
            index = int(project_id)
            if 0 <= index < len(all_projects):
                selected_projects.append(all_projects[index].dict())
        except (ValueError, IndexError):
            logger.warning(f"Invalid project ID: {project_id}")
    
    return selected_projects


async def get_job_context(job_id: str, db) -> Optional[Dict[str, Any]]:
    """Get job context for resume customization."""
    try:
        from app.services.job_service import JobService
        
        job_service = JobService(db)
        job = job_service.get_job_by_id(job_id)
        
        if job:
            return {
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "requirements": job.requirements or [],
                "location": job.location
            }
        return None
        
    except Exception as e:
        logger.warning(f"Could not get job context for {job_id}: {e}")
        return None


def validate_resume_request(request) -> Dict[str, Any]:
    """Validate and prepare resume request data."""
    errors = []
    
    # Required fields validation
    if not request.name or len(request.name.strip()) < 2:
        errors.append("Name is required and must be at least 2 characters")
    
    if not request.email or "@" not in request.email:
        errors.append("Valid email is required")
    
    if not request.phone:
        errors.append("Phone number is required")
    
    if not request.location:
        errors.append("Location is required")
    
    # Optional field validation
    if request.job_ids and len(request.job_ids) > 10:
        errors.append("Maximum 10 jobs allowed for bulk generation")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def prepare_resume_data(request, job_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Prepare resume data for generation."""
    
    # Convert request to dict for template
    user_data = request.dict()
    
    # Add job-specific customization
    if job_context:
        # Customize objective based on job
        user_data["job_context"] = job_context
    
    return user_data