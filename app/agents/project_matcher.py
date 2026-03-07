#Agent02 – matches user projects to a job's requirements.

from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session

from app.agents.base import AgentResult, BaseAgent
from app.agents.constants import MIN_PROJECT_SCORE, SCORING_WEIGHTS
from app.agents.exceptions import AgentValidationError
from app.agents.schemas import AgentStatus
from app.services.project_service import ProjectService


class ProjectMatcherAgent(BaseAgent):
    """Ranks a user's projects by relevance to a specific job."""

    def __init__(self, db: Session) -> None:
        super().__init__("ProjectMatcherAgent")
        self.db = db
        self.project_service = ProjectService(db)

    # ------------------------------------------------------------------
    # Validation hook
    # ------------------------------------------------------------------

    async def validate_and_parse_input(self, input_data: Any) -> dict[str, Any]:
        required = ("user_id", "job")
        missing = [k for k in required if k not in input_data]
        if missing:
            raise AgentValidationError(
                f"Missing required fields: {missing}", agent_name=self.name
            )
        if "description" not in input_data["job"]:
            raise AgentValidationError(
                "'job.description' is required", agent_name=self.name
            )
        return input_data

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Score and return the top-N projects for the given job.

        Expected input keys::

            {
                "user_id": str,
                "job": {
                    "title": str,
                    "description": str,
                    "required_skills": list[str],
                },
                "max_projects": int,   # default 5
            }
        """
        user_id: str = input_data["user_id"]
        job: dict[str, Any] = input_data["job"]
        max_projects: int = input_data.get("max_projects", 5)

        all_projects = self.project_service.get_user_projects(user_id)

        if not all_projects:
            self.logger.warning(f"No projects found for user_id={user_id!r}")
            return self.create_success_result(
                data={
                    "matched_projects": [],
                    "scores": [],
                    "total_available": 0,
                    "message": "No projects found for this user.",
                }
            )

        ranked = self._rank_projects(all_projects, job)
        top = ranked[:max_projects]

        return self.create_success_result(
            data={
                "matched_projects": [entry["project"].to_dict() for entry in top],
                "scores": [entry["score"] for entry in top],
                "total_available": len(all_projects),
            }
        )

    # ------------------------------------------------------------------
    # Scoring logic
    # ------------------------------------------------------------------

    def _rank_projects(
        self,
        projects: list,
        job: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Score every project against the job and return them sorted desc.

        Projects that score below ``MIN_PROJECT_SCORE`` are excluded so that
        completely unrelated projects never appear in results.
        """
        job_description = job.get("description", "").lower()
        job_title = job.get("title", "").lower()
        required_skills = {s.lower() for s in job.get("required_skills", [])}
        job_title_words = set(job_title.split())

        scored: list[dict[str, Any]] = []

        for project in projects:
            score = self._score_project(
                project, job_description, required_skills, job_title_words
            )
            if score >= MIN_PROJECT_SCORE:
                scored.append({"project": project, "score": score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _score_project(
        self,
        project: Any,
        job_description: str,
        required_skills: set[str],
        job_title_words: set[str],
    ) -> int:
        """Return a cumulative relevance score for a single project."""
        score = 0

        # Technology match (+3 each)
        for tech in (t.lower() for t in (project.technologies or [])):
            if tech in job_description or tech in required_skills:
                score += SCORING_WEIGHTS["technology_match"]

        # Skill match (+2 each)
        for skill in (s.lower() for s in (project.skills_demonstrated or [])):
            if skill in required_skills or skill in job_description:
                score += SCORING_WEIGHTS["skill_match"]

        # Keyword match in project description (+1 each)
        project_desc = (project.description or "").lower()
        for skill in required_skills:
            if skill in project_desc:
                score += SCORING_WEIGHTS["keyword_match"]

        # Title relevance (+2 if any job-title word appears in project title)
        project_title_words = set((project.title or "").lower().split())
        if project_title_words & job_title_words:
            score += SCORING_WEIGHTS["title_relevance"]

        return score