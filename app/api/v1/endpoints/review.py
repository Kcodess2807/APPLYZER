"""API endpoints for human-in-the-loop application review."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Literal
from pydantic import BaseModel
from loguru import logger
import uuid

from app.database.base import get_db
from app.orchestrator.review_workflow import HumanReviewWorkflow

router = APIRouter()


class StartReviewRequest(BaseModel):
    """Request to start application review."""
    user_id: str
    user_profile: Dict[str, Any]
    job: Dict[str, Any]
    matched_projects: List[Dict[str, Any]]


class ReviewDecisionRequest(BaseModel):
    """Request to submit review decision."""
    decision: Literal["approved", "edit", "rejected"]
    edits: Dict[str, Any] = {}
    reason: str = None


@router.post("/start")
async def start_review(
    request: StartReviewRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new application review workflow.
    
    This will:
    1. Generate resume and cover letter
    2. Pause for human review
    3. Return documents for review
    """
    try:
        application_id = str(uuid.uuid4())
        
        logger.info(f"Starting review workflow for application {application_id}")
        
        workflow = HumanReviewWorkflow(db)
        
        result = await workflow.start_application_review(
            user_id=request.user_id,
            user_profile=request.user_profile,
            job=request.job,
            matched_projects=request.matched_projects,
            application_id=application_id
        )
        
        return {
            "success": True,
            "thread_id": result["thread_id"],
            "application_id": result["application_id"],
            "status": result["status"],
            "resume": result["resume"],
            "cover_letter": result["cover_letter"],
            "message": "📝 Documents generated! Please review and submit your decision.",
            "next_steps": {
                "approve": f"POST /review/{result['thread_id']}/submit with decision='approved'",
                "edit": f"POST /review/{result['thread_id']}/submit with decision='edit' and edits",
                "reject": f"POST /review/{result['thread_id']}/submit with decision='rejected'"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thread_id}/submit")
async def submit_review(
    thread_id: str,
    decision: ReviewDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Submit review decision for an application.
    
    Decisions:
    - approved: Send the application
    - edit: Regenerate with changes
    - rejected: Skip this application
    """
    try:
        logger.info(f"Submitting review for {thread_id}: {decision.decision}")
        
        workflow = HumanReviewWorkflow(db)
        
        result = await workflow.submit_review(
            thread_id=thread_id,
            decision=decision.decision,
            edits=decision.edits,
            reason=decision.reason
        )
        
        return {
            "success": True,
            "thread_id": result["thread_id"],
            "status": result["status"],
            "message": result["message"],
            "final_state": result.get("final_state", {})
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}/status")
async def get_review_status(
    thread_id: str,
    db: Session = Depends(get_db)
):
    """Get current status of a review workflow."""
    try:
        workflow = HumanReviewWorkflow(db)
        
        status = await workflow.get_review_status(thread_id)
        
        return {
            "success": True,
            **status
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_reviews(
    user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all applications pending review.
    
    TODO: Implement database query for pending reviews
    """
    try:
        # This would query a reviews table in production
        logger.info(f"Fetching pending reviews for user: {user_id or 'all'}")
        
        return {
            "success": True,
            "pending_reviews": [],
            "message": "Review tracking not yet implemented in database"
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-start")
async def start_batch_review(
    user_id: str,
    user_profile: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Start review workflows for multiple jobs at once.
    
    Returns list of thread_ids for each job.
    """
    try:
        logger.info(f"Starting batch review for {len(jobs)} jobs")
        
        workflow = HumanReviewWorkflow(db)
        results = []
        
        # Import project matcher
        from app.agents.project_matcher import ProjectMatcherAgent
        
        project_matcher = ProjectMatcherAgent(db)
        
        for job in jobs:
            try:
                # Match projects for this job
                match_result = await project_matcher.run({
                    "user_id": user_id,
                    "job": job,
                    "max_projects": 5
                })
                
                matched_projects = match_result.data.get("matched_projects", [])
                
                # Start review workflow
                application_id = str(uuid.uuid4())
                result = await workflow.start_application_review(
                    user_id=user_id,
                    user_profile=user_profile,
                    job=job,
                    matched_projects=matched_projects,
                    application_id=application_id
                )
                
                results.append({
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "thread_id": result["thread_id"],
                    "application_id": result["application_id"],
                    "status": "pending_review"
                })
                
            except Exception as e:
                logger.error(f"Failed to process job {job.get('title')}: {e}")
                results.append({
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "success": True,
            "total_jobs": len(jobs),
            "successful": len([r for r in results if "thread_id" in r]),
            "failed": len([r for r in results if "error" in r]),
            "results": results,
            "message": f"Started review for {len([r for r in results if 'thread_id' in r])} applications"
        }
        
    except Exception as e:
        logger.error(f"Batch review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
