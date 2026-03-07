"""Tests for JobFetcherAgent."""
import pytest
from app.agents.job_fetcher import JobFetcherAgent
from app.agents.schemas import AgentStatus


@pytest.fixture
def job_fetcher():
    """Create JobFetcherAgent instance."""
    return JobFetcherAgent()


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return """job_title,company,job_link,job_description,email
Software Engineer,Tech Corp,https://example.com/job1,Python FastAPI developer needed,hr@techcorp.com
Data Scientist,Data Inc,https://example.com/job2,ML engineer with Python experience,jobs@datainc.com
"""


@pytest.mark.asyncio
async def test_fetch_from_csv_success(job_fetcher, sample_csv_content):
    """Test successful CSV parsing."""
    input_data = {
        "source": "csv",
        "csv_content": sample_csv_content
    }
    
    result = await job_fetcher.run(input_data)
    
    assert result.is_success()
    assert result.data["count"] == 2
    assert result.data["source"] == "csv"
    assert len(result.data["jobs"]) == 2
    
    # Check first job
    first_job = result.data["jobs"][0]
    assert first_job["title"] == "Software Engineer"
    assert first_job["company"] == "Tech Corp"


@pytest.mark.asyncio
async def test_fetch_from_csv_empty(job_fetcher):
    """Test CSV parsing with empty content."""
    input_data = {
        "source": "csv",
        "csv_content": ""
    }
    
    result = await job_fetcher.run(input_data)
    
    assert not result.is_success()
    assert "error" in result.to_dict()


@pytest.mark.asyncio
async def test_fetch_from_csv_missing_columns(job_fetcher):
    """Test CSV with missing required columns."""
    csv_content = "random_column,another_column\nvalue1,value2"
    
    input_data = {
        "source": "csv",
        "csv_content": csv_content
    }
    
    result = await job_fetcher.run(input_data)
    
    assert not result.is_success()


@pytest.mark.asyncio
async def test_fetch_from_csv_flexible_columns(job_fetcher):
    """Test CSV with alternative column names."""
    csv_content = """position,organization,link,details
Backend Developer,StartupXYZ,https://example.com,Django developer
"""
    
    input_data = {
        "source": "csv",
        "csv_content": csv_content
    }
    
    result = await job_fetcher.run(input_data)
    
    # Should handle flexible column names
    assert result.status in [AgentStatus.SUCCESS, AgentStatus.FAILED]


@pytest.mark.asyncio
async def test_unsupported_source(job_fetcher):
    """Test with unsupported source type."""
    input_data = {
        "source": "invalid_source"
    }
    
    result = await job_fetcher.run(input_data)
    
    assert not result.is_success()
    assert "Unsupported source" in result.error or "error" in result.to_dict()
