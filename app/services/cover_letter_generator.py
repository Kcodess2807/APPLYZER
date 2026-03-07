"""Cover letter generation service - delegates to CoverLetterWriterAgent."""
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class CoverLetterGenerationError(Exception):
    """Raised when cover letter generation fails."""
    pass


class CoverLetterGenerator:
    """Cover letter generator service."""
    
    def __init__(self):
        self.output_dir = Path("app/generated/cover_letters")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cover_letter(
        self,
        job_data: Dict[str, Any],
        user_data: Dict[str, Any],
        selected_projects: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate cover letter - stub for now."""
        logger.warning("Cover letter generation called - integrate with CoverLetterWriterAgent")
        return {
            "cover_letter_id": "test-123",
            "content": "Cover letter stub - integrate with agent system",
            "generation_method": "stub"
        }
    
    def get_cover_letter_path(self, cover_letter_id: str) -> Optional[Path]:
        """Get cover letter file path."""
        return None


# Global instance
cover_letter_generator = CoverLetterGenerator()
