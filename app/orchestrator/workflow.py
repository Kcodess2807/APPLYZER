"""Workflow orchestrator for managing agent execution."""
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from app.agents import (
    JobFetcherAgent,
    ProjectMatcherAgent,
    ResumeGeneratorAgent,
    CoverLetterWriterAgent,
    AgentStatus
)


class WorkflowStatus(str, Enum):
    """Overall workflow status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some agents succeeded, some failed


class WorkflowResult:
    """Result of complete workflow execution."""
    
    def __init__(self):
        self.status = WorkflowStatus.PENDING
        self.agent_results = {}
        self.start_time = None
        self.end_time = None
        self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "agent_results": {
                name: result.to_dict() 
                for name, result in self.agent_results.items()
            },
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else None
            ),
            "errors": self.errors
        }


class JobApplicationOrchestrator:
    """
    Orchestrates the complete job application workflow.
    Manages execution of all agents in sequence or individually.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger.bind(component="orchestrator")
        
        # Initialize agents
        self.job_fetcher = JobFetcherAgent()
        self.project_matcher = ProjectMatcherAgent(db)
        self.resume_generator = ResumeGeneratorAgent()
        self.cover_letter_writer = CoverLetterWriterAgent()
    
    async def run_full_workflow(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        job_source_config: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute complete workflow: fetch jobs → match projects → generate resume → write cover letter.
        
        Args:
            user_id: User identifier
            user_profile: User profile data
            job_source_config: Configuration for job fetching
            options: Optional settings (template, tone, max_projects, etc.)
        """
        result = WorkflowResult()
        result.start_time = datetime.utcnow()
        result.status = WorkflowStatus.RUNNING
        
        self.logger.info("🚀 Starting full job application workflow")
        
        try:
            options = options or {}
            
            # Step 1: Fetch jobs
            self.logger.info("Step 1/4: Fetching jobs...")
            job_result = await self.job_fetcher.execute(job_source_config)
            result.agent_results["job_fetcher"] = job_result
            
            if not job_result.is_success():
                result.status = WorkflowStatus.FAILED
                result.errors.append("Job fetching failed")
                return result
            
            jobs = job_result.data.get("jobs", [])
            if not jobs:
                result.status = WorkflowStatus.FAILED
                result.errors.append("No jobs found")
                return result
            
            self.logger.info(f"Found {len(jobs)} jobs")
            
            # Process each job
            applications = []
            
            for idx, job in enumerate(jobs):
                self.logger.info(f"Processing job {idx + 1}/{len(jobs)}: {job.get('title', 'Unknown')}")
                
                app_result = await self._process_single_job(
                    user_id,
                    user_profile,
                    job,
                    options
                )
                
                applications.append(app_result)
            
            result.agent_results["applications"] = applications
            result.status = WorkflowStatus.COMPLETED
            
            self.logger.info(f"✅ Workflow completed: {len(applications)} applications generated")
            
        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {str(e)}")
            result.status = WorkflowStatus.FAILED
            result.errors.append(str(e))
        
        finally:
            result.end_time = datetime.utcnow()
        
        return result
    
    async def _process_single_job(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        job: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single job through the pipeline."""
        
        application = {
            "job": job,
            "status": "processing",
            "results": {}
        }
        
        try:
            # Step 2: Match projects
            self.logger.info("Step 2/4: Matching projects...")
            project_result = await self.project_matcher.execute({
                "user_id": user_id,
                "job": job,
                "max_projects": options.get("max_projects", 5)
            })
            application["results"]["project_matcher"] = project_result.to_dict()
            
            matched_projects = project_result.data.get("matched_projects", [])
            
            # Step 3: Generate resume
            self.logger.info("Step 3/4: Generating resume...")
            resume_result = await self.resume_generator.execute({
                "user_profile": user_profile,
                "job": job,
                "matched_projects": matched_projects,
                "template": options.get("template", "standard")
            })
            application["results"]["resume_generator"] = resume_result.to_dict()
            
            # Step 4: Write cover letter
            self.logger.info("Step 4/4: Writing cover letter...")
            cover_letter_result = await self.cover_letter_writer.execute({
                "user_profile": user_profile,
                "job": job,
                "resume_data": resume_result.data.get("resume_data", {}),
                "matched_projects": matched_projects,
                "tone": options.get("tone", "professional")
            })
            application["results"]["cover_letter_writer"] = cover_letter_result.to_dict()
            
            application["status"] = "completed"
            
        except Exception as e:
            self.logger.error(f"Error processing job: {str(e)}")
            application["status"] = "failed"
            application["error"] = str(e)
        
        return application
    
    # Individual agent execution methods for standalone use
    
    async def fetch_jobs_only(
        self,
        source_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute only job fetching agent."""
        self.logger.info("Executing job fetcher only")
        result = await self.job_fetcher.execute(source_config)
        return result.to_dict()
    
    async def match_projects_only(
        self,
        user_id: str,
        job: Dict[str, Any],
        max_projects: int = 5
    ) -> Dict[str, Any]:
        """Execute only project matching agent."""
        self.logger.info("Executing project matcher only")
        result = await self.project_matcher.execute({
            "user_id": user_id,
            "job": job,
            "max_projects": max_projects
        })
        return result.to_dict()
    
    async def generate_resume_only(
        self,
        user_profile: Dict[str, Any],
        job: Dict[str, Any],
        matched_projects: List[Dict[str, Any]],
        template: str = "standard"
    ) -> Dict[str, Any]:
        """Execute only resume generation agent."""
        self.logger.info("Executing resume generator only")
        result = await self.resume_generator.execute({
            "user_profile": user_profile,
            "job": job,
            "matched_projects": matched_projects,
            "template": template
        })
        return result.to_dict()
    
    async def write_cover_letter_only(
        self,
        user_profile: Dict[str, Any],
        job: Dict[str, Any],
        resume_data: Dict[str, Any],
        matched_projects: List[Dict[str, Any]],
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """Execute only cover letter writing agent."""
        self.logger.info("Executing cover letter writer only")
        result = await self.cover_letter_writer.execute({
            "user_profile": user_profile,
            "job": job,
            "resume_data": resume_data,
            "matched_projects": matched_projects,
            "tone": tone
        })
        return result.to_dict()
