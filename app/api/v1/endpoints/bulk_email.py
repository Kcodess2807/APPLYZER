"""API endpoints for bulk email operations."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.schemas.bulk_email import BulkEmailRequest, BulkEmailResponse
from app.services.bulk_email_service import BulkEmailService
from app.services.email_tracker_service import EmailTrackerService
from app.workers.reply_checker import ReplyChecker
from app.workers.followup_scheduler import FollowUpScheduler
from app.core.config import settings

router = APIRouter()


@router.post("/send-bulk-emails", response_model=BulkEmailResponse)
async def send_bulk_emails(request: BulkEmailRequest):
    """
    Send bulk emails to multiple recipients with tracking.

    Each email is:
    - Sent via Gmail API
    - Tracked in Google Sheets with thread_id
    - Monitored for replies
    - Eligible for automated follow-ups
    """
    try:
        logger.info(f"Received bulk email request for {len(request.recipients)} recipients")

        bulk_service = BulkEmailService(settings.SHEETS_SPREADSHEET_ID)

        try:
            bulk_service.tracker_service.create_tracking_sheet()
        except Exception as e:
            logger.warning(f"Could not create tracking sheet: {e}")

        result = await bulk_service.send_bulk_emails(
            recipients=request.recipients,
            subject=request.subject,
            body=request.body,
        )

        return BulkEmailResponse(**result)

    except Exception as e:
        logger.error(f"Error in bulk email endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-replies")
async def check_replies_manual():
    """
    Manually trigger reply checking for tracked emails.

    Checks all emails with status "SENT" for replies and updates their
    status to "REPLIED" if a response is detected.
    """
    try:
        logger.info("Manual reply check triggered")
        checker = ReplyChecker(settings.SHEETS_SPREADSHEET_ID)
        result = await checker.check_replies()
        return {"success": True, "message": "Reply check completed", "details": result}
    except Exception as e:
        logger.error(f"Error checking replies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-followups")
async def send_followups_manual():
    """
    Manually trigger follow-up email sending.

    Sends follow-up emails to recipients who:
    - Have status "SENT" (no reply received)
    - Were sent more than FOLLOWUP_DAYS_INTERVAL days ago
    - Have followup_count < MAX_FOLLOWUP_COUNT

    Returns:
        - success: Operation status
        - message: Human-readable message
        - details: Statistics about sent/failed follow-ups
        - config: Current follow-up configuration
    """
    try:
        logger.info("Manual follow-up send triggered via API")
        
        # Validate spreadsheet configuration
        if not settings.SHEETS_SPREADSHEET_ID:
            raise HTTPException(
                status_code=500,
                detail="SHEETS_SPREADSHEET_ID not configured. Please set it in .env file."
            )
        
        # Initialize scheduler
        scheduler = FollowUpScheduler(settings.SHEETS_SPREADSHEET_ID)
        
        # Execute follow-up sending
        result = await scheduler.send_followups()
        
        # Build response with detailed information
        sent = result.get('sent', 0)
        errors = result.get('errors', 0)
        
        response = {
            "success": True,
            "message": f"Follow-up cycle completed: {sent} sent, {errors} failed",
            "details": {
                "sent": sent,
                "errors": errors,
                "timestamp": result.get('timestamp', datetime.now().isoformat())
            },
            "config": {
                "followup_interval_days": settings.FOLLOWUP_DAYS_INTERVAL,
                "max_followup_count": settings.MAX_FOLLOWUP_COUNT
            }
        }
        
        logger.info(f"Follow-up send completed: {sent} sent, {errors} errors")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending follow-ups: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send follow-ups: {str(e)}"
        )


@router.get("/tracking-status")
async def get_tracking_status():
    """Get current email tracking statistics."""
    try:
        tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)

        sent_emails = tracker.get_emails_by_status("SENT")
        replied_emails = tracker.get_emails_by_status("REPLIED")
        followup_emails = tracker.get_emails_for_followup()

        total = len(sent_emails) + len(replied_emails)

        return {
            "success": True,
            "statistics": {
                "total_sent": len(sent_emails),
                "total_replied": len(replied_emails),
                "pending_followup": len(followup_emails),
                "reply_rate": f"{(len(replied_emails) / max(total, 1)) * 100:.1f}%",
            },
            "config": {
                "followup_interval_days": settings.FOLLOWUP_DAYS_INTERVAL,
                "max_followup_count": settings.MAX_FOLLOWUP_COUNT
            },
            "eligible_for_followup": [
                {
                    "email": email.get("email"),
                    "subject": email.get("subject"),
                    "sent_at": email.get("sent_at"),
                    "followup_count": email.get("followup_count")
                }
                for email in followup_emails[:5]  # Show first 5
            ]
        }
    except Exception as e:
        logger.error(f"Error getting tracking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-with-attachments", response_model=BulkEmailResponse)
async def send_bulk_emails_with_attachments(
    recipients: str = Form(..., description="Comma-separated list of recipient email addresses"),
    subject: str = Form(..., description="Email subject line"),
    body: str = Form(..., description="Email body (HTML supported)"),
    attachments: List[UploadFile] = File(default=[], description="Files to attach to every email"),
):
    """
    Send bulk emails with file attachments to multiple recipients.

    Accepts multipart/form-data:
    - recipients: comma-separated email addresses
    - subject: email subject
    - body: email body (HTML supported)
    - attachments: one or more files (PDF, DOCX, etc.)

    Each recipient receives the same email with all attachments.
    All sends are tracked in Google Sheets.
    """
    tmp_dir = None
    try:
        recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]
        if not recipient_list:
            raise HTTPException(status_code=400, detail="At least one recipient email is required")

        # Save uploaded files to a temp directory
        attachment_paths: List[str] = []
        if attachments:
            tmp_dir = tempfile.mkdtemp(prefix="applybot_attachments_")
            for upload in attachments:
                dest = Path(tmp_dir) / upload.filename
                with dest.open("wb") as f:
                    shutil.copyfileobj(upload.file, f)
                attachment_paths.append(str(dest))
            logger.info(f"Saved {len(attachment_paths)} attachment(s) to temp dir")

        bulk_service = BulkEmailService(settings.SHEETS_SPREADSHEET_ID)

        try:
            bulk_service.tracker_service.create_tracking_sheet()
        except Exception as e:
            logger.warning(f"Could not create tracking sheet: {e}")

        result = await bulk_service.send_bulk_emails_with_attachments(
            recipients=recipient_list,
            subject=subject,
            body=body,
            attachment_paths=attachment_paths,
        )

        return BulkEmailResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-with-attachments endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always clean up temp files
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/initialize-tracking")
async def initialize_tracking():
    """
    Initialize the email tracking sheet in Google Sheets.

    Creates the EmailTracking sheet with proper headers if it doesn't exist.
    """
    try:
        tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)
        tracker.create_tracking_sheet()
        return {"success": True, "message": "Email tracking sheet initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


