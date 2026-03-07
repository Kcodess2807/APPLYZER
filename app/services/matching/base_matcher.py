
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from app.models import Project

@dataclass
class MatchResult:
    """Result of a project match with explanations."""
    project: Project
    confidence_score: float
    explanation: Dict[str, Any]
    matching_keywords: List[str]
    similarity_breakdown: Dict[str, float]

@dataclass
class JobContext:
    """Job context for matching."""
    job_id: str
    title: str
    description: str
    company: str
    required_skills: List[str]
    preferred_skills: List[str]
    category: str = None
    location: str = None

class BaseProjectMatcher(ABC):
    """Abstract base class for project matching algorithms."""
    
    @abstractmethod
    def match_projects(
        self, 
        projects: List[Project], 
        job_context: JobContext,
        max_results: int = 5
    ) -> List[MatchResult]:
        """
        Match projects to job requirements.
        
        Args:
            projects: List of user projects to match against
            job_context: Job information and requirements
            max_results: Maximum number of results to return
            
        Returns:
            List of MatchResult objects sorted by confidence score
        """
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Return the name of the matching algorithm."""
        pass
    
    @abstractmethod
    def get_algorithm_version(self) -> str:
        """Return the version of the matching algorithm."""
        pass
