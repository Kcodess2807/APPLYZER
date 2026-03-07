"""
Job storage service with deduplication logic.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from app.models.job import Job
from app.schemas.job import JobCreate
from app.database.base import get_db


class JobStorageService:
    """Service for storing and managing job data with deduplication."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def store_jobs(self, jobs: List[JobCreate]) -> Tuple[int, int, int]:
        """
        Store jobs in database with deduplication.
        
        Args:
            jobs: List of JobCreate objects to store
            
        Returns:
            Tuple of (total_processed, new_jobs, updated_jobs)
        """
        if not jobs:
            return 0, 0, 0
        
        total_processed = len(jobs)
        new_jobs = 0
        updated_jobs = 0
        
        logger.info(f"Processing {total_processed} jobs for storage")
        
        for job_data in jobs:
            try:
                existing_job = self._find_duplicate(job_data)
                
                if existing_job:
                    # Update existing job if needed
                    if self._should_update_job(existing_job, job_data):
                        self._update_job(existing_job, job_data)
                        updated_jobs += 1
                        logger.debug(f"Updated job: {job_data.title} at {job_data.company}")
                else:
                    # Create new job
                    self._create_job(job_data)
                    new_jobs += 1
                    logger.debug(f"Created new job: {job_data.title} at {job_data.company}")
                    
            except Exception as e:
                logger.error(f"Error storing job {job_data.title}: {e}")
                continue
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"Job storage complete: {new_jobs} new, {updated_jobs} updated, {total_processed} total")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit job storage: {e}")
            raise
        
        return total_processed, new_jobs, updated_jobs
    
    def _find_duplicate(self, job_data: JobCreate) -> Optional[Job]:
        """
        Find duplicate job based on multiple criteria.
        
        Deduplication strategy:
        1. Same external_id and source (exact match)
        2. Same title and company (fuzzy match)
        3. Similar title and company with recent posting (time-based)
        """
        # Strategy 1: Exact match by external_id and source
        if job_data.external_id:
            exact_match = self.db.query(Job).filter(
                and_(
                    Job.external_id == job_data.external_id,
                    Job.source == job_data.source
                )
            ).first()
            
            if exact_match:
                return exact_match
        
        # Strategy 2: Match by title and company (case-insensitive)
        title_company_match = self.db.query(Job).filter(
            and_(
                Job.title.ilike(f"%{job_data.title}%"),
                Job.company.ilike(f"%{job_data.company}%")
            )
        ).first()
        
        if title_company_match:
            # Additional check: if it's very similar, consider it a duplicate
            if self._is_similar_job(title_company_match, job_data):
                return title_company_match
        
        return None
    
    def _is_similar_job(self, existing_job: Job, new_job_data: JobCreate) -> bool:
        """
        Check if two jobs are similar enough to be considered duplicates.
        
        Uses fuzzy matching on title and company.
        """
        # Simple similarity check (can be enhanced with fuzzy string matching)
        title_similarity = self._calculate_similarity(
            existing_job.title.lower(), 
            new_job_data.title.lower()
        )
        
        company_similarity = self._calculate_similarity(
            existing_job.company.lower(),
            new_job_data.company.lower()
        )
        
        # Consider similar if both title and company have high similarity
        return title_similarity > 0.8 and company_similarity > 0.9
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate simple string similarity ratio.
        
        This is a basic implementation. For production, consider using
        libraries like fuzzywuzzy or difflib for better fuzzy matching.
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple Jaccard similarity on words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _should_update_job(self, existing_job: Job, new_job_data: JobCreate) -> bool:
        """
        Determine if an existing job should be updated with new data.
        
        Update if:
        1. New job has more complete information
        2. Description has changed significantly
        3. Requirements have been updated
        """
        # Update if new job has description and existing doesn't
        if new_job_data.description and not existing_job.description:
            return True
        
        # Update if new job has more requirements
        if len(new_job_data.requirements) > len(existing_job.requirements or []):
            return True
        
        # Update if salary information is added
        if new_job_data.salary_range and not existing_job.salary_range:
            return True
        
        # Update if application email is added
        if new_job_data.application_email and not existing_job.application_email:
            return True
        
        return False
    
    def _update_job(self, existing_job: Job, new_job_data: JobCreate):
        """Update existing job with new data."""
        # Update fields that might have new information
        if new_job_data.description and len(new_job_data.description) > len(existing_job.description or ""):
            existing_job.description = new_job_data.description
        
        if new_job_data.salary_range and not existing_job.salary_range:
            existing_job.salary_range = new_job_data.salary_range
        
        if new_job_data.application_email and not existing_job.application_email:
            existing_job.application_email = new_job_data.application_email
        
        if len(new_job_data.requirements) > len(existing_job.requirements or []):
            existing_job.requirements = new_job_data.requirements
        
        # Always update the fetched_at timestamp
        from datetime import datetime
        existing_job.fetched_at = datetime.utcnow()
    
    def _create_job(self, job_data: JobCreate):
        """Create a new job record."""
        job = Job(**job_data.dict())
        self.db.add(job)
    
    def get_jobs_count(self) -> int:
        """Get total number of jobs in database."""
        return self.db.query(Job).count()
    
    def get_recent_jobs(self, limit: int = 10) -> List[Job]:
        """Get most recently fetched jobs."""
        return self.db.query(Job).order_by(Job.fetched_at.desc()).limit(limit).all()
    
    def search_jobs(
        self, 
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Job]:
        """
        Search jobs with filters.
        
        Args:
            keywords: Keywords to search in title and description
            location: Location filter
            company: Company filter
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            List of matching jobs
        """
        query = self.db.query(Job)
        
        # Apply filters
        if keywords:
            keyword_filters = []
            for keyword in keywords:
                keyword_filter = or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Job.description.ilike(f"%{keyword}%"),
                    Job.requirements.any(keyword)
                )
                keyword_filters.append(keyword_filter)
            
            # Jobs must match at least one keyword
            query = query.filter(or_(*keyword_filters))
        
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        
        if company:
            query = query.filter(Job.company.ilike(f"%{company}%"))
        
        # Order by most recent first
        query = query.order_by(Job.fetched_at.desc())
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()