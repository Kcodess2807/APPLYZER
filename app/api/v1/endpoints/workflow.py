"""API endpoints for workflow orchestration."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.database.base import get_db  # consolidated — was app.database.session
from app.orchestrator import JobApplicationOrchestrator
from loguru import logger

router = APIRouter()


# Request/Response models
class JobSourceConfig(BaseModel):
    """Configuration for job source."""
    source: str  # "csv", "linkedin", "google_sheets"
    url: Optional[str] = None
    filters: Optional[dict] = None


class WorkflowOptions(BaseModel):
    """Optional workflow settings."""
    template: str = "standard"
    tone: str = "professional"
    max_projects: int = 5


class FullWorkflowRequest(BaseModel):
    """Request for full workflow execution."""
    user_id: str
    user_profile: dict
    job_source: JobSourceConfig
    options: Optional[WorkflowOptions] = None


class SingleJobRequest(BaseModel):
    """Request for processing a single job."""
    user_id: str
    user_profile: dict
    job: dict
    options: Optional[WorkflowOptions] = None


class MatchProjectsRequest(BaseModel):
    """Request body for project matching."""
    user_id: str
    job: Dict[str, Any]
    max_projects: int = 5


class GenerateResumeRequest(BaseModel):
    """Request body for standalone resume generation."""
    user_profile: Dict[str, Any]
    job: Dict[str, Any]
    matched_projects: List[Any]
    template: str = "standard"


class WriteCoverLetterRequest(BaseModel):
    """Request body for standalone cover letter generation."""
    user_profile: Dict[str, Any]
    job: Dict[str, Any]
    resume_data: Dict[str, Any]
    matched_projects: List[Any]
    tone: str = "professional"


@router.post("/run-full-workflow")
async def run_full_workflow(
    request: FullWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Execute complete workflow: fetch jobs → match projects → generate resume → write cover letter.
    """
    try:
        orchestrator = JobApplicationOrchestrator(db)
        
        result = await orchestrator.run_full_workflow(
            user_id=request.user_id,
            user_profile=request.user_profile,
            job_source_config=request.job_source.dict(),
            options=request.options.dict() if request.options else None
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Workflow execution failed")


@router.post("/upload-jobs-csv")
async def upload_jobs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file with job listings.
    Expected columns: job_title, company, job_link, job_description, email
    """
    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode("utf-8")
        
        orchestrator = JobApplicationOrchestrator(db)
        
        result = await orchestrator.fetch_jobs_only({
            "source": "csv",
            "csv_content": csv_content
        })
        
        return result
        
    except Exception as e:
        logger.error(f"CSV upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="CSV upload failed")


@router.post("/fetch-jobs")
async def fetch_jobs(
    source_config: JobSourceConfig,
    db: Session = Depends(get_db)
):
    """
    Fetch jobs from specified source (standalone agent execution).
    """
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.fetch_jobs_only(source_config.dict())
        return result
        
    except Exception as e:
        logger.error(f"Job fetching failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Job fetching failed")


@router.post("/match-projects")
async def match_projects(
    request: MatchProjectsRequest,
    db: Session = Depends(get_db),
):
    """Match projects to job requirements (standalone agent execution)."""
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.match_projects_only(
            request.user_id, request.job, request.max_projects
        )
        return result

    except Exception as e:
        logger.error(f"Project matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Project matching failed")


@router.post("/generate-resume")
async def generate_resume(
    request: GenerateResumeRequest,
    db: Session = Depends(get_db),
):
    """Generate resume for specific job (standalone agent execution)."""
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.generate_resume_only(
            request.user_profile, request.job, request.matched_projects, request.template
        )
        return result

    except Exception as e:
        logger.error(f"Resume generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Resume generation failed")


@router.post("/write-cover-letter")
async def write_cover_letter(
    request: WriteCoverLetterRequest,
    db: Session = Depends(get_db),
):
    """Write cover letter for specific job (standalone agent execution)."""
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.write_cover_letter_only(
            request.user_profile,
            request.job,
            request.resume_data,
            request.matched_projects,
            request.tone,
        )
        return result

    except Exception as e:
        logger.error(f"Cover letter writing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cover letter generation failed")


@router.post("/process-single-job")
async def process_single_job(
    request: SingleJobRequest,
    db: Session = Depends(get_db)
):
    """
    Process a single job through the complete pipeline.
    """
    try:
        orchestrator = JobApplicationOrchestrator(db)
        
        options = request.options.dict() if request.options else {}
        
        result = await orchestrator._process_single_job(
            user_id=request.user_id,
            user_profile=request.user_profile,
            job=request.job,
            options=options
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Single job processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Single job processing failed")
