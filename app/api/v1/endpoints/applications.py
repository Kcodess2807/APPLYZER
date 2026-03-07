"""Job application endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
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
    BatchReviewResponse,
    BatchApplicationPreview,
    BatchApproveRequest,
    BatchRejectRequest,
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
                application_id=g.get("application_id"),
                job_id=g["job_id"],
                job_title=g.get("job_title"),
                company=g.get("company"),
                hr_email=g.get("hr_email"),
                success=g.get("success", False),
                selected_projects=g.get("selected_projects"),
                resume_path=g.get("resume_path"),
                cover_letter_path=g.get("cover_letter_path"),
                output_dir=g.get("output_dir"),
                email_subject=g.get("email_subject"),
                email_body_preview=(g.get("email_body") or "")[:500],
                cover_letter_preview=(g.get("cover_letter") or "")[:500],
                error=g.get("error"),
            )
            for g in generated_raw
        ]

        # ── Phase 2 is gated behind human approval ───────────────────────────
        # Call POST /applications/batches/{batch_id}/approve to send emails.

        return BulkApplyResponse(
            batch_id=batch_id,
            status="pending_approval" if successful else "generation_failed",
            total_jobs=len(request.job_ids),
            docs_generated=len(successful),
            send_gap_minutes=request.send_gap_minutes,
            generated=generated_info,
            review_url=f"/api/v1/applications/batches/{batch_id}",
            message=(
                f"Documents generated for {len(successful)}/{len(request.job_ids)} jobs. "
                f"Review at /api/v1/applications/batches/{batch_id} then POST .../approve to send."
                if successful
                else "Document generation failed for all jobs."
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
            Application.profile_id == str(user_id)
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
                application_id=g.get("application_id"),
                job_id=g["job_id"],
                job_title=g.get("job_title"),
                company=g.get("company"),
                hr_email=g.get("hr_email"),
                success=g.get("success", False),
                selected_projects=g.get("selected_projects"),
                resume_path=g.get("resume_path"),
                cover_letter_path=g.get("cover_letter_path"),
                output_dir=g.get("output_dir"),
                email_subject=g.get("email_subject"),
                email_body_preview=(g.get("email_body") or "")[:500],
                cover_letter_preview=(g.get("cover_letter") or "")[:500],
                error=g.get("error"),
            )
            for g in generated_raw
        ]

        # ── Phase 2 is gated behind human approval ───────────────────────────
        # Call POST /applications/batches/{batch_id}/approve to send emails.

        return BulkApplyResponse(
            batch_id=batch_id,
            status="pending_approval" if successful else "generation_failed",
            total_jobs=len(request.jobs),
            docs_generated=len(successful),
            send_gap_minutes=request.send_gap_minutes,
            generated=generated_info,
            review_url=f"/api/v1/applications/batches/{batch_id}",
            message=(
                f"Documents generated for {len(successful)}/{len(request.jobs)} jobs. "
                f"Review at /api/v1/applications/batches/{batch_id} then POST .../approve to send."
                if successful
                else "Document generation failed for all jobs."
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Quick-apply error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Human-in-the-Loop batch review / approve / reject ────────────────────────

def _get_batch_applications(db: Session, batch_id: str) -> List[Application]:
    """Fetch all Application rows belonging to a batch."""
    return (
        db.query(Application)
        .filter(Application.batch_id == uuid.UUID(batch_id))
        .order_by(Application.created_at.asc())
        .all()
    )


@router.get("/batches/{batch_id}", response_model=BatchReviewResponse)
async def review_batch(
    batch_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve all generated applications in a batch for human review.

    Returns full email body, cover letter preview, resume path, and HR email
    so you can decide what to approve or reject before any email is sent.
    """
    try:
        applications = _get_batch_applications(db, batch_id)
        if not applications:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

        previews = []
        for app in applications:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            previews.append(BatchApplicationPreview(
                application_id=str(app.id),
                job_id=str(app.job_id),
                job_title=job.title if job else "Unknown",
                company=job.company if job else "Unknown",
                hr_email=job.application_email if job else None,
                status=app.status,
                email_subject=app.email_subject,
                email_body=app.email_body,
                cover_letter_preview=(app.cover_letter or "")[:800] or None,
                resume_path=app.resume_path,
                cover_letter_path=app.cover_letter_path,
                created_at=app.created_at,
            ))

        pending = sum(1 for a in applications if a.status == "docs_ready")
        return BatchReviewResponse(
            batch_id=batch_id,
            total=len(applications),
            pending_approval=pending,
            applications=previews,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batches/{batch_id}/approve")
async def approve_batch(
    batch_id: str,
    request: BatchApproveRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Approve a batch (or specific applications) and trigger email sending.

    - Leave `application_ids` empty to approve all docs_ready applications.
    - Supply specific `application_ids` to send only those.
    - Emails are dispatched in the background with `send_gap_minutes` between each.
    """
    try:
        applications = _get_batch_applications(db, batch_id)
        if not applications:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

        # Filter to the requested subset (or all docs_ready)
        if request.application_ids:
            id_set = set(request.application_ids)
            to_send = [a for a in applications if str(a.id) in id_set and a.status == "docs_ready"]
        else:
            to_send = [a for a in applications if a.status == "docs_ready"]

        if not to_send:
            raise HTTPException(
                status_code=400,
                detail="No docs_ready applications found in this batch (already sent or rejected?)"
            )

        # Mark as approved (status stays docs_ready until sent; we log approval time)
        now = datetime.now(timezone.utc)
        for app in to_send:
            app.approved_at = now
        db.commit()

        # Build the send payload expected by send_applications_with_gaps
        send_payload = []
        for app in to_send:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            send_payload.append({
                "application_id": str(app.id),
                "hr_email": job.application_email if job else None,
                "email_subject": app.email_subject,
                "email_body": app.email_body,
                "resume_path": app.resume_path,
                "cover_letter_path": app.cover_letter_path,
            })

        background_tasks.add_task(
            send_applications_with_gaps,
            send_payload,
            request.send_gap_minutes,
        )

        logger.info(f"Batch {batch_id}: approved {len(to_send)} applications for sending")
        return {
            "batch_id": batch_id,
            "approved": len(to_send),
            "send_gap_minutes": request.send_gap_minutes,
            "status": "sending_in_progress",
            "message": (
                f"{len(to_send)} emails queued. "
                f"Sending every {request.send_gap_minutes} min in the background."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batches/{batch_id}/reject")
async def reject_batch(
    batch_id: str,
    request: BatchRejectRequest,
    db: Session = Depends(get_db),
):
    """
    Reject a batch (or specific applications) — marks them cancelled, no email sent.

    - Leave `application_ids` empty to reject all docs_ready applications.
    - Supply specific `application_ids` to reject only those.
    """
    try:
        applications = _get_batch_applications(db, batch_id)
        if not applications:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

        if request.application_ids:
            id_set = set(request.application_ids)
            to_reject = [a for a in applications if str(a.id) in id_set and a.status == "docs_ready"]
        else:
            to_reject = [a for a in applications if a.status == "docs_ready"]

        if not to_reject:
            raise HTTPException(
                status_code=400,
                detail="No docs_ready applications to reject in this batch"
            )

        for app in to_reject:
            app.status = "rejected"
            app.rejection_reason = request.reason
            app.rejected_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Batch {batch_id}: rejected {len(to_reject)} applications")
        return {
            "batch_id": batch_id,
            "rejected": len(to_reject),
            "reason": request.reason,
            "status": "rejected",
            "message": f"{len(to_reject)} applications cancelled. No emails will be sent.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting batch {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
