"""
Main job service that orchestrates job fetching and storage.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.services.job_fetcher import JobFetcher
from app.services.job_storage import JobStorageService
from app.services.job_source_config import job_source_manager
from app.database.base import get_db


class JobService:
    """Main service for job operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_service = JobStorageService(db)
        self.fetchers: List[JobFetcher] = job_source_manager.get_enabled_fetchers()
    
    async def fetch_and_store_jobs(
        self, 
        keywords: Optional[List[str]] = None,
        limit_per_source: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch jobs from all configured sources and store them.
        
        Args:
            keywords: Keywords to search for
            limit_per_source: Maximum jobs to fetch per source
            
        Returns:
            Dictionary with fetching results and statistics
        """
        logger.info(f"Starting job fetch with keywords: {keywords}")
        
        results = {
            "total_fetched": 0,
            "total_stored": 0,
            "new_jobs": 0,
            "updated_jobs": 0,
            "sources": {},
            "errors": []
        }
        
        # Fetch from all sources
        for fetcher in self.fetchers:
            source_name = fetcher.get_source_name()
            logger.info(f"Fetching jobs from {source_name}")
            
            try:
                # Fetch jobs from this source
                jobs = await fetcher.fetch_jobs(keywords or [], limit_per_source)
                
                if jobs:
                    # Store jobs in database
                    total_processed, new_jobs, updated_jobs = await self.storage_service.store_jobs(jobs)
                    
                    # Update results
                    results["total_fetched"] += len(jobs)
                    results["total_stored"] += total_processed
                    results["new_jobs"] += new_jobs
                    results["updated_jobs"] += updated_jobs
                    
                    results["sources"][source_name] = {
                        "fetched": len(jobs),
                        "new": new_jobs,
                        "updated": updated_jobs,
                        "status": "success"
                    }
                    
                    logger.info(f"{source_name}: {len(jobs)} fetched, {new_jobs} new, {updated_jobs} updated")
                else:
                    results["sources"][source_name] = {
                        "fetched": 0,
                        "new": 0,
                        "updated": 0,
                        "status": "no_jobs"
                    }
                    logger.warning(f"{source_name}: No jobs found")
                    
            except Exception as e:
                error_msg = f"{source_name} fetch failed: {str(e)}"
                logger.error(error_msg)
                
                results["errors"].append(error_msg)
                results["sources"][source_name] = {
                    "fetched": 0,
                    "new": 0,
                    "updated": 0,
                    "status": "error",
                    "error": str(e)
                }
        
        logger.info(f"Job fetch complete: {results['new_jobs']} new, {results['updated_jobs']} updated")
        return results
    
    def search_jobs(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ):
        """Search jobs with filters."""
        return self.storage_service.search_jobs(
            keywords=keywords,
            location=location,
            company=company,
            limit=limit,
            offset=offset
        )
    
    def get_job_by_id(self, job_id: str):
        """Get a specific job by ID."""
        from app.models.job import Job
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job database statistics."""
        from app.models.job import Job
        from sqlalchemy import func
        
        total_jobs = self.db.query(Job).count()
        
        # Jobs by source
        jobs_by_source = self.db.query(
            Job.source,
            func.count(Job.id).label('count')
        ).group_by(Job.source).all()
        
        # Recent jobs (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_jobs = self.db.query(Job).filter(Job.fetched_at >= week_ago).count()
        
        return {
            "total_jobs": total_jobs,
            "recent_jobs_7_days": recent_jobs,
            "jobs_by_source": {source: count for source, count in jobs_by_source},
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def add_job_fetcher(self, fetcher: JobFetcher):
        """Add a new job fetcher to the service."""
        self.fetchers.append(fetcher)
        logger.info(f"Added job fetcher: {fetcher.get_source_name()}")
    
    def get_available_sources(self) -> List[str]:
        """Get list of available job sources."""
        return [fetcher.get_source_name() for fetcher in self.fetchers]