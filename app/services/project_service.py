"""GitHub project sync service with LLM enrichment via Groq."""
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from loguru import logger
import requests

from app.models.project import Project
from app.core.config import settings


GITHUB_API_BASE = "https://api.github.com"


class ProjectService:
    """Fetch repos from GitHub, enrich with LLM, persist to DB."""

    def __init__(self, db: Session):
        self.db = db

    # ── DB queries ─────────────────────────────────────────────────────────────

    def get_user_projects(self, profile_id: str, featured_only: bool = False) -> List[Project]:
        """Return all (or featured-only) projects for a profile."""
        pid = str(profile_id)
        query = self.db.query(Project).filter(Project.profile_id == pid)
        if featured_only:
            query = query.filter(Project.is_featured.is_(True))
        return query.all()

    def get_project_by_id(self, project_id: str, profile_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(
            Project.id == uuid.UUID(project_id),
            Project.profile_id == str(profile_id),
        ).first()

    def toggle_featured(self, project_id: str, profile_id: str, is_featured: bool) -> Optional[Project]:
        """Show or hide a project on generated resumes."""
        project = self.get_project_by_id(project_id, profile_id)
        if not project:
            return None
        project.is_featured = is_featured
        project.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(project)
        return project

    # ── GitHub API ─────────────────────────────────────────────────────────────

    def _gh_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        return headers

    def fetch_repos(self, github_username: str) -> List[Dict[str, Any]]:
        """Fetch all public repos for a GitHub user (sorted by recently pushed)."""
        try:
            resp = requests.get(
                f"{GITHUB_API_BASE}/users/{github_username}/repos",
                headers=self._gh_headers(),
                params={"per_page": 100, "sort": "pushed"},
                timeout=15,
            )
            resp.raise_for_status()
            repos = resp.json()
            logger.info(f"Fetched {len(repos)} repos for {github_username}")
            return repos
        except Exception as e:
            logger.error(f"GitHub repos fetch failed for {github_username}: {e}")
            return []

    def fetch_readme(self, github_username: str, repo_name: str) -> Optional[str]:
        """Fetch raw README content. Returns None if repo has no README."""
        try:
            resp = requests.get(
                f"{GITHUB_API_BASE}/repos/{github_username}/{repo_name}/readme",
                headers={**self._gh_headers(), "Accept": "application/vnd.github.v3.raw"},
                timeout=15,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"README fetch failed for {github_username}/{repo_name}: {e}")
            return None

    def fetch_languages(self, github_username: str, repo_name: str) -> List[str]:
        """Return list of languages used in a repo."""
        try:
            resp = requests.get(
                f"{GITHUB_API_BASE}/repos/{github_username}/{repo_name}/languages",
                headers=self._gh_headers(),
                timeout=10,
            )
            resp.raise_for_status()
            return list(resp.json().keys())
        except Exception:
            return []

    # ── LLM enrichment ─────────────────────────────────────────────────────────

    def _enrich_with_llm(
        self,
        repo: Dict[str, Any],
        readme: Optional[str],
        languages: List[str],
    ) -> Dict[str, Any]:
        """Call Groq to extract resume-ready info from a repo. Returns {} on failure."""
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set — skipping LLM enrichment")
            return {}

        readme_excerpt = (readme or "No README available.")[:3000]
        topics_str = ", ".join(repo.get("topics", []))
        langs_str = ", ".join(languages) if languages else "Unknown"

        prompt = (
            "You are a technical resume writer. Analyze this GitHub repository and extract resume-ready information.\n\n"
            f"Repository: {repo.get('name')}\n"
            f"Description: {repo.get('description', 'No description')}\n"
            f"Primary Language: {repo.get('language', 'Unknown')}\n"
            f"All Languages: {langs_str}\n"
            f"Topics: {topics_str}\n"
            f"Stars: {repo.get('stargazers_count', 0)}\n\n"
            f"README (first 3000 chars):\n{readme_excerpt}\n\n"
            'Return ONLY a JSON object with these exact keys:\n'
            '{\n'
            '  "title": "Clean project display name (Title Case, human readable)",\n'
            '  "description": "2-3 sentence resume-quality project description",\n'
            '  "tech_stack": ["technology1", "technology2"],\n'
            '  "features": ["key feature 1", "key feature 2", "key feature 3"],\n'
            '  "resume_bullets": ["Action verb bullet 1", "Action verb bullet 2", "Action verb bullet 3"],\n'
            '  "category": "One of: Web App, API/Backend, ML/AI, Data Pipeline, CLI Tool, Mobile App, DevOps/Infrastructure, Library/Package, Other",\n'
            '  "skills_demonstrated": ["skill1", "skill2", "skill3"]\n'
            '}'
        )

        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a technical resume writer. Return only valid JSON, no explanation.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            if "{" in content and "}" in content:
                start = content.index("{")
                end = content.rindex("}") + 1
                return json.loads(content[start:end])

        except Exception as e:
            logger.error(f"LLM enrichment failed for {repo.get('name')}: {e}")

        return {}

    # ── Sync orchestration ─────────────────────────────────────────────────────

    def sync_projects(self, profile_id: str, github_username: str) -> Dict[str, Any]:
        """
        Full sync pipeline:
          1. Fetch all public repos from GitHub
          2. Skip repos unchanged since last sync
          3. Fetch README + languages for new/changed repos
          4. Enrich with LLM (Groq)
          5. Upsert to DB (unique on profile_id + github_repo_name)
        """
        pid = str(profile_id)
        repos = self.fetch_repos(github_username)

        if not repos:
            return {
                "synced": 0, "skipped": 0, "failed": 0, "total_repos": 0,
                "message": "No public repos found on GitHub",
            }

        synced = skipped = failed = 0

        for repo in repos:
            try:
                repo_name = repo["name"]
                pushed_at = repo.get("pushed_at")
                github_updated = (
                    datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                    if pushed_at else None
                )

                existing = self.db.query(Project).filter(
                    Project.profile_id == pid,
                    Project.github_repo_name == repo_name,
                ).first()

                # Skip if nothing changed on GitHub since last sync
                if existing and existing.last_synced_at and github_updated:
                    if existing.last_synced_at >= github_updated:
                        skipped += 1
                        continue

                readme = self.fetch_readme(github_username, repo_name)
                languages = self.fetch_languages(github_username, repo_name)
                enriched = self._enrich_with_llm(repo, readme, languages)
                now = datetime.now(timezone.utc)

                if existing:
                    existing.github_repo_url = repo.get("html_url", "")
                    existing.primary_language = repo.get("language")
                    existing.github_topics = repo.get("topics", [])
                    existing.github_stars = repo.get("stargazers_count", 0)
                    existing.github_updated_at = github_updated
                    existing.readme_raw = readme
                    existing.last_synced_at = now
                    if enriched:
                        existing.title = enriched.get("title")
                        existing.description = enriched.get("description")
                        existing.tech_stack = enriched.get("tech_stack", [])
                        existing.features = enriched.get("features", [])
                        existing.resume_bullets = enriched.get("resume_bullets", [])
                        existing.category = enriched.get("category")
                        existing.skills_demonstrated = enriched.get("skills_demonstrated", [])
                        existing.llm_processed_at = now
                    existing.updated_at = now
                else:
                    project = Project(
                        id=uuid.uuid4(),
                        profile_id=pid,
                        github_repo_name=repo_name,
                        github_repo_url=repo.get("html_url", ""),
                        primary_language=repo.get("language"),
                        github_topics=repo.get("topics", []),
                        github_stars=repo.get("stargazers_count", 0),
                        github_updated_at=github_updated,
                        readme_raw=readme,
                        last_synced_at=now,
                        title=enriched.get("title"),
                        description=enriched.get("description"),
                        tech_stack=enriched.get("tech_stack", []),
                        features=enriched.get("features", []),
                        resume_bullets=enriched.get("resume_bullets", []),
                        category=enriched.get("category"),
                        skills_demonstrated=enriched.get("skills_demonstrated", []),
                        llm_processed_at=now if enriched else None,
                        is_featured=True,
                    )
                    self.db.add(project)

                self.db.commit()
                synced += 1
                logger.info(f"Synced: {repo_name}")

            except Exception as e:
                logger.error(f"Failed to sync repo {repo.get('name')}: {e}")
                self.db.rollback()
                failed += 1

        return {
            "synced": synced,
            "skipped": skipped,
            "failed": failed,
            "total_repos": len(repos),
            "message": f"Sync complete: {synced} updated, {skipped} unchanged, {failed} failed",
        }

    # ── AI-based project selection for a job ──────────────────────────────────

    def get_projects_for_job(
        self,
        profile_id: str,
        job_title: str,
        job_description: str,
        max_projects: int = 3,
    ) -> List[Project]:
        """Return AI-ranked featured projects best suited to a job."""
        projects = self.get_user_projects(profile_id, featured_only=True)
        if not projects:
            projects = self.get_user_projects(profile_id)
        if not projects:
            return []

        from app.services.ai_service import AIService
        ai = AIService()
        projects_data = [p.to_dict() for p in projects]
        selected_data = ai.select_relevant_projects(
            projects=projects_data,
            job_description=job_description,
            job_title=job_title,
            max_projects=max_projects,
        )
        selected_ids = {d["id"] for d in selected_data}
        ordered = [p for p in projects if str(p.id) in selected_ids]
        return ordered[:max_projects]

    def select_relevant_projects_for_job(
        self,
        user_id: str,
        job_title: str,
        job_description: str,
        max_projects: int = 3,
    ) -> List[Project]:
        """Alias for get_projects_for_job using user_id parameter name."""
        return self.get_projects_for_job(
            profile_id=user_id,
            job_title=job_title,
            job_description=job_description,
            max_projects=max_projects,
        )
