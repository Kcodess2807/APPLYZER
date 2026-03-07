"""Resume parser endpoint — upload a PDF, get back structured profile data."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from loguru import logger

from app.services.resume_parser_service import ResumeParserService

router = APIRouter()
_parser = ResumeParserService()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF and extract structured profile data.

    Returns:
    - professional_summary
    - skills        (list of {category, items})
    - education     (list of {degree, institution, year, coursework})
    - experiences   (list of {role, company, location, duration, achievements})
    - projects      (list of {title, description, technologies, achievements, skills_demonstrated, project_url})
    - file_path     (where the PDF was saved on the server)

    The returned data is NOT saved automatically — review it and use the
    existing /skills, /education, /experiences, /projects endpoints to save.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB.")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(f"Parsing resume: {file.filename} ({len(file_bytes)} bytes)")

    try:
        result = _parser.parse(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse resume.")

    return {
        "success": True,
        "message": "Resume parsed successfully. Review the data and save using the profile endpoints.",
        "parsed_data": result
    }
