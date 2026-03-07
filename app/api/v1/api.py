"""API router configuration - aggregates all endpoint routers."""
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import get_current_user
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
    profile,
    gmail,
    sheets,
    applications,
    bulk_email,
    ai_features,
    dynamic_resume,
    resume_parser,
)

api_router = APIRouter()

# Shared auth dependency applied at router level.
# When REQUIRE_AUTH=false (dev default) this is a no-op.
_auth = [Depends(get_current_user)]

# Public routers — no auth required
api_router.include_router(health.router, prefix="/health", tags=["health"])
# Gmail/Sheets OAuth flows must remain public so the browser redirect works.
api_router.include_router(gmail.router, prefix="/gmail", tags=["gmail"])
api_router.include_router(sheets.router, prefix="/sheets", tags=["sheets"])

# Protected routers
api_router.include_router(users.router, prefix="/users", tags=["users"], dependencies=_auth)
api_router.include_router(profile.router, prefix="/profile", tags=["profile"], dependencies=_auth)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"], dependencies=_auth)
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"], dependencies=_auth)
api_router.include_router(applications.router, prefix="/applications", tags=["applications"], dependencies=_auth)
api_router.include_router(bulk_email.router, prefix="/bulk-email", tags=["bulk-email"], dependencies=_auth)
api_router.include_router(ai_features.router, prefix="/ai", tags=["ai-features"], dependencies=_auth)
api_router.include_router(dynamic_resume.router, prefix="/dynamic-resume", tags=["dynamic-resume"], dependencies=_auth)
api_router.include_router(resume.router, prefix="/resume", tags=["resume"], dependencies=_auth)
api_router.include_router(cover_letters.router, prefix="/cover-letters", tags=["cover-letters"], dependencies=_auth)
api_router.include_router(project_matching.router, prefix="/match", tags=["project-matching"], dependencies=_auth)
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"], dependencies=_auth)
api_router.include_router(review.router, prefix="/review", tags=["review"], dependencies=_auth)
api_router.include_router(resume_parser.router, prefix="/profile", tags=["resume-parser"], dependencies=_auth)

# Test/debug endpoints — only registered outside production
if settings.ENVIRONMENT != "production":
    api_router.include_router(test_generation.router, prefix="/test", tags=["testing"])
