#Pydantic v2 schemas for all agent inputs, outputs, and shared data models.
#Job Source → JobFetcher → ProjectMatcher → ResumeGenerator → CoverLetterWriter → Workflow Output

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


class AgentStatus(str, Enum):
    PENDING="pending"
    RUNNING="running"
    SUCCESS="success"
    FAILED="failed"
    SKIPPED="skipped"


class JobSourceType(str, Enum):
    CSV="csv"
    LINKEDIN="linkedin"
    GOOGLE_SHEETS="google_sheets"


class ResumeTemplate(str, Enum):
    STANDARD="standard"
    MODERN="modern"
    MINIMAL="minimal"
    PROFESSIONAL="professional"


class CoverLetterTone(str, Enum):
    PROFESSIONAL="professional"
    ENTHUSIASTIC="enthusiastic"
    FORMAL="formal"
    CASUAL="casual"


#ill act a s a template
class _BaseSchema(BaseModel):
    model_config={"use_enum_values": True, "frozen": False}


#AGENT RESULT WRAPPER
class AgentResultMetadata(_BaseSchema):
    agent_name: str
    execution_time_ms: float | None = None
    version: str="1.0.0"


class AgentResultSchema(_BaseSchema):
    status: AgentStatus
    data: dict[str, Any]=Field(default_factory=dict)
    error: str | None=None
    metadata: AgentResultMetadata
    timestamp: datetime=Field(default_factory=datetime.utcnow)



#job source/job data
class JobSourceConfig(_BaseSchema):
    #will decide whenere and how to fetch jobs

    source: JobSourceType
    url: str | None=None
    csv_content: str | None=None
    filters: dict[str, Any]=Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_required_fields(self)->"JobSourceConfig":
        if self.source in (JobSourceType.LINKEDIN, JobSourceType.GOOGLE_SHEETS):
            if not self.url:
                raise ValueError(f"'url' is required for source '{self.source}'")
        if self.source==JobSourceType.CSV and not self.csv_content:
            raise ValueError("'csv_content' is required for source 'csv'")
        return self


class JobData(_BaseSchema):
    #Normalised job listing, regardless of origin

    title: str
    company: str
    description: str
    url: str | None = None
    email: str | None = None
    location: str | None = None
    salary_range: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    source: str


#job fetcher servcie
class JobFetcherInput(_BaseSchema):
    source_config: JobSourceConfig


class JobFetcherOutput(_BaseSchema):
    jobs: list[JobData]
    count: int
    source: str


#project matcher service


class ProjectMatcherInput(_BaseSchema):
    user_id: str
    job: JobData
    max_projects: int = Field(default=5, ge=1, le=20)


class ProjectScore(_BaseSchema):
    project_id: str
    title: str
    score: float
    match_reasons: list[str] = Field(default_factory=list)


class ProjectMatcherOutput(_BaseSchema):
    matched_projects: list[dict[str, Any]]
    scores: list[float]
    total_available: int
    match_details: list[ProjectScore] = Field(default_factory=list)



#user profile/profile info
class PersonalInfo(_BaseSchema):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        import re
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError(f"Invalid email address: {v!r}")
        return v


class UserProfile(_BaseSchema):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)

#resume generator
class ResumeGeneratorInput(_BaseSchema):
    user_profile: UserProfile
    job: JobData
    matched_projects: list[dict[str, Any]] = Field(default_factory=list)
    template: ResumeTemplate = ResumeTemplate.STANDARD


class ResumeData(_BaseSchema):
    personal_info: PersonalInfo
    summary: str
    skills: list[str]
    projects: list[dict[str, Any]]
    experience: list[dict[str, Any]]
    education: list[dict[str, Any]]
    certifications: list[dict[str, Any]]


class ResumeGeneratorOutput(_BaseSchema):
    resume: dict[str, Any]
    resume_data: ResumeData
    template_used: str
    generated_at: datetime


#Cover Letter Writer Agent

class CoverLetterWriterInput(_BaseSchema):
    user_profile: UserProfile
    job: JobData
    resume_data: dict[str, Any] | None = None
    matched_projects: list[dict[str, Any]] = Field(default_factory=list)
    tone: CoverLetterTone = CoverLetterTone.PROFESSIONAL


class CoverLetterContent(_BaseSchema):
    opening: str
    body: str
    closing: str


class CoverLetterData(_BaseSchema):
    header: PersonalInfo
    recipient: dict[str, str]
    content: CoverLetterContent
    full_text: str


class CoverLetterWriterOutput(_BaseSchema):
    cover_letter: CoverLetterData
    tone: str
    generated_at: datetime


#workflow orchestration, top plevel it will help in the entire pipeline
class WorkflowOptions(_BaseSchema):
    template: ResumeTemplate = ResumeTemplate.STANDARD
    tone: CoverLetterTone = CoverLetterTone.PROFESSIONAL
    max_projects: int = Field(default=5, ge=1, le=20)
    skip_cover_letter: bool = False
    skip_resume: bool = False


class WorkflowInput(_BaseSchema):
    user_id: str
    user_profile: UserProfile
    job_source: JobSourceConfig
    options: WorkflowOptions = Field(default_factory=WorkflowOptions)


class ApplicationResult(_BaseSchema):
    job: JobData
    status: str
    matched_projects: list[dict[str, Any]] | None = None
    resume: dict[str, Any] | None = None
    cover_letter: dict[str, Any] | None = None
    error: str | None = None


class WorkflowOutput(_BaseSchema):
    status: str
    applications: list[ApplicationResult]
    total_jobs: int
    successful: int
    failed: int
    start_time: datetime
    end_time: datetime
    duration_seconds: float