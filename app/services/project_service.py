"""Project service for managing user projects."""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.models.project import Project
from app.services.ai_service import AIService
from loguru import logger


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    def create_project(self, project_data: Dict[str, Any]) -> Project:
        """Create a new project."""
        # Handle achievements data format
        achievements_data = project_data.get("achievments", [])
        if isinstance(achievements_data, dict):
            achievements_list = []
            for key, value in achievements_data.items():
                if isinstance(value, list):
                    achievements_list.extend(value)
                else:
                    achievements_list.append(f"{key}: {value}")
        else:
            achievements_list = achievements_data if isinstance(achievements_data, list) else []
        
        # Convert user_id to UUID if it's a string
        user_id = project_data["user_id"]
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        # Generate project ID if not provided
        project_id = project_data.get("id")
        if project_id:
            if isinstance(project_id, str):
                project_id = uuid.UUID(project_id)
        else:
            project_id = uuid.uuid4()
        
        project = Project(
            id=project_id,
            user_id=user_id,
            title=project_data["title"],
            description=project_data["description"],
            project_type=project_data.get("category"),
            category=project_data.get("category"),
            technologies=project_data.get("technologies", []),
            achievements=achievements_list,
            skills_demonstrated=project_data.get("skills_demonstrated", []),
            project_url=project_data.get("project_url") or project_data.get("url")
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def get_user_projects(
        self, 
        user_id: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Project]:
        """Get all projects for a user with optional filters."""
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        query = self.db.query(Project).filter(Project.user_id == user_id)
        
        if filters:
            if "project_type" in filters:
                query = query.filter(Project.project_type == filters["project_type"])
            if "technology" in filters:
                query = query.filter(Project.technologies.contains([filters["technology"]]))
        
        return query.offset(offset).limit(limit).all()
    
    def get_project_by_id(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get a specific project by ID and user ID."""
        # Convert IDs to UUID if they're strings
        if isinstance(project_id, str):
            project_id = uuid.UUID(project_id)
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        return self.db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id
        ).first()
    
    def update_project(
        self, 
        project_id: str, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Project]:
        """Update an existing project."""
        project = self.get_project_by_id(project_id, user_id)
        
        if not project:
            return None
        
        for key, value in update_data.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Delete a project."""
        project = self.get_project_by_id(project_id, user_id)
        
        if not project:
            return False
        
        self.db.delete(project)
        self.db.commit()
        
        return True
    
    def select_relevant_projects_for_job(
        self,
        user_id: str,
        job_description: str,
        job_title: str,
        max_projects: int = 3
    ) -> List[Project]:
        """
        Select the most relevant projects for a job using AI.
        
        Args:
            user_id: User's ID
            job_description: Job description text
            job_title: Job title/role
            max_projects: Maximum number of projects to return
            
        Returns:
            List of most relevant projects
        """
        # Get all user projects
        all_projects = self.get_user_projects(user_id)
        
        if not all_projects:
            logger.warning(f"No projects found for user {user_id}")
            return []
        
        # Convert to dict format for AI
        projects_data = []
        for project in all_projects:
            projects_data.append({
                "id": str(project.id),
                "title": project.title,
                "description": project.description,
                "technologies": project.technologies or [],
                "skills_demonstrated": project.skills_demonstrated or [],
                "achievements": project.achievements or [],
                "category": project.category,
                "project_url": project.project_url
            })
        
        # Use AI to select relevant projects
        selected_projects_data = self.ai_service.select_relevant_projects(
            projects=projects_data,
            job_description=job_description,
            job_title=job_title,
            max_projects=max_projects
        )
        
        # Convert back to Project objects
        selected_project_ids = [p["id"] for p in selected_projects_data]
        selected_projects = [p for p in all_projects if str(p.id) in selected_project_ids]
        
        # Maintain the order from AI selection
        ordered_projects = []
        for project_data in selected_projects_data:
            for project in selected_projects:
                if str(project.id) == project_data["id"]:
                    ordered_projects.append(project)
                    break
        
        logger.info(f"Selected {len(ordered_projects)} relevant projects for {job_title}")

        return ordered_projects

    def get_projects_for_job(
        self,
        user_id: str,
        job_title: str,
        job_description: str,
        max_projects: int = 3
    ) -> List[Project]:
        """
        Get AI-selected projects for a job, pre-filtered by job_role tags where possible.

        Strategy:
        1. Look for projects the user tagged with this job role (normalised).
        2. If none are tagged, fall back to all user projects.
        3. Run AI ranking on the candidate pool to pick the best N.
        """
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

        # Normalise: "Web Developer" -> "web_developer"
        normalised_role = job_title.lower().replace(" ", "_")

        tagged = self.db.query(Project).filter(
            Project.user_id == uid,
            Project.job_roles.contains([normalised_role])
        ).all()

        candidate_pool = tagged if tagged else self.get_user_projects(user_id)

        if not candidate_pool:
            logger.warning(f"No projects found for user {user_id}")
            return []

        projects_data = [
            {
                "id": str(p.id),
                "title": p.title,
                "description": p.description,
                "technologies": p.technologies or [],
                "skills_demonstrated": p.skills_demonstrated or [],
                "achievements": p.achievements or [],
                "category": p.category,
                "project_url": p.project_url,
            }
            for p in candidate_pool
        ]

        selected_data = self.ai_service.select_relevant_projects(
            projects=projects_data,
            job_description=job_description,
            job_title=job_title,
            max_projects=max_projects,
        )

        # Preserve AI ranking order
        ordered = []
        for sd in selected_data:
            for p in candidate_pool:
                if str(p.id) == sd["id"]:
                    ordered.append(p)
                    break

        logger.info(
            f"Selected {len(ordered)} projects for '{job_title}' "
            f"(pool: {len(candidate_pool)}, role-tagged: {len(tagged)})"
        )
        return ordered
