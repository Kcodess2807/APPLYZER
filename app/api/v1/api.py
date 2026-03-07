"""API router configuration - aggregates all endpoint routers."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    jobs,
    users,
    projects,
    resume,
    cover_letters,
    project_matching,
    workflow,
    review,
    test_generation,
    skills,
    education,
    experiences,
    profile,
    gmail,
    sheets,
    applications,
    bulk_email,
    ai_features,
    dynamic_resume,
    resume_parser
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(education.router, prefix="/education", tags=["education"])
api_router.include_router(experiences.router, prefix="/experiences", tags=["experiences"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(gmail.router, prefix="/gmail", tags=["gmail"])
api_router.include_router(sheets.router, prefix="/sheets", tags=["sheets"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(bulk_email.router, prefix="/bulk-email", tags=["bulk-email"])
api_router.include_router(ai_features.router, prefix="/ai", tags=["ai-features"])
api_router.include_router(dynamic_resume.router, prefix="/dynamic-resume", tags=["dynamic-resume"])
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(cover_letters.router, prefix="/cover-letters", tags=["cover-letters"])
api_router.include_router(project_matching.router, prefix="/match", tags=["project-matching"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(review.router, prefix="/review", tags=["review"])
api_router.include_router(test_generation.router, prefix="/test", tags=["testing"])
api_router.include_router(resume_parser.router, prefix="/profile", tags=["resume-parser"])