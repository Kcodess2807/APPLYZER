"""Resume parser service — extracts structured profile data from a PDF using pdfplumber + Groq."""
import json
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

import pdfplumber
from loguru import logger

from app.core.config import settings
from app.services.ai_service import AIService


UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


class ResumeParserService:

    def __init__(self):
        self.ai = AIService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_upload(self, file_bytes: bytes, original_filename: str) -> Path:
        """Persist the uploaded PDF to uploads/ and return its path."""
        safe_name = f"{uuid.uuid4()}_{Path(original_filename).name}"
        dest = UPLOADS_DIR / safe_name
        dest.write_bytes(file_bytes)
        logger.info(f"Resume saved: {dest}")
        return dest

    def extract_text(self, file_bytes: bytes) -> str:
        """Pull plain text from every page of the PDF."""
        pages: list[str] = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

        if not pages:
            raise ValueError("Could not extract any text from the uploaded PDF.")

        return "\n\n".join(pages)

    def parse(self, file_bytes: bytes, original_filename: str) -> dict[str, Any]:
        """
        Full pipeline:
          1. Save PDF to uploads/
          2. Extract text
          3. Send to Groq for structured extraction
          4. Return parsed data + file path
        """
        saved_path = self.save_upload(file_bytes, original_filename)

        raw_text = self.extract_text(file_bytes)
        logger.info(f"Extracted {len(raw_text)} chars from resume")

        parsed = self._call_groq(raw_text)
        parsed["file_path"] = str(saved_path)
        return parsed

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _call_groq(self, resume_text: str) -> dict[str, Any]:
        """Send resume text to Groq and return structured JSON."""

        prompt = f"""You are a resume parser. Extract structured information from the resume text below.

Return ONLY valid JSON — no explanation, no markdown, no code fences.

The JSON must follow this exact structure:
{{
  "professional_summary": "5-10 word summary of the candidate (e.g. 'Backend engineer with 3 years in Python and ML')",
  "skills": [
    {{"category": "Programming Languages", "items": ["Python", "JavaScript"]}},
    {{"category": "Frameworks", "items": ["FastAPI", "React"]}}
  ],
  "education": [
    {{
      "degree": "B.Tech Computer Science",
      "institution": "University Name",
      "year": "2022",
      "coursework": "Data Structures, Algorithms"
    }}
  ],
  "experiences": [
    {{
      "role": "Software Engineer",
      "company": "Company Name",
      "location": "City, Country",
      "duration": "Jan 2022 - Present",
      "achievements": ["Built X which improved Y by Z%", "Led a team of 3"]
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "description": "What it does in 1-2 sentences",
      "technologies": ["Python", "FastAPI", "PostgreSQL"],
      "achievements": ["Reduced latency by 40%"],
      "skills_demonstrated": ["Backend Development", "API Design"],
      "project_url": "https://github.com/..."
    }}
  ]
}}

Rules:
- If a field is not found in the resume, use an empty string or empty array.
- project_url should only be included if a URL is explicitly present.
- Keep achievements as concise bullet points.
- Group skills into meaningful categories (e.g. Languages, Frameworks, Databases, Cloud, Tools).

Resume text:
---
{resume_text}
---

Return only the JSON object now:"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert resume parser. You extract structured data from resume text and return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Use a higher token limit for resume parsing
        import requests
        response_text = self._call_groq_raw(messages)

        if not response_text:
            raise RuntimeError("Groq returned an empty response. Check your API key.")

        return self._parse_json(response_text)

    def _call_groq_raw(self, messages: list) -> str | None:
        """Direct Groq call with higher token limit for resume parsing."""
        import requests

        if not self.ai.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        try:
            response = requests.post(
                self.ai.base_url,
                headers={
                    "Authorization": f"Bearer {self.ai.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.ai.model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Groq call failed: {e}")
            return None

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Extract and parse JSON from Groq response."""
        text = text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        # Find the outermost JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON object found in Groq response: {text[:200]}")

        return json.loads(text[start:end])
