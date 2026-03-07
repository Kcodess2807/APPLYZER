"""API endpoints for workflow orchestration."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database.session import get_db
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match-projects")
async def match_projects(
    user_id: str,
    job: dict,
    max_projects: int = 5,
    db: Session = Depends(get_db)
):
    """
    Match projects to job requirements (standalone agent execution).
    """
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.match_projects_only(user_id, job, max_projects)
        return result
        
    except Exception as e:
        logger.error(f"Project matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-resume")
async def generate_resume(
    user_profile: dict,
    job: dict,
    matched_projects: list,
    template: str = "standard",
    db: Session = Depends(get_db)
):
    """
    Generate resume for specific job (standalone agent execution).
    """
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.generate_resume_only(
            user_profile, job, matched_projects, template
        )
        return result
        
    except Exception as e:
        logger.error(f"Resume generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/write-cover-letter")
async def write_cover_letter(
    user_profile: dict,
    job: dict,
    resume_data: dict,
    matched_projects: list,
    tone: str = "professional",
    db: Session = Depends(get_db)
):
    """
    Write cover letter for specific job (standalone agent execution).
    """
    try:
        orchestrator = JobApplicationOrchestrator(db)
        result = await orchestrator.write_cover_letter_only(
            user_profile, job, resume_data, matched_projects, tone
        )
        return result
        
    except Exception as e:
        logger.error(f"Cover letter writing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))
