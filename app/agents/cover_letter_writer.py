#Agent04 – crafts a personalised cover letter for a specific job application.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.schemas import CoverLetterTone


class CoverLetterWriterAgent(BaseAgent):
    """Generates structured, tone-aware cover letters."""

    def __init__(self) -> None:
        super().__init__("CoverLetterWriterAgent")

    # ------------------------------------------------------------------
    # Validation hook
    # ------------------------------------------------------------------

    async def validate_and_parse_input(self, input_data: Any) -> dict[str, Any]:
        required = ("user_profile", "job")
        missing = [k for k in required if k not in input_data]
        if missing:
            raise AgentValidationError(
                f"Missing required fields: {missing}", agent_name=self.name
            )
        return input_data

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Generate and return a cover letter for the given job.

        Expected input keys::

            {
                "user_profile": dict,
                "job": dict,
                "resume_data": dict,          # optional
                "matched_projects": list,     # optional
                "tone": str,                  # optional, default "professional"
            }
        """
        user_profile: dict[str, Any] = input_data["user_profile"]
        job: dict[str, Any] = input_data["job"]
        resume_data: dict[str, Any] = input_data.get("resume_data", {})
        projects: list[dict[str, Any]] = input_data.get("matched_projects", [])
        tone: str = input_data.get("tone", CoverLetterTone.PROFESSIONAL)

        cover_letter = self._build_cover_letter(user_profile, job, resume_data, projects, tone)

        return self.create_success_result(
            data={
                "cover_letter": cover_letter,
                "tone": tone,
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    # ------------------------------------------------------------------
    # Cover-letter assembly
    # ------------------------------------------------------------------

    def _build_cover_letter(
        self,
        user_profile: dict[str, Any],
        job: dict[str, Any],
        resume_data: dict[str, Any],
        projects: list[dict[str, Any]],
        tone: str,
    ) -> dict[str, Any]:
        """Assemble all cover-letter sections into a single structured dict."""
        company = job.get("company", "the company")
        position = job.get("title", "the position")
        user_name = user_profile.get("name", "")

        opening = self._write_opening(company, position, tone)
        body = self._write_body(job, projects, resume_data, tone)
        closing = self._write_closing(company, user_name, tone)

        return {
            "header": {
                "name": user_name,
                "email": user_profile.get("email", ""),
                "phone": user_profile.get("phone", ""),
                "date": datetime.now(tz=timezone.utc).strftime("%B %d, %Y"),
            },
            "recipient": {
                "company": company,
                "position": position,
            },
            "content": {
                "opening": opening,
                "body": body,
                "closing": closing,
            },
            "full_text": f"{opening}\n\n{body}\n\n{closing}",
        }

    # ------------------------------------------------------------------
    # Section writers (AI stubs – replace with LLM calls)
    # ------------------------------------------------------------------

    @staticmethod
    def _write_opening(company: str, position: str, tone: str) -> str:
        """Return the opening paragraph.

        TODO: Replace with an LLM prompt that incorporates company research.
        """
        templates: dict[str, str] = {
            CoverLetterTone.ENTHUSIASTIC: (
                f"I am thrilled to apply for the {position} position at {company}. "
                "Your company's innovative approach and commitment to excellence align "
                "perfectly with my professional goals and values."
            ),
            CoverLetterTone.FORMAL: (
                f"I am writing to express my interest in the {position} position at "
                f"{company}. With my background and experience, I believe I would be "
                "a valuable addition to your team."
            ),
        }
        # Default to professional tone if not explicitly mapped.
        return templates.get(
            tone,
            f"I am excited to apply for the {position} role at {company}. "
            "My experience and skills make me a strong candidate for this position.",
        )

    @staticmethod
    def _write_body(
        job: dict[str, Any],
        projects: list[dict[str, Any]],
        resume_data: dict[str, Any],
        tone: str,
    ) -> str:
        """Return the body paragraphs.

        Highlights the most relevant project and top skills.
        TODO: Replace with an LLM prompt that references the full job description.
        """
        paragraphs: list[str] = []

        if projects:
            top = projects[0]
            tech_preview = ", ".join(top.get("technologies", [])[:3])
            paragraphs.append(
                f"In my recent project '{top.get('title', '')}', I demonstrated "
                f"expertise in {tech_preview}. This experience directly aligns with "
                "the requirements for this role."
            )

        skills = resume_data.get("skills", [])[:5]
        if skills:
            paragraphs.append(
                f"My technical skills include {', '.join(skills)}, which I believe "
                "will contribute meaningfully to your team's success."
            )

        return "\n\n".join(paragraphs)

    @staticmethod
    def _write_closing(company: str, user_name: str, tone: str) -> str:
        """Return the closing paragraph and sign-off.

        TODO: Replace with an LLM prompt to vary closing energy by tone.
        """
        return (
            f"I am eager to bring my skills and enthusiasm to {company} and contribute "
            "to your team's continued success. Thank you for considering my application. "
            "I look forward to the opportunity to discuss how I can add value to your "
            f"organisation.\n\nSincerely,\n{user_name}"
        )