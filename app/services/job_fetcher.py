"""Job fetcher base class and implementations for external job sources."""
from abc import ABC, abstractmethod
from typing import List
from app.schemas.job import JobCreate


class JobFetcher(ABC):
    """Base class for job fetchers."""
    
    @abstractmethod
    async def fetch_jobs(self, keywords: List[str], limit: int = 50) -> List[JobCreate]:
        """Fetch jobs from the source."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this job source."""
        pass


class RemoteOKFetcher(JobFetcher):
    """Fetcher for RemoteOK API."""
    
    def get_source_name(self) -> str:
        return "RemoteOK"
    
    async def fetch_jobs(self, keywords: List[str], limit: int = 50) -> List[JobCreate]:
        """Fetch jobs from RemoteOK."""
        # Implementation exists in old code - keeping stub for now
        return []


class GitHubJobsFetcher(JobFetcher):
    """Fetcher for GitHub jobs."""
    
    def get_source_name(self) -> str:
        return "GitHub"
    
    async def fetch_jobs(self, keywords: List[str], limit: int = 50) -> List[JobCreate]:
        """Fetch jobs from GitHub."""
        return []


class ReedFetcher(JobFetcher):
    """Fetcher for Reed.co.uk API."""
    
    def get_source_name(self) -> str:
        return "Reed"
    
    async def fetch_jobs(self, keywords: List[str], limit: int = 50) -> List[JobCreate]:
        """Fetch jobs from Reed."""
        return []


class AdzunaFetcher(JobFetcher):
    """Fetcher for Adzuna API."""
    
    def get_source_name(self) -> str:
        return "Adzuna"
    
    async def fetch_jobs(self, keywords: List[str], limit: int = 50) -> List[JobCreate]:
        """Fetch jobs from Adzuna."""
        return []
