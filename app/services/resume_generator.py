"""Resume generation service - delegates to ResumeGeneratorAgent."""
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class ResumeGenerationError(Exception):
    """Raised when resume generation fails."""
    pass


class ResumeGenerator:
    """Resume generator service."""
    
    def __init__(self):
        self.output_dir = Path("app/generated/resumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_resume(
        self,
        user_data: Dict[str, Any],
        selected_projects: Optional[List[Dict[str, Any]]] = None,
        job_context: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate resume - stub for now."""
        logger.warning("Resume generation called - integrate with ResumeGeneratorAgent")
        return {
            "resume_id": job_id or "test-123",
            "generation_method": "stub",
            "message": "Resume generation stub - integrate with agent system"
        }
    
    def get_resume_path(self, resume_id: str) -> Optional[Path]:
        """Get resume file path."""
        return None


# Global instance
resume_generator = ResumeGenerator()
