"""FastAPI app with PDF generation - Core backend for ATS resume builder."""
import os
import logging
import tempfile
import subprocess
import shutil
from pathlib import Path
from io import BytesIO
from typing import Optional, Tuple
import json
import asyncio
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Applyzer Resume Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store generated content temporarily
_generated_content = {}


# === MODELS ===
class JobTarget(BaseModel):
    company: str
    role: str
    jobDescription: str


class GenerateRequest(BaseModel):
    target: JobTarget


class ProjectEntry(BaseModel):
    id: str
    title: str
    dateRange: str
    stack: list[str]
    tags: list[str]
    bullets: list[str]

class GenerateResponse(BaseModel):
    selectedProjects: list[ProjectEntry]
    rationale: str
    resumeLatex: str
    coverLetter: str
    coverLetterLatex: str
    resumePdfAvailable: bool = False
    coverLetterPdfAvailable: bool = False


class ProjectsResponse(BaseModel):
    count: int
    projects: list[ProjectEntry]


# === PDF GENERATION ===
class PDFGenerationError(Exception):
    pass


def generate_pdf_from_latex(latex_content: str, filename: str = "document") -> bytes:
    """Generate PDF from LaTeX content using system pdflatex."""
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = Path(temp_dir) / f"{filename}.tex"
        pdf_file = Path(temp_dir) / f"{filename}.pdf"
        
        # Write LaTeX content
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        try:
            # Run pdflatex twice for cross-references
            for _ in range(2):
                result = subprocess.run([
                    "pdflatex", 
                    "-interaction=nonstopmode",
                    "-output-directory", temp_dir,
                    str(tex_file)
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode != 0:
                    raise PDFGenerationError(f"LaTeX compilation failed: {result.stderr}")
            
            # Read generated PDF
            if pdf_file.exists():
                with open(pdf_file, 'rb') as f:
                    return f.read()
            else:
                raise PDFGenerationError("PDF file was not generated")
                
        except subprocess.TimeoutExpired:
            raise PDFGenerationError("LaTeX compilation timed out")
        except Exception as e:
            raise PDFGenerationError(f"Compilation error: {str(e)}")


def check_pdf_available() -> bool:
    """Check if PDF generation is available."""
    try:
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, timeout=10)
        return result.returncode == 0
    except:
        return False

# === DATA ACCESS ===
async def get_profile():
    """Get user profile from JSON file."""
    await asyncio.sleep(0.1)  # Simulate DB latency
    path = Path(__file__).parent / "data" / "profile.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def get_project_pool():
    """Get all projects from JSON file."""
    await asyncio.sleep(0.15)  # Simulate DB latency
    path = Path(__file__).parent / "data" / "projects.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def get_projects_by_ids(project_ids: list[str]):
    """Get specific projects by IDs."""
    await asyncio.sleep(0.1)  # Simulate DB latency
    all_projects = await get_project_pool()
    return [p for p in all_projects if p["id"] in project_ids]


# === PROJECT SELECTION ===
def tokenize(text: str) -> list[str]:
    return [w for w in re.sub(r"[^a-z0-9\s]", " ", text.lower()).split() if w]


def score_project(project: dict, jd_tokens: set[str]) -> int:
    searchable = " ".join([
        project.get("title", ""),
        " ".join(project.get("stack", [])),
        " ".join(project.get("tags", [])),
        " ".join(project.get("bullets", [])),
    ])
    tokens = tokenize(searchable)
    return sum(1 for t in tokens if t in jd_tokens)


async def select_projects_with_openrouter(api_key: str, company: str, role: str, job_description: str, projects: list[dict]) -> tuple[list[str], str]:
    """Use OpenRouter to select best projects."""
    prompt = f"""Pick exactly 2 projects from the pool that best fit the target role.
Only use project IDs present in the input.
Return strict JSON:
{{"selectedProjectIds": ["id1","id2"], "rationale": "short explanation"}}

Target: {company} - {role}
Job: {job_description}

Projects:
{json.dumps(projects, indent=2)}"""

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-OpenRouter-Title": "Applyzer Resume Builder",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
            },
            timeout=60.0,
        )
    
    response.raise_for_status()
    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Extract JSON
    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        raise ValueError("No JSON in response")
    
    data = json.loads(match.group(0))
    ids = data.get("selectedProjectIds", [])
    
    if not isinstance(ids, list) or len(ids) != 2:
        raise ValueError("Must return exactly 2 project IDs")
    
    return ids, data.get("rationale", "Selected by job fit")
async def pick_two_relevant_projects(company: str, role: str, job_description: str, project_pool: list[dict]) -> tuple[list[str], str]:
    """Select 2 relevant projects using OpenRouter or local fallback."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if api_key:
        try:
            return await select_projects_with_openrouter(
                api_key, company, role, job_description,
                [{"id": p["id"], "title": p["title"], "stack": p["stack"], "tags": p["tags"], "bullets": p["bullets"]} for p in project_pool]
            )
        except Exception as e:
            logger.warning(f"OpenRouter failed: {e}, using local fallback")
    
    # Local fallback
    jd_tokens = set(tokenize(f"{company} {role} {job_description}"))
    scored = [(score_project(p, jd_tokens), p) for p in project_pool]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    top_projects = [p for _, p in scored[:2]]
    return [p["id"] for p in top_projects], f"Selected top 2 projects by keyword relevance: {', '.join(p['title'] for p in top_projects)}"


# === LATEX GENERATION ===
def escape_latex(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def build_resume_latex(profile: dict, selected_projects: list[dict]) -> str:
    """Generate Jake-style ATS-friendly resume LaTeX."""
    edu = (profile.get("education") or [{}])[0]
    skills = profile.get("skills") or {}
    
    # Build experience section
    experience_section = ""
    for exp in profile.get("experience", []):
        bullets = "\n".join(f"\\resumeItem{{{escape_latex(b)}}}" for b in exp.get("bullets", [])[:3])
        experience_section += f"""
\\resumeSubheading
{{{escape_latex(exp.get('role', ''))}}}{{{escape_latex(exp.get('dateRange', ''))}}}
{{{escape_latex(exp.get('company', ''))}}}{{{escape_latex(exp.get('location', ''))}}}
\\resumeItemListStart
{bullets}
\\resumeItemListEnd
"""
    
    # Build projects section
    projects_section = ""
    for p in selected_projects:
        bullets = "\n".join(f"\\resumeItem{{{escape_latex(b)}}}" for b in p.get("bullets", [])[:3])
        stack = ", ".join(p.get("stack", []))
        projects_section += f"""
\\resumeProjectHeading
{{\\textbf{{{escape_latex(p.get('title', ''))}}} $|$ \\emph{{{escape_latex(stack)}}}}}{{{escape_latex(p.get('dateRange', ''))}}}
\\resumeItemListStart
{bullets}
\\resumeItemListEnd
"""
    return f"""\\documentclass[letterpaper,11pt]{{article}}
\\usepackage{{latexsym}}
\\usepackage[empty]{{fullpage}}
\\usepackage{{titlesec}}
\\usepackage{{marvosym}}
\\usepackage[usenames,dvipsnames]{{color}}
\\usepackage{{verbatim}}
\\usepackage{{enumitem}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{fancyhdr}}
\\usepackage[english]{{babel}}
\\usepackage{{tabularx}}
\\input{{glyphtounicode}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyfoot{{}}
\\renewcommand{{\\headrulewidth}}{{0pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}
\\addtolength{{\\oddsidemargin}}{{-0.5in}}
\\addtolength{{\\evensidemargin}}{{-0.5in}}
\\addtolength{{\\textwidth}}{{1in}}
\\addtolength{{\\topmargin}}{{-.5in}}
\\addtolength{{\\textheight}}{{1.0in}}
\\urlstyle{{same}}
\\raggedbottom
\\raggedright
\\setlength{{\\tabcolsep}}{{0in}}
\\titleformat{{\\section}}{{\\vspace{{-4pt}}\\scshape\\raggedright\\large}}{{}}{{0em}}{{}}[\\color{{black}}\\titlerule \\vspace{{-5pt}}]
\\pdfgentounicode=1
\\newcommand{{\\resumeItem}}[1]{{\\item\\small{{{{#1 \\vspace{{-2pt}}}}}}}}
\\newcommand{{\\resumeSubheading}}[4]{{
  \\vspace{{-2pt}}\\item
  \\begin{{tabular*}}{{0.97\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
    \\textbf{{#1}} & #2 \\\\
    \\textit{{\\small#3}} & \\textit{{\\small #4}} \\\\
  \\end{{tabular*}}\\vspace{{-7pt}}
}}
\\newcommand{{\\resumeProjectHeading}}[2]{{
  \\item
  \\begin{{tabular*}}{{0.97\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
    \\small#1 & #2 \\\\
  \\end{{tabular*}}\\vspace{{-7pt}}
}}
\\newcommand{{\\resumeSubHeadingListStart}}{{\\begin{{itemize}}[leftmargin=0.15in, label={{}}]}}
\\newcommand{{\\resumeSubHeadingListEnd}}{{\\end{{itemize}}}}
\\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}}}
\\newcommand{{\\resumeItemListEnd}}{{\\end{{itemize}}\\vspace{{-5pt}}}}
\\begin{{document}}
\\begin{{center}}
  \\textbf{{\\Huge \\scshape {escape_latex(profile.get('fullName', ''))}}} \\\\ \\vspace{{1pt}}
  \\small {escape_latex(profile.get('phone', ''))} $|$ \\href{{mailto:{escape_latex(profile.get('email', ''))}}}{{\\underline{{{escape_latex(profile.get('email', ''))}}}}} $|$
  \\href{{{escape_latex((profile.get('links') or {{}}).get('linkedin', ''))}}}{{\\underline{{linkedin}}}} $|$
  \\href{{{escape_latex((profile.get('links') or {{}}).get('github', ''))}}}{{\\underline{{github}}}}
\\end{{center}}
\\section{{Education}}
\\resumeSubHeadingListStart
\\resumeSubheading
{{{escape_latex(edu.get('school', ''))}}}{{{escape_latex(edu.get('location', ''))}}}
{{{escape_latex(edu.get('degree', ''))}}}{{{escape_latex(edu.get('dateRange', ''))}}}
\\resumeSubHeadingListEnd
\\section{{Experience}}
\\resumeSubHeadingListStart{experience_section}
\\resumeSubHeadingListEnd
\\section{{Projects}}
\\resumeSubHeadingListStart{projects_section}
\\resumeSubHeadingListEnd
\\section{{Technical Skills}}
\\begin{{itemize}}[leftmargin=0.15in, label={{}}]
\\small{{\\item{{
\\textbf{{Languages}}{{: {escape_latex(', '.join(skills.get('languages', [])))}}} \\\\
\\textbf{{Frameworks}}{{: {escape_latex(', '.join(skills.get('frameworks', [])))}}} \\\\
\\textbf{{Developer Tools}}{{: {escape_latex(', '.join(skills.get('tools', [])))}}} \\\\
\\textbf{{Libraries}}{{: {escape_latex(', '.join(skills.get('libraries', [])))}}}
}}}}
\\end{{itemize}}
\\end{{document}}"""
def build_cover_letter_text(profile: dict, selected_projects: list[dict], target: dict, rationale: str) -> str:
    """Generate cover letter plain text."""
    company = target.get("company", "")
    role = target.get("role", "")
    intro = f"Dear Hiring Manager at {company},"
    p1 = f"I am excited to apply for the {role} role at {company}. I am a Computer Science student with hands-on full-stack and machine learning experience, and I enjoy building reliable products that connect model performance with real user impact."
    t1 = selected_projects[0].get("title", "") if selected_projects else ""
    t2 = selected_projects[1].get("title", "") if len(selected_projects) > 1 else ""
    p2 = f"Two projects that best reflect this fit are {t1} and {t2}. In these projects, I built production-style APIs, implemented measurable performance improvements, and translated complex requirements into clear, maintainable features aligned with business goals."
    p3 = f"I would value the opportunity to contribute this mix of software engineering and applied ML experience to your team. Thank you for your time and consideration, and I look forward to discussing how I can support {company}'s goals."
    close = f"Sincerely,\\n{profile.get('fullName', '')}\\n{profile.get('email', '')} | {profile.get('phone', '')}"
    return "\\n".join([intro, "", p1, "", p2, "", f"Selection rationale: {rationale}", "", p3, "", close])


def build_cover_letter_latex(cover_text: str) -> str:
    """Convert cover letter text to LaTeX format."""
    latex_text = cover_text.replace("\\n", "\\\\\n")
    return f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage[hidelinks]{{hyperref}}
\\begin{{document}}
{latex_text}
\\end{{document}}"""


# === API ENDPOINTS ===
@app.get("/api/projects", response_model=ProjectsResponse)
async def list_projects():
    """Return full project pool."""
    projects = await get_project_pool()
    return ProjectsResponse(count=len(projects), projects=projects)


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Select 2 relevant projects and generate resume + cover letter."""
    target = req.target
    if not target.company or not target.role or not target.jobDescription:
        raise HTTPException(status_code=400, detail="Missing required fields")

    profile, project_pool = await get_profile(), await get_project_pool()
    selected_ids, rationale = await pick_two_relevant_projects(
        target.company, target.role, target.jobDescription, project_pool
    )

    selected_projects = await get_projects_by_ids(selected_ids)
    if len(selected_projects) < 2:
        raise HTTPException(status_code=500, detail="Could not resolve two selected projects")

    resume_latex = build_resume_latex(profile, selected_projects)
    cover_letter = build_cover_letter_text(profile, selected_projects, target.model_dump(), rationale)
    cover_letter_latex = build_cover_letter_latex(cover_letter)

    # Store content for PDF generation
    session_id = f"{target.company}_{target.role}".replace(" ", "_").lower()
    _generated_content[session_id] = {
        "resume_latex": resume_latex,
        "cover_letter_latex": cover_letter_latex,
        "target": target,
    }

    pdf_available = check_pdf_available()

    return GenerateResponse(
        selectedProjects=selected_projects,
        rationale=rationale,
        resumeLatex=resume_latex,
        coverLetter=cover_letter,
        coverLetterLatex=cover_letter_latex,
        resumePdfAvailable=pdf_available,
        coverLetterPdfAvailable=pdf_available,
    )
@app.get("/api/download/resume-pdf/{session_id}")
async def download_resume_pdf(session_id: str):
    """Download resume as PDF."""
    if session_id not in _generated_content:
        raise HTTPException(status_code=404, detail="Generated content not found. Please generate first.")
    
    content = _generated_content[session_id]
    
    try:
        pdf_bytes = generate_pdf_from_latex(content["resume_latex"], "resume")
        target = content["target"]
        filename = f"resume_{target.company}_{target.role}.pdf".replace(" ", "_").lower()
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except PDFGenerationError as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.get("/api/download/cover-letter-pdf/{session_id}")
async def download_cover_letter_pdf(session_id: str):
    """Download cover letter as PDF."""
    if session_id not in _generated_content:
        raise HTTPException(status_code=404, detail="Generated content not found. Please generate first.")
    
    content = _generated_content[session_id]
    
    try:
        pdf_bytes = generate_pdf_from_latex(content["cover_letter_latex"], "cover_letter")
        target = content["target"]
        filename = f"cover_letter_{target.company}_{target.role}.pdf".replace(" ", "_").lower()
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except PDFGenerationError as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.get("/api/pdf-status")
async def check_pdf_status():
    """Check if PDF generation is available."""
    available = check_pdf_available()
    return {
        "available": available,
        "message": "PDF generation is available" if available else "pdflatex not found",
        "suggestion": "Install TeX Live (Linux) or MiKTeX (Windows)" if not available else None
    }


@app.get("/")
async def root():
    return {"message": "Applyzer Resume Builder API", "docs": "/docs"}