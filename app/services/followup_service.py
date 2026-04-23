"""Follow-up email service — handles both manual and auto follow-up logic."""
import base64
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.services.ai_service import AIService
from app.services.gmail_service import GmailService


class FollowUpService:
    """Handles scheduling and sending of follow-up emails, backed by the DB."""

    def __init__(self, db: Session, user_id: str = None):
        self.db = db
        self.user_id = user_id
        self.ai = AIService()

    # ── Scheduling ─────────────────────────────────────────────────────────────

    def schedule_auto_followup(self, application_id: str, after_minutes: int) -> Application:
        """
        Set follow_up_scheduled_at = email_sent_at + after_minutes.
        The background worker will fire the follow-up when that time passes.
        """
        app = self._get_app(application_id)

        if not app.email_sent_at:
            raise ValueError("Application email has not been sent yet — cannot schedule follow-up")

        app.follow_up_scheduled_at = app.email_sent_at + timedelta(minutes=after_minutes)
        self.db.commit()
        self.db.refresh(app)
        logger.info(
            f"Auto follow-up scheduled for application {application_id} "
            f"at {app.follow_up_scheduled_at} ({after_minutes} min after send)"
        )
        return app

    def cancel_auto_followup(self, application_id: str) -> Application:
        """Clear a pending auto follow-up schedule."""
        app = self._get_app(application_id)
        app.follow_up_scheduled_at = None
        self.db.commit()
        self.db.refresh(app)
        return app

    # ── Sending ────────────────────────────────────────────────────────────────

    def send_followup(
        self,
        application_id: str,
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a follow-up email for an application.
        Works for both manual triggers and the background worker.

        Raises ValueError for business-rule violations (already replied,
        max follow-ups reached, no thread, etc.) so the caller can return
        a clean 400/409 instead of a 500.
        """
        app = self._get_app(application_id)

        # ── Guard rails ────────────────────────────────────────────────────────
        if app.reply_received:
            raise ValueError("A reply has already been received — no follow-up needed")

        if not app.gmail_thread_id:
            raise ValueError("No Gmail thread found — was the application email sent via Gmail?")

        max_followups = settings.MAX_FOLLOWUP_COUNT
        if app.followup_count >= max_followups:
            raise ValueError(
                f"Maximum follow-ups ({max_followups}) already sent for this application"
            )

        # ── Build content ──────────────────────────────────────────────────────
        job = app.job
        original_subject = app.email_subject or f"Application - {job.title} at {job.company}"

        sent_ts = app.email_sent_at or app.created_at
        days_since = max(
            1,
            (datetime.now(timezone.utc) - sent_ts.replace(tzinfo=timezone.utc)).days,
        )

        body = custom_message or self.ai.generate_followup_email(
            original_subject=original_subject,
            job_title=job.title,
            company_name=job.company,
            followup_count=app.followup_count + 1,
            user_name="",
            days_since_sent=days_since,
        )

        to_email = job.hr_email or ""
        if not to_email:
            raise ValueError(f"No HR email on record for job '{job.title}' at '{job.company}'")

        # ── Send ───────────────────────────────────────────────────────────────
        result = self._send_in_thread(
            to=to_email,
            subject=f"Re: {original_subject}",
            body=body,
            thread_id=app.gmail_thread_id,
        )

        if result.get("success"):
            app.followup_count += 1
            app.last_followup_at = datetime.now(timezone.utc)
            app.status = "follow_up_sent"
            app.follow_up_scheduled_at = None  # clear pending schedule
            self.db.commit()
            logger.info(
                f"Follow-up #{app.followup_count} sent for application {application_id} "
                f"to {to_email}"
            )

        return result

    # ── Background worker helpers ───────────────────────────────────────────────

    def get_due_followups(self) -> List[Application]:
        """
        Return applications whose auto follow-up is now due:
          - follow_up_scheduled_at <= now
          - no reply received yet
          - below the max follow-up cap
          - email was actually sent (has a gmail_thread_id)
        """
        now = datetime.now(timezone.utc)
        return (
            self.db.query(Application)
            .filter(
                Application.follow_up_scheduled_at <= now,
                Application.reply_received.is_(False),
                Application.followup_count < settings.MAX_FOLLOWUP_COUNT,
                Application.gmail_thread_id.isnot(None),
                Application.status.in_(["sent", "no_response"]),
            )
            .all()
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_app(self, application_id: str) -> Application:
        app = (
            self.db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )
        if not app:
            raise ValueError(f"Application {application_id} not found")
        return app

    def _send_in_thread(
        self, to: str, subject: str, body: str, thread_id: str
    ) -> Dict[str, Any]:
        """Send a reply in an existing Gmail thread."""
        try:
            gmail = GmailService(user_id=self.user_id)
            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject
            message.attach(MIMEText(body, "html"))
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            sent = gmail.service.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": thread_id},
            ).execute()

            return {
                "success": True,
                "message_id": sent.get("id"),
                "thread_id": sent.get("threadId"),
            }
        except Exception as e:
            logger.error(f"Failed to send follow-up in thread {thread_id}: {e}")
            return {"success": False, "error": str(e)}
