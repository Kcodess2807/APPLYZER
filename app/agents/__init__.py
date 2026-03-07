"""Agent system for the automated job-application workflow.

Public surface area is intentionally narrow – import only what you need.
Internal implementation modules should not be imported directly by external code.
"""

from app.agents.base import AgentResult, BaseAgent
from app.agents.cover_letter_writer import CoverLetterWriterAgent
from app.agents.exceptions import (
    AgentException,
    AgentExecutionError,
    AgentValidationError,
    CoverLetterWriterError,
    JobFetcherError,
    ProjectMatcherError,
    ResumeGeneratorError,
)
from app.agents.job_fetcher import JobFetcherAgent
from app.agents.project_matcher import ProjectMatcherAgent
from app.agents.resume_generator import ResumeGeneratorAgent
from app.agents.schemas import AgentStatus

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    "AgentStatus",
    # Agents
    "JobFetcherAgent",
    "ProjectMatcherAgent",
    "ResumeGeneratorAgent",
    "CoverLetterWriterAgent",
    # Exceptions
    "AgentException",
    "AgentValidationError",
    "AgentExecutionError",
    "JobFetcherError",
    "ProjectMatcherError",
    "ResumeGeneratorError",
    "CoverLetterWriterError",
]

__version__ = "1.0.0"

# {
#     "Web developer" : {
#         Projects: [ "p1", "p2", "p3"],
#         Skills: ['a','b', 'c', 'd']
#     },
#     "Data Analyst" : {
#         Projects: [ "p1", "p2", "p3"],
#         Skills: ['a','b', 'c', 'd']
#     },
#     "Web developer" : {
#         Projects: [ "p1", "p2", "p3"],
#         Skills: ['a','b', 'c', 'd']
#     },
#     "Web developer" : {
#         Projects: [ "p1", "p2", "p3"],
#         Skills: ['a','b', 'c', 'd']
#     },
# }