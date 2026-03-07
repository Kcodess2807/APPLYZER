"""
Projects API endpoints with job matching capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from loguru import logger
import uuid
from datetime import datetime, timezone

from app.database.base import get_db
from app.services.project_service import ProjectService
router = APIRouter()

class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    title: str
    description: str
    technologies: List[str]
    category: str  # e.g., "Web Development", "Machine Learning", "Mobile App"
    project_url: Optional[str] = None  # GitHub, demo link
    achievments: Optional[Dict[str, Any]] = {}  # Performance metrics, user counts, etc.
    skills_demonstrated: Optional[List[str]] = []  # Skills this project showcases
    
class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    category: Optional[str] = None
    project_url: Optional[str] = None
    skills_demonstrated: Optional[List[str]] = None

class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: str
    title: str
    description: str
    technologies: List[str]
    category: str
    project_url: Optional[str]
    skills_demonstrated: List[str]
    relevance_score: Optional[float] = None  # For job matching
    created_at: str
    updated_at: str
    user_id: str


@router.post("/", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    try:
        logger.info(f"Creating project '{request.title}' for user {user_id}")
        
        project_service = ProjectService(db)
        
        project_data = {
            **request.dict(),
            "user_id": user_id,
            "id": str(uuid.uuid4())
        }
        
        project = project_service.create_project(project_data)
        
        return ProjectResponse(
            id=str(project.id),
            title=project.title,
            description=project.description,
            technologies=project.technologies or [],
            category=project.category or "Other",
            project_url=project.project_url,
            skills_demonstrated=project.skills_demonstrated or [],
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            user_id=str(project.user_id)
        )
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

#working properly!!
@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    user_id: str = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    technology: Optional[str] = Query(None, description="Filter by technology"),
    limit: int = Query(50, description="Maximum number of projects to return"),
    offset: int = Query(0, description="Number of projects to skip"),
    db: Session = Depends(get_db)
):
    """Get all projects for a user with optional filtering."""
    try:
        logger.info(f"Fetching projects for user {user_id}")
        
        project_service = ProjectService(db)
        
        filters = {}
        if category:
            filters["category"] = category
        if technology:
            filters["technology"] = technology
            
        projects = project_service.get_user_projects(
            user_id, filters=filters, limit=limit, offset=offset
        )
        
        return [
            ProjectResponse(
                id=str(project.id),
                title=project.title,
                description=project.description,
                technologies=project.technologies or [],
                category=project.category,
                project_url=project.project_url,
                skills_demonstrated=project.skills_demonstrated or [],
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                user_id=str(project.user_id)
            )
            for project in projects
        ]
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific project by ID."""
    try:
        logger.info(f"Fetching project {project_id} for user {user_id}")
        
        project_service = ProjectService(db)
        project = project_service.get_project_by_id(project_id, user_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(
            id=str(project.id),
            title=project.title,
            description=project.description,
            technologies=project.technologies or [],
            category=project.category,
            project_url=project.project_url,
            skills_demonstrated=project.skills_demonstrated or [],
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            user_id=str(project.user_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update an existing project."""
    try:
        logger.info(f"Updating project {project_id} for user {user_id}")
        
        project_service = ProjectService(db)
        
        # Only update fields that are provided
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        project = project_service.update_project(project_id, user_id, update_data)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(
            id=str(project.id),
            title=project.title,
            description=project.description,
            technologies=project.technologies or [],
            category=project.category,
            project_url=project.project_url,
            skills_demonstrated=project.skills_demonstrated or [],
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            user_id=str(project.user_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a project."""
    try:
        logger.info(f"Deleting project {project_id} for user {user_id}")
        
        project_service = ProjectService(db)
        success = project_service.delete_project(project_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "success": True,
            "message": f"Project {project_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@router.get("/categories/list")
async def get_project_categories():
    """Get list of available project categories."""
    categories = [
        "Web Development",
        "Mobile App Development", 
        "Machine Learning",
        "Data Science",
        "DevOps/Infrastructure",
        "Desktop Application",
        "Game Development",
        "API Development",
        "Database Design",
        "UI/UX Design",
        "Blockchain",
        "IoT (Internet of Things)",
        "Computer Vision",
        "Natural Language Processing",
        "Cloud Computing",
        "Cybersecurity",
        "Other"
    ]
    
    return {
        "success": True,
        "categories": categories
    }

@router.get("/technologies/popular")
async def get_popular_technologies():
    """Get list of popular technologies for project tagging."""
    technologies = {
        "Programming Languages": [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", 
            "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin"
        ],
        "Web Frameworks": [
            "React", "Angular", "Vue.js", "Next.js", "Django", "Flask", 
            "FastAPI", "Express.js", "Node.js", "Spring Boot"
        ],
        "Mobile": [
            "React Native", "Flutter", "iOS (Swift)", "Android (Kotlin)", 
            "Xamarin", "Ionic"
        ],
        "Databases": [
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", 
            "SQLite", "Firebase", "DynamoDB"
        ],
        "Cloud & DevOps": [
            "AWS", "Google Cloud", "Azure", "Docker", "Kubernetes", 
            "Jenkins", "GitHub Actions", "Terraform"
        ],
        "Machine Learning": [
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", 
            "OpenCV", "Hugging Face", "MLflow"
        ]
    }
    
    return {
        "success": True,
        "technologies": technologies
    }

@router.post("/bulk-create")
async def bulk_create_projects(
    projects: List[ProjectCreateRequest],
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create multiple projects at once for testing."""
    try:
        logger.info(f"Bulk creating {len(projects)} projects for user {user_id}")
        
        project_service = ProjectService(db)
        created_projects = []
        
        for project_data in projects:
            project_dict = {
                **project_data.dict(),
                "user_id": user_id,
                "id": str(uuid.uuid4())
            }
            
            try:
                project = project_service.create_project(project_dict)
                created_projects.append(project.id)
            except Exception as e:
                logger.warning(f"Failed to create project '{project_data.title}': {e}")
        
        return {
            "success": True,
            "message": f"Successfully created {len(created_projects)} projects",
            "created_project_ids": created_projects,
            "failed_count": len(projects) - len(created_projects)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk project creation: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk creation failed: {str(e)}")
