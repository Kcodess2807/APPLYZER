"""Cold DM email body generator."""
from typing import Dict, Any
from jinja2 import Template
from loguru import logger

from app.services.ai_service import AIService


class ColdDMGenerator:
    """Generate personalized cold DM email bodies using AI."""

    def __init__(self):
        self.ai_service = AIService()

    def generate(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        tone: str = "professional"
    ) -> str:
        """
        Generate cold DM email body with AI.

        Format:
          - Brief intro (1–2 sentences)
          - 3 bullet points: what the candidate brings to the table
          - Closing line

        Returns HTML email body.
        """
        cold_dm_text = self._generate_with_ai(user_profile, job_data, tone)
        html_body = self._format_as_html(cold_dm_text, user_profile)
        logger.info(f"Generated cold DM for {job_data.get('title')} at {job_data.get('company')}")
        return html_body

    def _generate_with_ai(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        tone: str,
    ) -> str:
        name = user_profile.get("full_name", "I")
        summary = user_profile.get("professional_summary", "")
        experience = user_profile.get("experience", [])
        skills = user_profile.get("skills", [])
        experience_years = user_profile.get("experience_years", "")

        # Flatten skills for the prompt
        all_skills = []
        for s in skills:
            if isinstance(s, dict):
                all_skills.extend(s.get("items", []))
            elif isinstance(s, str):
                all_skills.append(s)

        # Summarise experience for the prompt
        exp_summary = "\n".join(
            f"- {e.get('role')} at {e.get('company')} ({e.get('duration', '')}): "
            + "; ".join(e.get("achievements", [])[:2])
            for e in experience[:3]
        )

        prompt = f"""You are writing a cold job-application email on behalf of {name}.

Candidate profile:
- Summary: {summary}
- Experience years: {experience_years}
- Key skills: {', '.join(all_skills[:10])}
- Recent experience:
{exp_summary}

Target role: {job_data.get('title', 'this position')}
Company: {job_data.get('company', 'the company')}
Job description snippet: {(job_data.get('description') or '')[:400]}

Write a concise, {tone} cold email body in EXACTLY this structure:
1. One short introductory paragraph (2 sentences max): who you are and why you are reaching out.
2. Three bullet points starting with "• " — each one specific thing you bring to the table, grounded in the candidate's actual experience and skills above. Make them punchy and concrete.
3. One short closing paragraph: express interest in a conversation, no fluff.

Rules:
- Do NOT include subject line, salutation, or sign-off — those are added separately.
- Do NOT use placeholders like [Company] or [Role] — use the real values.
- Keep total length under 150 words.
- Return plain text only."""

        messages = [
            {"role": "system", "content": "You write concise, impactful cold job-application emails. You follow the exact format requested."},
            {"role": "user", "content": prompt},
        ]

        response = self.ai_service._call_groq_api(messages, temperature=0.6)
        if response and response.strip():
            return response.strip()

        # Fallback
        logger.warning("AI cold DM generation failed, using fallback")
        return self._fallback(user_profile, job_data)

    def _fallback(self, user_profile: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        name = user_profile.get("full_name", "I")
        role = job_data.get("title", "this role")
        company = job_data.get("company", "your company")
        summary = user_profile.get("professional_summary", "relevant experience in software engineering")
        skills = user_profile.get("skills", [])
        top_skills = []
        for s in skills:
            if isinstance(s, dict):
                top_skills.extend(s.get("items", [])[:2])
        skills_str = ", ".join(top_skills[:4]) or "Python, APIs, databases"

        return (
            f"I'm {name}, a software engineer interested in the {role} position at {company}.\n\n"
            f"• {summary}\n"
            f"• Hands-on experience with {skills_str}\n"
            f"• Track record of delivering production-grade systems on time\n\n"
            f"I'd love to connect and learn more about the role — happy to share more details."
        )

    def _format_as_html(self, text: str, user_profile: Dict[str, Any]) -> str:
        """Convert plain text (with • bullets) to HTML email."""
        lines = text.strip().split('\n')
        html_parts = []
        in_list = False

        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                continue
            if line.startswith('• '):
                if not in_list:
                    html_parts.append('<ul style="margin:10px 0;padding-left:20px;">')
                    in_list = True
                html_parts.append(f'<li style="margin:4px 0;">{line[2:]}</li>')
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append(f'<p style="margin:10px 0;">{line}</p>')

        if in_list:
            html_parts.append('</ul>')

        body_html = '\n'.join(html_parts)

        template = Template("""<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .signature { margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; }
        a { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            {{ body_text | safe }}
        </div>
        <div class="signature">
            <p>Best regards,<br>
            <strong>{{ name }}</strong><br>
            {% if email %}<a href="mailto:{{ email }}">{{ email }}</a><br>{% endif %}
            {% if phone %}{{ phone }}<br>{% endif %}
            {% if linkedin %}<a href="{{ linkedin }}">LinkedIn</a>{% endif %}
            {% if github %} &nbsp;|&nbsp; <a href="{{ github }}">GitHub</a>{% endif %}
            </p>
        </div>
    </div>
</body>
</html>""")

        return template.render(
            body_text=body_html,
            name=user_profile.get('full_name', ''),
            email=user_profile.get('email', ''),
            phone=user_profile.get('phone', ''),
            linkedin=user_profile.get('linkedin_url', ''),
            github=user_profile.get('github_url', ''),
        )
