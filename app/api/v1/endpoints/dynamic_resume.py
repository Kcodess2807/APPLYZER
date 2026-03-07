"""API endpoints for dynamic resume generation."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from pathlib import Path
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.services.dynamic_resume_generator import dynamic_resume_generator
from app.services.profile_service import ProfileService
from app.services.project_service import ProjectService

router = APIRouter()


class DynamicResumeRequest(BaseModel):
    """Request model for dynamic resume generation."""
    user_id: str
    target_role: str
    use_ai_selection: bool = True
    output_format: str = "pdf"  # "pdf" or "tex"


class RoleListResponse(BaseModel):
    """Response model for available roles."""
    roles: List[str]


@router.get("/available-roles", response_model=RoleListResponse)
async def get_available_roles():
    """
    Get list of available job roles for resume generation.

    Returns list of roles with pre-defined project templates.
    """
    try:
        roles = dynamic_resume_generator.get_available_roles()
        return RoleListResponse(roles=roles)
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_dynamic_resume(
    request: DynamicResumeRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a dynamic resume with role-specific projects.

    This endpoint:
    1. Gets user profile from database
    2. Uses AI to select most relevant projects for the target role
    3. Generates LaTeX file with selected projects
    4. Compiles to PDF (if pdflatex is available)
    5. Returns file paths and metadata

    The Projects section is dynamically adapted based on the target role.
    """
    try:
        logger.info(f"Generating resume for user {request.user_id}, role: {request.target_role}")

        profile = ProfileService(db).get_profile_as_dict(request.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"User {request.user_id} not found")

        # Load user's actual projects from DB (featured first, fall back to all)
        projects_qs = ProjectService(db).get_user_projects(
            request.user_id, featured_only=True
        ) or ProjectService(db).get_user_projects(request.user_id)
        user_projects_data = [p.to_dict() for p in projects_qs] if projects_qs else None

        result = dynamic_resume_generator.generate_resume(
            user_data=profile,
            target_role=request.target_role,
            user_projects=user_projects_data if user_projects_data else None,
            use_ai_selection=request.use_ai_selection,
            output_format=request.output_format,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Resume generation failed"))

        download_file = result.get("pdf_path") or result.get("tex_path")
        download_url = (
            f"/api/v1/dynamic-resume/download/{Path(download_file).name}"
            if download_file
            else None
        )

        return {
            "success": True,
            "message": "Resume generated successfully",
            "resume_id": result.get("resume_id"),
            "target_role": result.get("target_role"),
            "pdf_path": result.get("pdf_path"),
            "tex_path": result.get("tex_path"),
            "selected_projects": result.get("selected_projects"),
            "generation_method": result.get("generation_method"),
            "download_url": download_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dynamic resume generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_resume(filename: str):
    """
    Download generated resume file (PDF or TEX).

    Args:
        filename: Name of the file to download

    Returns:
        File response with the resume
    """
    try:
        # Sanitise filename — reject any path traversal attempts.
        safe_name = Path(filename).name  # strips leading dirs
        if safe_name != filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        base_dir = Path("generated/resumes").resolve()
        file_path = (base_dir / safe_name).resolve()

        # Ensure the resolved path is still inside the allowed directory.
        if not str(file_path).startswith(str(base_dir)):
            raise HTTPException(status_code=400, detail="Invalid filename")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Resume file not found")

        if safe_name.endswith(".pdf"):
            media_type = "application/pdf"
        elif safe_name.endswith(".tex"):
            media_type = "application/x-tex"
        else:
            media_type = "application/octet-stream"

        return FileResponse(path=str(file_path), media_type=media_type, filename=safe_name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to download resume")


@router.post("/generate-quick")
async def generate_quick_resume(
    target_role: str,
    user_name: str = "John Doe",
    user_email: str = "john@example.com",
):
    """
    Quick resume generation without user account (demo/testing).

    Uses template projects for the specified role.
    """
    try:
        user_data = {
            "full_name": user_name,
            "email": user_email,
            "phone": "+1234567890",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "github_url": "https://github.com/johndoe",
            "experience_years": "5+",
            "primary_skills": ["Python", "JavaScript", "React"],
            "skills": [
                {"category": "Programming Languages", "items": ["Python", "JavaScript", "TypeScript"]},
                {"category": "Frameworks", "items": ["React", "Node.js", "FastAPI"]},
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University Name",
                    "year": "2015 - 2019",
                    "coursework": "Data Structures, Algorithms, Machine Learning",
                }
            ],
            "experience": [
                {
                    "role": "Software Engineer",
                    "company": "Tech Company",
                    "location": "San Francisco, CA",
                    "duration": "2020 - Present",
                    "achievements": [
                        "Led development of major features",
                        "Improved system performance by 40%",
                    ],
                }
            ],
            "extra_curricular": [],
            "leadership": [],
        }

        result = dynamic_resume_generator.generate_resume(
            user_data=user_data,
            target_role=target_role,
            user_projects=None,
            use_ai_selection=False,
            output_format="pdf",
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Resume generation failed"))

        download_file = result.get("pdf_path") or result.get("tex_path")
        download_url = (
            f"/api/v1/dynamic-resume/download/{Path(download_file).name}"
            if download_file
            else None
        )

        return {
            "success": True,
            "message": "Quick resume generated successfully",
            "resume_id": result.get("resume_id"),
            "target_role": result.get("target_role"),
            "pdf_path": result.get("pdf_path"),
            "tex_path": result.get("tex_path"),
            "selected_projects": result.get("selected_projects"),
            "download_url": download_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick resume generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
