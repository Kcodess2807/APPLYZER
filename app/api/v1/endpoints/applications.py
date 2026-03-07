"""Job application endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
import uuid

from app.database.base import get_db
from app.services.application_orchestrator import ApplicationOrchestrator, send_applications_with_gaps
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import (
    ApplicationResponse,
    BulkApplyRequest,
    BulkApplyResponse,
    GeneratedApplicationInfo,
    QuickApplyRequest,
)

router = APIRouter()


@router.post("/bulk-apply", response_model=BulkApplyResponse)
async def bulk_apply_to_jobs(
    request: BulkApplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Two-phase bulk job application.

    Phase 1 (runs before this endpoint returns):
    - For each selected job: AI selects relevant projects, generates
      resume (LaTeX/PDF), cover letter (AI), and cold DM email body.
    - All files saved to generated/{user_id}/{job_id}/.
    - Application records created in DB with status='docs_ready'.

    Phase 2 (runs in the background after response is sent):
    - Emails are sent one by one with a gap of `send_gap_minutes` between
      each to avoid spam filters.
    - Each email includes resume.pdf and cover_letter.txt as attachments.
    - Application status updated to 'sent' and tracked in Google Sheets.
    """
    try:
        logger.info(f"Bulk apply request: {len(request.job_ids)} jobs for profile {request.profile_id}")

        batch_id = str(uuid.uuid4())
        orchestrator = ApplicationOrchestrator(db)

        # ── Phase 1: generate all documents (blocking) ───────────────────────
        generated_raw = orchestrator.generate_all_documents(
            user_id=request.profile_id,
            job_ids=request.job_ids,
            batch_id=batch_id,
        )

        successful = [g for g in generated_raw if g.get("success")]
        generated_info = [
            GeneratedApplicationInfo(
                job_id=g["job_id"],
                job_title=g.get("job_title"),
                company=g.get("company"),
                success=g.get("success", False),
                selected_projects=g.get("selected_projects"),
                resume_path=g.get("resume_path"),
                cover_letter_path=g.get("cover_letter_path"),
                output_dir=g.get("output_dir"),
                error=g.get("error"),
            )
            for g in generated_raw
        ]

        # ── Phase 2: send emails in background with gap ──────────────────────
        if successful:
            background_tasks.add_task(
                send_applications_with_gaps,
                successful,
                request.send_gap_minutes,
            )

        return BulkApplyResponse(
            batch_id=batch_id,
            status="sending_in_progress" if successful else "generation_failed",
            total_jobs=len(request.job_ids),
            docs_generated=len(successful),
            send_gap_minutes=request.send_gap_minutes,
            generated=generated_info,
            message=(
                f"Documents generated for {len(successful)}/{len(request.job_ids)} jobs. "
                f"Emails will be sent every {request.send_gap_minutes} minutes in the background."
                if successful
                else "Document generation failed for all jobs. No emails will be sent."
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Bulk apply error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ApplicationResponse])
async def get_user_applications(
    user_id: str = Query(..., description="User ID"),
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all applications for a user."""
    try:
        query = db.query(Application).filter(
            Application.profile_id == uuid.UUID(user_id)
        )
        
        if status:
            query = query.filter(Application.status == status)
        
        applications = query.order_by(
            Application.email_sent_at.desc()
        ).offset(offset).limit(limit).all()
        
        return applications
        
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get specific application details."""
    try:
        application = db.query(Application).filter(
            Application.id == uuid.UUID(application_id)
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{application_id}/status")
async def check_application_status(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Check email status and replies for an application."""
    try:
        application = db.query(Application).filter(
            Application.id == uuid.UUID(application_id)
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Check for replies in Gmail
        from app.services.gmail_service import GmailService
        gmail = GmailService()
        
        has_reply = gmail.check_thread_replies(application.gmail_thread_id)
        
        # Update if reply found
        if has_reply and not application.reply_received:
            application.reply_received = True
            application.status = 'replied'
            db.commit()
        
        return {
            "application_id": str(application.id),
            "status": application.status,
            "email_sent_at": application.email_sent_at,
            "reply_received": application.reply_received,
            "followup_count": application.followup_count,
            "last_followup_at": application.last_followup_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-apply", response_model=BulkApplyResponse)
async def quick_apply_to_jobs(
    request: QuickApplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Apply to jobs by providing JDs inline — no pre-seeded job IDs needed.

    Perfect for testing or applying to 10 jobs at once:
    - Provide title, company, description, hr_email for each job
    - System creates Job records, selects relevant projects per JD,
      generates resume + cover letter + cold DM, then emails them out
      with a gap between each send.
    """
    try:
        logger.info(f"Quick-apply: {len(request.jobs)} jobs for user {request.user_id}")

        # ── Create Job records for each target ──────────────────────────────
        created_job_ids: List[str] = []
        for target in request.jobs:
            job = Job(
                id=uuid.uuid4(),
                title=target.title,
                company=target.company,
                description=target.description,
                location=target.location or "Remote",
                requirements=[],
                application_email=target.hr_email,
                source="quick_apply",
            )
            db.add(job)
            created_job_ids.append(str(job.id))

        db.commit()
        logger.info(f"Created {len(created_job_ids)} job records")

        # ── Phase 1: generate documents ──────────────────────────────────────
        batch_id = str(uuid.uuid4())
        orchestrator = ApplicationOrchestrator(db)

        generated_raw = orchestrator.generate_all_documents(
            user_id=request.user_id,
            job_ids=created_job_ids,
            batch_id=batch_id,
        )

        successful = [g for g in generated_raw if g.get("success")]
        generated_info = [
            GeneratedApplicationInfo(
                job_id=g["job_id"],
                job_title=g.get("job_title"),
                company=g.get("company"),
                success=g.get("success", False),
                selected_projects=g.get("selected_projects"),
                resume_path=g.get("resume_path"),
                cover_letter_path=g.get("cover_letter_path"),
                output_dir=g.get("output_dir"),
                error=g.get("error"),
            )
            for g in generated_raw
        ]

        # ── Phase 2: send emails in background ──────────────────────────────
        if successful:
            background_tasks.add_task(
                send_applications_with_gaps,
                successful,
                request.send_gap_minutes,
            )

        return BulkApplyResponse(
            batch_id=batch_id,
            status="sending_in_progress" if successful else "generation_failed",
            total_jobs=len(request.jobs),
            docs_generated=len(successful),
            send_gap_minutes=request.send_gap_minutes,
            generated=generated_info,
            message=(
                f"Documents generated for {len(successful)}/{len(request.jobs)} jobs. "
                f"Emails will be sent every {request.send_gap_minutes} minutes in the background."
                if successful
                else "Document generation failed for all jobs. No emails will be sent."
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Quick-apply error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
