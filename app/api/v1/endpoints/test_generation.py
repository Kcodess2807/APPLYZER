"""Test endpoints for resume and cover letter generation."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from typing import Dict, Any
from pydantic import BaseModel
from loguru import logger
import asyncio

router = APIRouter()


class TestGenerationRequest(BaseModel):
    """Request for testing document generation."""
    user_profile: Dict[str, Any]
    job: Dict[str, Any]
    matched_projects: list = []


@router.post("/resume")
async def test_resume_generation(request: TestGenerationRequest):
    """
    Test resume generation with sample data.
    
    Returns the generated resume data structure.
    """
    try:
        logger.info("Testing resume generation")
        
        from app.agents.resume_generator import ResumeGeneratorAgent
        
        agent = ResumeGeneratorAgent()
        
        result = await agent.run({
            "user_profile": request.user_profile,
            "job": request.job,
            "matched_projects": request.matched_projects,
            "template": "standard"
        })
        
        if result.is_success():
            return {
                "success": True,
                "status": "generated",
                "data": result.data,
                "message": "✅ Resume generated successfully"
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "message": "❌ Resume generation failed"
            }
            
    except Exception as e:
        logger.error(f"Resume generation test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cover-letter")
async def test_cover_letter_generation(request: TestGenerationRequest):
    """
    Test cover letter generation with sample data.
    
    Returns the generated cover letter content.
    """
    try:
        logger.info("Testing cover letter generation")
        
        from app.agents.cover_letter_writer import CoverLetterWriterAgent
        
        agent = CoverLetterWriterAgent()
        
        result = await agent.run({
            "user_profile": request.user_profile,
            "job": request.job,
            "resume_data": {},
            "matched_projects": request.matched_projects,
            "tone": "professional"
        })
        
        if result.is_success():
            return {
                "success": True,
                "status": "generated",
                "data": result.data,
                "message": "✅ Cover letter generated successfully"
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "message": "❌ Cover letter generation failed"
            }
            
    except Exception as e:
        logger.error(f"Cover letter generation test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/both")
async def test_both_generation(request: TestGenerationRequest):
    """
    Test both resume and cover letter generation together.
    
    This simulates the full document generation pipeline.
    """
    try:
        logger.info("Testing complete document generation")
        
        from app.agents.resume_generator import ResumeGeneratorAgent
        from app.agents.cover_letter_writer import CoverLetterWriterAgent
        
        # Generate resume
        resume_agent = ResumeGeneratorAgent()
        resume_result = await resume_agent.run({
            "user_profile": request.user_profile,
            "job": request.job,
            "matched_projects": request.matched_projects,
            "template": "standard"
        })
        
        # Generate cover letter
        cover_letter_agent = CoverLetterWriterAgent()
        cover_letter_result = await cover_letter_agent.run({
            "user_profile": request.user_profile,
            "job": request.job,
            "resume_data": resume_result.data.get("resume_data", {}),
            "matched_projects": request.matched_projects,
            "tone": "professional"
        })
        
        return {
            "success": True,
            "resume": {
                "status": "success" if resume_result.is_success() else "failed",
                "data": resume_result.data if resume_result.is_success() else None,
                "error": resume_result.error if not resume_result.is_success() else None
            },
            "cover_letter": {
                "status": "success" if cover_letter_result.is_success() else "failed",
                "data": cover_letter_result.data if cover_letter_result.is_success() else None,
                "error": cover_letter_result.error if not cover_letter_result.is_success() else None
            },
            "message": "✅ Both documents generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Document generation test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample-data")
async def get_sample_data():
    """
    Get sample data for testing document generation.
    
    Use this data to test the generation endpoints.
    """
    return {
        "user_profile": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-234-567-8900",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
            "summary": "Software Engineer with 3+ years of experience in Python and web development",
            "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "AWS"],
            "experience": [
                {
                    "role": "Senior Software Engineer",
                    "company": "Tech Startup",
                    "duration": "2022 - Present",
                    "location": "San Francisco, CA",
                    "achievements": [
                        "Led development of microservices architecture serving 100K+ users",
                        "Reduced API response time by 60% through optimization",
                        "Mentored 3 junior developers"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of California",
                    "year": "2020",
                    "coursework": "Data Structures, Algorithms, Machine Learning"
                }
            ]
        },
        "job": {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "description": "We are looking for an experienced Python developer with FastAPI expertise. Must have experience with PostgreSQL, Redis, and building scalable APIs. E-commerce experience is a plus.",
            "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]
        },
        "matched_projects": [
            {
                "title": "E-commerce Platform",
                "description": "Built a full-stack e-commerce platform with payment integration, user authentication, and admin dashboard. Handles 10K+ concurrent users with 99.9% uptime.",
                "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Redis"],
                "achievements": [
                    "Increased sales by 40%",
                    "Reduced load time by 60%",
                    "Handles 10K+ concurrent users"
                ],
                "project_url": "https://github.com/johndoe/ecommerce"
            },
            {
                "title": "API Gateway Service",
                "description": "Developed a high-performance API gateway with rate limiting, authentication, and request routing",
                "technologies": ["Python", "FastAPI", "Docker", "Redis"],
                "achievements": [
                    "Processes 1M+ requests/day",
                    "99.99% uptime"
                ],
                "project_url": "https://github.com/johndoe/api-gateway"
            }
        ]
    }


@router.post("/quick-test")
async def quick_test():
    """
    Quick test with pre-filled sample data.
    
    One-click test to see resume and cover letter generation.
    """
    try:
        logger.info("Running quick test with sample data")
        
        # Get sample data
        sample = await get_sample_data()
        
        # Test both generations
        from app.agents.resume_generator import ResumeGeneratorAgent
        from app.agents.cover_letter_writer import CoverLetterWriterAgent
        
        # Generate resume
        resume_agent = ResumeGeneratorAgent()
        resume_result = await resume_agent.run({
            "user_profile": sample["user_profile"],
            "job": sample["job"],
            "matched_projects": sample["matched_projects"],
            "template": "standard"
        })
        
        # Generate cover letter
        cover_letter_agent = CoverLetterWriterAgent()
        cover_letter_result = await cover_letter_agent.run({
            "user_profile": sample["user_profile"],
            "job": sample["job"],
            "resume_data": resume_result.data.get("resume_data", {}),
            "matched_projects": sample["matched_projects"],
            "tone": "professional"
        })
        
        return {
            "success": True,
            "message": "✅ Quick test completed!",
            "sample_data_used": {
                "user": sample["user_profile"]["name"],
                "job": f"{sample['job']['title']} at {sample['job']['company']}",
                "projects_count": len(sample["matched_projects"])
            },
            "results": {
                "resume": {
                    "status": "success" if resume_result.is_success() else "failed",
                    "data": resume_result.data,
                    "execution_time_ms": resume_result.metadata.get("execution_time_ms")
                },
                "cover_letter": {
                    "status": "success" if cover_letter_result.is_success() else "failed",
                    "data": cover_letter_result.data,
                    "execution_time_ms": cover_letter_result.metadata.get("execution_time_ms")
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/render-preview/{thread_id}")
async def render_preview(thread_id: str):
    """
    Get a preview of generated documents in HTML format.
    
    TODO: Implement HTML rendering of resume and cover letter
    """
    return {
        "message": "HTML preview not yet implemented",
        "thread_id": thread_id,
        "suggestion": "Use /review/{thread_id}/status to get JSON data"
    }
