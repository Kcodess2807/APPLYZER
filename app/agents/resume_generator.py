#Agent03 generates a tailored resume from a user profile and matched projects.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.agents.exceptions import AgentValidationError


class ResumeGeneratorAgent(BaseAgent):
    """Builds a structured, job-tailored resume from user profile data."""

    def __init__(self) -> None:
        super().__init__("ResumeGeneratorAgent")

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
        """Build and return a formatted resume.

        Expected input keys::

            {
                "user_profile": dict,
                "job": dict,
                "matched_projects": list[dict],   # default []
                "template": str,                  # default "standard"
            }
        """
        user_profile: dict[str, Any] = input_data["user_profile"]
        job: dict[str, Any] = input_data["job"]
        projects: list[dict[str, Any]] = input_data.get("matched_projects", [])
        template: str = input_data.get("template", "standard")

        resume_data = self._build_resume_data(user_profile, job, projects)
        formatted_resume = self._apply_template(resume_data, template)

        return self.create_success_result(
            data={
                "resume": formatted_resume,
                "resume_data": resume_data,
                "template_used": template,
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    # ------------------------------------------------------------------
    # Data assembly
    # ------------------------------------------------------------------

    def _build_resume_data(
        self,
        user_profile: dict[str, Any],
        job: dict[str, Any],
        projects: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble a structured resume dict from the available inputs."""
        job_skills = self._extract_skills_from_job(job)
        ordered_skills = self._prioritise_skills(user_profile.get("skills", []), job_skills)

        return {
            "personal_info": {
                "name": user_profile.get("name", ""),
                "email": user_profile.get("email", ""),
                "phone": user_profile.get("phone", ""),
                "location": user_profile.get("location", ""),
                "linkedin": user_profile.get("linkedin", ""),
                "github": user_profile.get("github", ""),
            },
            "summary": self._generate_summary(user_profile, job),
            "skills": ordered_skills,
            "projects": self._format_projects(projects),
            "experience": user_profile.get("experience", []),
            "education": user_profile.get("education", []),
            "certifications": user_profile.get("certifications", []),
        }

    # ------------------------------------------------------------------
    # Skills helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_skills_from_job(job: dict[str, Any]) -> list[str]:
        """Return the list of explicitly required skills from the job dict.

        TODO: Augment with NLP-based extraction from ``job["description"]``.
        """
        return job.get("required_skills", [])

    @staticmethod
    def _prioritise_skills(
        user_skills: list[str],
        job_skills: list[str],
        max_other: int = 10,
    ) -> list[str]:
        """Put job-matching skills first, then fill with remaining user skills.

        Args:
            user_skills: All skills from the user profile.
            job_skills: Skills explicitly required by the job.
            max_other: Cap on non-matching skills appended after matches.

        Returns:
            Ordered, deduplicated skill list.
        """
        job_skills_lower = {s.lower() for s in job_skills}
        matching = [s for s in user_skills if s.lower() in job_skills_lower]
        other = [s for s in user_skills if s.lower() not in job_skills_lower]
        return matching + other[:max_other]

    # ------------------------------------------------------------------
    # Content generation (AI stubs)
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_summary(user_profile: dict[str, Any], job: dict[str, Any]) -> str:
        """Return a tailored professional summary.

        TODO: Replace stub with an LLM call using job context.
        """
        return user_profile.get("summary", "")

    # ------------------------------------------------------------------
    # Project formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalise project dicts to the resume schema."""
        return [
            {
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "technologies": p.get("technologies", []),
                "achievements": p.get("achievements", []),
                "url": p.get("project_url", ""),
            }
            for p in projects
        ]

    # ------------------------------------------------------------------
    # Template rendering (stub)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_template(resume_data: dict[str, Any], template: str) -> dict[str, Any]:
        """Render resume data using the requested template.

        TODO: Implement PDF, DOCX, and HTML renderers; dispatch by *template*.
        """
        return {"format": template, "content": resume_data}