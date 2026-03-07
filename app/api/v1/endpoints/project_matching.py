"""
Project Matching API Endpoints

ML-powered project matching system with caching and experiment tracking:
- Match user projects to job requirements using TF-IDF + keyword analysis
- Confidence scoring with detailed explanations
- Redis caching for performance optimization
- MLflow experiment tracking for algorithm monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from loguru import logger
import time
import uuid
import os

from app.database.base import get_db
from app.services.matching.TFIDF_matcher import TFIDFProjectMatcher
from app.services.matching.base_matcher import JobContext
from app.services.matching.cache_service import MatchingCacheService
from app.services.job_service import JobService
from app.services.project_service import ProjectService

router = APIRouter()

# Initialize services
matcher = TFIDFProjectMatcher()
cache_service = MatchingCacheService(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    default_ttl=3600  # 1 hour cache
)


class ProjectMatchRequest(BaseModel):
    """Request model for project matching."""
    user_id: uuid.UUID
    algorithm: Optional[str] = "tfidf"
    max_results: Optional[int] = 5
    use_cache: Optional[bool] = True


class ProjectMatchResponse(BaseModel):
    """Response model for project matching."""
    success: bool
    job_id: str
    user_id: str
    algorithm_used: str
    execution_time_ms: float
    cache_hit: bool
    matches: List[Dict[str, Any]]
    explanation: Dict[str, Any]


@router.get("/{job_id}", response_model=ProjectMatchResponse)
async def match_projects_to_job(
    job_id: str,
    user_id: str = Query(..., description="User ID for project matching"),
    algorithm: str = Query("tfidf", description="Matching algorithm to use"),
    max_results: int = Query(5, description="Maximum number of results"),
    use_cache: bool = Query(True, description="Whether to use cached results"),
    db: Session = Depends(get_db)
):
    """
    Match user projects to a specific job using ML algorithms.
    Returns ranked projects with confidence scores and explanations.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Matching projects for job {job_id}, user {user_id}")
        
        # Get job details
        job_service = JobService(db)
        job = job_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create job context
        job_context = JobContext(
            job_id=job_id,
            title=job.title,
            description=job.description or "",
            company=job.company,
            required_skills=job.requirements or [],
            preferred_skills=[],  # Could be enhanced
            category=getattr(job, 'category', 'Software Development'),
            location=job.location
        )
        
        # Check cache first
        cache_hit = False
        cached_results = None
        
        if use_cache:
            cache_key = cache_service.generate_cache_key(
                user_id=user_id,
                job_context=job_context,
                algorithm_name=matcher.get_algorithm_name(),
                algorithm_version=matcher.get_algorithm_version()
            )
            cached_results = cache_service.get_cached_results(cache_key)
            cache_hit = cached_results is not None
        
        if cached_results:
            # Return cached results
            execution_time = (time.time() - start_time) * 1000
            
            return ProjectMatchResponse(
                success=True,
                job_id=job_id,
                user_id=user_id,
                algorithm_used=matcher.get_algorithm_name(),
                execution_time_ms=execution_time,
                cache_hit=True,
                matches=cached_results,
                explanation={
                    "source": "cache",
                    "algorithm": matcher.get_algorithm_name(),
                    "cached_at": cached_results[0].get("cached_at") if cached_results else None
                }
            )
        
        # Get user projects
        project_service = ProjectService(db)
        user_projects = project_service.get_projects_by_user_id(user_id)
        
        if not user_projects:
            return ProjectMatchResponse(
                success=True,
                job_id=job_id,
                user_id=user_id,
                algorithm_used=matcher.get_algorithm_name(),
                execution_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                matches=[],
                explanation={"message": "No projects found for user"}
            )
        
        # Perform matching
        match_results = matcher.match_projects(
            projects=user_projects,
            job_context=job_context,
            max_results=max_results
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        # Convert results to response format
        matches = []
        for result in match_results:
            match_dict = {
                "project_id": result.project.id,
                "project_title": result.project.title,
                "project_description": result.project.description,
                "confidence_score": result.confidence_score,
                "confidence_percentage": round(result.confidence_score * 100, 1),
                "matching_keywords": result.matching_keywords,
                "explanation": result.explanation,
                "similarity_breakdown": result.similarity_breakdown
            }
            matches.append(match_dict)
        
        # Cache results
        if use_cache and match_results:
            cache_service.cache_results(cache_key, match_results)
        
        # Log to MLflow
        _log_matching_experiment(
            job_context=job_context,
            match_results=match_results,
            execution_time=execution_time / 1000,  # Convert to seconds
            user_id=user_id
        )
        
        return ProjectMatchResponse(
            success=True,
            job_id=job_id,
            user_id=user_id,
            algorithm_used=matcher.get_algorithm_name(),
            execution_time_ms=execution_time,
            cache_hit=False,
            matches=matches,
            explanation={
                "algorithm": matcher.get_algorithm_name(),
                "version": matcher.get_algorithm_version(),
                "total_projects_analyzed": len(user_projects),
                "matching_criteria": "TF-IDF similarity + keyword matching + technology alignment"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to match projects")


@router.post("/{job_id}/explain")
async def explain_project_match(
    job_id: str,
    project_id: str = Query(..., description="Project ID to explain"),
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get detailed explanation for why a specific project matches a job."""
    
    try:
        # Get job and project
        job_service = JobService(db)
        project_service = ProjectService(db)
        
        job = job_service.get_job_by_id(job_id)
        project = project_service.get_project_by_id(project_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create job context
        job_context = JobContext(
            job_id=job_id,
            title=job.title,
            description=job.description or "",
            company=job.company,
            required_skills=job.requirements or [],
            preferred_skills=[],
            category=getattr(job, 'category', 'Software Development'),
            location=job.location
        )
        
        # Perform single project match for detailed explanation
        match_results = matcher.match_projects(
            projects=[project],
            job_context=job_context,
            max_results=1
        )
        
        if not match_results:
            return {
                "success": False,
                "message": "No match found for this project"
            }
        
        result = match_results[0]
        
        return {
            "success": True,
            "job_title": job.title,
            "project_title": project.title,
            "confidence_score": result.confidence_score,
            "confidence_percentage": round(result.confidence_score * 100, 1),
            "detailed_explanation": result.explanation,
            "matching_keywords": result.matching_keywords,
            "similarity_breakdown": result.similarity_breakdown,
            "recommendations": _generate_improvement_recommendations(result, job_context)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining project match: {e}")
        raise HTTPException(status_code=500, detail="Failed to explain match")


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache performance statistics."""
    
    try:
        stats = cache_service.get_cache_stats()
        
        return {
            "success": True,
            "cache_stats": stats,
            "mlflow_experiments": len(experiment_tracker.get_experiment_metrics(limit=100))
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")


@router.delete("/cache/{user_id}")
async def invalidate_user_cache(user_id: str):
    """Invalidate all cached results for a specific user."""
    
    try:
        invalidated_count = cache_service.invalidate_user_cache(user_id)
        
        return {
            "success": True,
            "message": f"Invalidated {invalidated_count} cache entries for user {user_id}",
            "invalidated_count": invalidated_count
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.get("/experiments/compare")
async def compare_algorithm_performance():
    """Compare performance of different matching algorithms."""
    
    try:
        comparison = experiment_tracker.compare_algorithms()
        
        return {
            "success": True,
            "algorithm_comparison": comparison,
            "total_experiments": sum(stats['runs'] for stats in comparison.values())
        }
        
    except Exception as e:
        logger.error(f"Error comparing algorithms: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare algorithms")


def _log_matching_experiment(
    job_context: JobContext,
    match_results: List,
    execution_time: float,
    user_id: str
):
    """Log matching experiment to MLflow."""
    
    try:
        # Calculate metrics
        avg_confidence = sum(r.confidence_score for r in match_results) / len(match_results) if match_results else 0
        max_confidence = max(r.confidence_score for r in match_results) if match_results else 0
        min_confidence = min(r.confidence_score for r in match_results) if match_results else 0
        
        # Parameters
        parameters = {
            "max_results": len(match_results),
            "user_id": user_id,
            "job_category": job_context.category or "unknown",
            "required_skills_count": len(job_context.required_skills),
            "job_description_length": len(job_context.description)
        }
        
        # Metrics
        metrics = {
            "average_confidence": avg_confidence,
            "max_confidence": max_confidence,
            "min_confidence": min_confidence,
            "results_count": len(match_results)
        }
        
        # Job context for artifact
        job_data = {
            "job_id": job_context.job_id,
            "title": job_context.title,
            "company": job_context.company,
            "required_skills": job_context.required_skills,
            "category": job_context.category
        }
        
        # Match results for artifact
        results_data = [
            {
                "project_title": r.project.title,
                "confidence_score": r.confidence_score,
                "matching_keywords": r.matching_keywords
            }
            for r in match_results
        ]
        
        experiment_tracker.log_matching_experiment(
            algorithm_name=matcher.get_algorithm_name(),
            algorithm_version=matcher.get_algorithm_version(),
            parameters=parameters,
            metrics=metrics,
            job_context=job_data,
            match_results=results_data,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.warning(f"Failed to log MLflow experiment: {e}")


def _generate_improvement_recommendations(match_result, job_context: JobContext) -> List[str]:
    """Generate recommendations for improving project-job match."""
    
    recommendations = []
    
    # Check missing required skills
    missing_skills = set(job_context.required_skills) - set(match_result.matching_keywords)
    if missing_skills:
        recommendations.append(
            f"Consider adding these skills to your project: {', '.join(list(missing_skills)[:3])}"
        )
    
    # Check confidence score
    if match_result.confidence_score < 0.3:
        recommendations.append(
            "This project has low relevance. Consider highlighting more relevant technologies or outcomes."
        )
    elif match_result.confidence_score < 0.6:
        recommendations.append(
            "Good match! Consider emphasizing the matching technologies in your project description."
        )
    else:
        recommendations.append(
            "Excellent match! This project strongly aligns with the job requirements."
        )
    
    return recommendations