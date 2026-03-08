"""Two-phase bulk job application orchestrator.

Phase 1 (blocking)  – generate all documents for every selected job.
Phase 2 (background) – send emails one by one with a configurable gap
                        to avoid spam filters.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import asyncio
import shutil
import uuid

from sqlalchemy.orm import Session
from loguru import logger

from app.models.application import Application
from app.models.job import Job
from app.services.cold_dm_generator import ColdDMGenerator
from app.services.ai_service import AIService
from app.services.dynamic_resume_generator import dynamic_resume_generator
from app.services.profile_service import ProfileService
from app.services.project_service import ProjectService


# ── helpers ──────────────────────────────────────────────────────────────────

def _projects_to_dicts(projects) -> List[Dict[str, Any]]:
    return [
        {
            "title": p.title,
            "description": p.description,
            "technologies": p.tech_stack or [],
            "achievements": p.resume_bullets or [],
            "project_url": p.github_repo_url,
        }
        for p in projects
    ]


def _generate_cover_letter(
    ai_service: AIService,
    user_data: Dict[str, Any],
    job_data: Dict[str, Any],
    selected_projects: List[Dict[str, Any]],
) -> str:
    """Generate cover letter via AI, with a plain-text fallback."""
    project_lines = "\n".join(
        f"- {p['title']}: {p['description']}" for p in selected_projects
    ) or "No specific projects provided."

    prompt = f"""Write a professional cover letter for:
Job Title: {job_data.get('title')}
Company: {job_data.get('company')}
Job Description: {job_data.get('description', '')}

Applicant: {user_data.get('full_name')}
Summary: {user_data.get('professional_summary', '')}
Relevant Projects:
{project_lines}

Requirements: professional tone, 3-4 paragraphs, no contact info block.
Write the cover letter now:"""

    messages = [
        {
            "role": "system",
            "content": "You are an expert cover letter writer for technical positions.",
        },
        {"role": "user", "content": prompt},
    ]

    content = ai_service._call_groq_api(messages, temperature=0.7)

    if content:
        header = (
            f"{user_data.get('full_name', '')}\n"
            f"{user_data.get('email', '')}\n"
            f"{user_data.get('phone', '')}\n\n"
            f"{datetime.now().strftime('%B %d, %Y')}\n\n"
        )
        return header + content

    # Fallback template
    return (
        f"{user_data.get('full_name', '')}\n"
        f"{user_data.get('email', '')}\n\n"
        f"{datetime.now().strftime('%B %d, %Y')}\n\n"
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my interest in the {job_data.get('title')} position "
        f"at {job_data.get('company')}.\n\n"
        f"{user_data.get('professional_summary', '')}\n\n"
        f"Thank you for considering my application.\n\n"
        f"Sincerely,\n{user_data.get('full_name', '')}\n"
    )


# ── background send task ──────────────────────────────────────────────────────

async def send_applications_with_gaps(
    applications: List[Dict[str, Any]],
    send_gap_minutes: int = 7,
    user_id: str = None,
) -> None:
    """
    Background task: send each prepared application email with a gap in between.
    Creates its own DB session since the request session will have closed.
    """
    from app.services.gmail_service import GmailService
    from app.services.email_tracker_service import EmailTrackerService
    from app.core.config import settings
    from app.database.base import SessionLocal

    logger.info(
        f"Background send started — {len(applications)} applications, "
        f"{send_gap_minutes} min gap"
    )

    for i, app_data in enumerate(applications):
        if i > 0:
            logger.info(f"Waiting {send_gap_minutes} min before next email...")
            await asyncio.sleep(send_gap_minutes * 60)

        application_id = app_data.get("application_id")
        hr_email = app_data.get("hr_email")

        if not hr_email:
            logger.warning(f"No HR email for application {application_id}, skipping")
            continue

        try:
            gmail = GmailService(user_id)
            attachments = [
                p for p in [app_data.get("resume_path"), app_data.get("cover_letter_path")]
                if p and Path(p).exists()
            ]

            result = gmail.send_email(
                to=hr_email,
                subject=app_data["email_subject"],
                body_html=app_data["email_body"],
                attachments=attachments or None,
            )

            db = SessionLocal()
            try:
                application = db.query(Application).filter(
                    Application.id == uuid.UUID(application_id)
                ).first()

                if result.get("success"):
                    logger.info(f"✓ Sent application to {hr_email}")

                    if application:
                        application.status = "sent"
                        application.gmail_message_id = result.get("message_id")
                        application.gmail_thread_id = result.get("thread_id")
                        application.email_sent_at = datetime.now()
                        application.sent_at = datetime.now()
                        db.commit()

                    # Track in Google Sheets
                    try:
                        tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)
                        tracker.add_email_tracking(
                            email=hr_email,
                            subject=app_data["email_subject"],
                            thread_id=result.get("thread_id"),
                            message_id=result.get("message_id"),
                            status="SENT",
                        )
                    except Exception as sheets_err:
                        logger.warning(f"Sheets tracking failed: {sheets_err}")

                else:
                    logger.error(f"✗ Failed to send to {hr_email}: {result.get('error')}")
                    if application:
                        application.status = "send_failed"
                        db.commit()
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error sending application {application_id}: {e}")


# ── orchestrator ──────────────────────────────────────────────────────────────

class ApplicationOrchestrator:
    """Orchestrate the two-phase bulk job application workflow."""

    OUTPUT_BASE = Path("generated")

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.cold_dm_gen = ColdDMGenerator()

    # ── public API ────────────────────────────────────────────────────────────

    def generate_all_documents(
        self,
        user_id: str,
        job_ids: List[str],
        batch_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Generate resume, cover letter, and cold DM for every job.
        Returns a list of application data dicts (one per job) ready for Phase 2.
        """
        profile = ProfileService(self.db).get_profile_as_dict(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        # Remove projects from profile — we inject AI-selected ones per job
        profile.pop("projects", None)

        results = []
        for job_id in job_ids:
            try:
                app_data = self._generate_for_job(
                    user_id=user_id,
                    profile=profile,
                    job_id=job_id,
                    batch_id=batch_id,
                )
                results.append(app_data)
                logger.info(f"✓ Docs generated for job {job_id}")
            except Exception as e:
                logger.error(f"✗ Failed to generate docs for job {job_id}: {e}")
                results.append({
                    "job_id": job_id,
                    "success": False,
                    "error": str(e),
                })

        return results

    # ── internals ─────────────────────────────────────────────────────────────

    def _generate_for_job(
        self,
        user_id: str,
        profile: Dict[str, Any],
        job_id: str,
        batch_id: str,
    ) -> Dict[str, Any]:
        """Generate all documents for one job and create an Application record."""
        job = self.db.query(Job).filter(
            Job.id == uuid.UUID(job_id)
        ).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        hr_email = job.application_email
        job_data = {
            "title": job.title,
            "company": job.company,
            "description": job.description or "",
            "requirements": job.requirements or [],
        }

        # Output directory: generated/{user_id}/{job_id}/
        out_dir = self.OUTPUT_BASE / user_id / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # ── 1. AI project selection ───────────────────────────────────────────
        project_service = ProjectService(self.db)
        selected_projects_orm = project_service.get_projects_for_job(
            profile_id=user_id,
            job_title=job.title,
            job_description=job.description or job.title,
            max_projects=3,
        )
        selected_projects = _projects_to_dicts(selected_projects_orm)
        logger.info(f"Selected {len(selected_projects)} projects for '{job.title}'")

        # ── 2. Generate resume (LaTeX → PDF) ─────────────────────────────────
        resume_path = self._generate_resume(profile, job.title, selected_projects, out_dir)

        # ── 3. Generate cover letter ─────────────────────────────────────────
        cover_letter_path = self._generate_cover_letter(
            profile, job_data, selected_projects, out_dir
        )

        # ── 4. Generate cold DM / email body ─────────────────────────────────
        email_body_html = self.cold_dm_gen.generate(
            user_profile=profile,
            job_data=job_data,
            tone="professional",
        )
        email_body_path = out_dir / "email_body.html"
        email_body_path.write_text(email_body_html, encoding="utf-8")

        email_subject = f"Application for {job.title} at {job.company}"

        # ── 5. Create Application DB record ──────────────────────────────────
        application = Application(
            id=uuid.uuid4(),
            profile_id=str(user_id),
            job_id=job.id,
            batch_id=uuid.UUID(batch_id),
            status="docs_ready",
            resume_path=str(resume_path) if resume_path else None,
            cover_letter_path=str(cover_letter_path) if cover_letter_path else None,
            email_subject=email_subject,
            email_body=email_body_html,
        )
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)

        return {
            "success": True,
            "application_id": str(application.id),
            "job_id": job_id,
            "job_title": job.title,
            "company": job.company,
            "hr_email": hr_email,
            "email_subject": email_subject,
            "email_body": email_body_html,
            "resume_path": str(resume_path) if resume_path else None,
            "cover_letter_path": str(cover_letter_path) if cover_letter_path else None,
            "email_body_path": str(email_body_path),
            "selected_projects": [p["title"] for p in selected_projects],
            "output_dir": str(out_dir),
        }

    def _generate_resume(
        self,
        profile: Dict[str, Any],
        job_title: str,
        selected_projects: List[Dict[str, Any]],
        out_dir: Path,
    ) -> Optional[Path]:
        """Generate LaTeX resume and move it to out_dir."""
        try:
            result = dynamic_resume_generator.generate_resume(
                user_data=profile,
                target_role=job_title,
                user_projects=selected_projects if selected_projects else None,
                use_ai_selection=False,   # already selected above
                output_format="pdf",
            )

            if not result.get("success"):
                logger.warning(f"Resume generation failed: {result.get('error')}")
                return None

            # Move the generated file into the per-job directory
            src = result.get("pdf_path") or result.get("tex_path")
            if src and Path(src).exists():
                dest = out_dir / "resume.pdf" if src.endswith(".pdf") else out_dir / "resume.tex"
                shutil.move(src, dest)
                return dest

            return None
        except Exception as e:
            logger.error(f"Resume generation error: {e}")
            return None

    def _generate_cover_letter(
        self,
        profile: Dict[str, Any],
        job_data: Dict[str, Any],
        selected_projects: List[Dict[str, Any]],
        out_dir: Path,
    ) -> Optional[Path]:
        """Generate AI cover letter and save to out_dir."""
        try:
            content = _generate_cover_letter(
                self.ai_service, profile, job_data, selected_projects
            )
            dest = out_dir / "cover_letter.txt"
            dest.write_text(content, encoding="utf-8")
            return dest
        except Exception as e:
            logger.error(f"Cover letter generation error: {e}")
            return None
