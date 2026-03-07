"""
Job source configuration and management.
"""

from typing import List, Dict, Any
from loguru import logger

from app.services.job_fetcher import (
    JobFetcher, 
    RemoteOKFetcher, 
    GitHubJobsFetcher,
    ReedFetcher,
    AdzunaFetcher
)


class JobSourceManager:
    """Manages available job sources and their configuration."""
    
    def __init__(self):
        self.available_sources = {
            "remoteok": {
                "name": "RemoteOK",
                "class": RemoteOKFetcher,
                "enabled": True,
                "description": "Remote job listings from RemoteOK.com",
                "api_type": "REST API",
                "rate_limit": "No authentication required"
            },
            "github": {
                "name": "GitHub",
                "class": GitHubJobsFetcher,
                "enabled": True,
                "description": "Tech jobs from GitHub repositories and organizations",
                "api_type": "GitHub API",
                "rate_limit": "60 requests/hour (unauthenticated)"
            },
            "reed": {
                "name": "Reed",
                "class": ReedFetcher,
                "enabled": True,  # Enabled - will skip if no API key
                "description": "UK job listings from Reed.co.uk",
                "api_type": "REST API",
                "rate_limit": "1000 requests/month (free tier)"
            },
            "adzuna": {
                "name": "Adzuna",
                "class": AdzunaFetcher,
                "enabled": True,  # Enabled - will skip if no API credentials
                "description": "Global job listings from Adzuna",
                "api_type": "REST API",
                "rate_limit": "1000 calls/month (free tier)"
            }
        }
    
    def get_enabled_fetchers(self) -> List[JobFetcher]:
        """Get list of enabled job fetchers."""
        fetchers = []
        
        for source_id, config in self.available_sources.items():
            if config["enabled"]:
                try:
                    fetcher_class = config["class"]
                    fetcher = fetcher_class()
                    fetchers.append(fetcher)
                    logger.info(f"Enabled job source: {config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize {config['name']}: {e}")
        
        return fetchers
    
    def enable_source(self, source_id: str) -> bool:
        """Enable a job source."""
        if source_id in self.available_sources:
            self.available_sources[source_id]["enabled"] = True
            logger.info(f"Enabled job source: {source_id}")
            return True
        return False
    
    def disable_source(self, source_id: str) -> bool:
        """Disable a job source."""
        if source_id in self.available_sources:
            self.available_sources[source_id]["enabled"] = False
            logger.info(f"Disabled job source: {source_id}")
            return True
        return False
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about all available sources."""
        return {
            source_id: {
                "name": config["name"],
                "enabled": config["enabled"],
                "description": config["description"],
                "api_type": config["api_type"],
                "rate_limit": config["rate_limit"]
            }
            for source_id, config in self.available_sources.items()
        }
    
    def get_enabled_source_names(self) -> List[str]:
        """Get names of enabled sources."""
        return [
            config["name"] 
            for config in self.available_sources.values() 
            if config["enabled"]
        ]


# Global instance
job_source_manager = JobSourceManager()