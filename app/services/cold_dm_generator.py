"""Cold DM email body generator."""
from typing import Dict, Any
from jinja2 import Template
from loguru import logger


class ColdDMGenerator:
    """Generate personalized cold DM email bodies."""
    
    def generate(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        tone: str = "professional"
    ) -> str:
        """
        Generate cold DM email body.
        
        Args:
            user_profile: User's profile data
            job_data: Job description and details
            tone: Email tone (professional, friendly, enthusiastic)
            
        Returns:
            HTML email body
        """
        # For now, use template-based generation
        # TODO: Integrate with AI service for dynamic generation
        
        cold_dm_text = self._generate_template_based(user_profile, job_data, tone)
        html_body = self._format_as_html(cold_dm_text, user_profile)
        
        logger.info(f"Generated cold DM for {job_data.get('title')}")
        return html_body
    
    def _generate_template_based(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        tone: str
    ) -> str:
        """Generate cold DM using templates."""
        
        templates = {
            "professional": """
Dear {company} Hiring Team,

I am writing to express my strong interest in the {role} position at {company}. With {experience} and a proven track record in {skills}, I am confident I can contribute significantly to your team.

In my recent work, I have {achievement}. I am particularly drawn to this opportunity because {reason}.

I have attached my resume and cover letter for your review. I would welcome the opportunity to discuss how my background and skills align with your needs.

Thank you for considering my application. I look forward to hearing from you.
            """,
            "friendly": """
Hi {company} team,

I'm excited to apply for the {role} position! With my background in {skills} and {experience}, I believe I'd be a great fit for your team.

What really caught my eye about this role is {reason}. In my recent projects, I've {achievement}, and I'm eager to bring that same energy and expertise to {company}.

I've attached my resume and cover letter with more details about my experience. Would love to chat more about how I can contribute to your team!

Looking forward to connecting.
            """,
            "enthusiastic": """
Hello {company} Team!

I'm thrilled to apply for the {role} position at {company}! This opportunity perfectly aligns with my passion for {skills} and my {experience}.

I'm particularly excited about {reason}. Recently, I {achievement}, and I can't wait to bring that same drive and innovation to your team.

Please find my resume and cover letter attached. I'd be honored to discuss how my skills and enthusiasm can contribute to {company}'s success.

Thank you for this opportunity – I'm looking forward to hearing from you!
            """
        }
        
        template_text = templates.get(tone, templates["professional"])
        
        # Fill in placeholders
        cold_dm = template_text.format(
            company=job_data.get('company', 'your company'),
            role=job_data.get('title', 'this position'),
            experience=user_profile.get('professional_summary', 'relevant experience'),
            skills=', '.join(user_profile.get('top_skills', [])[:3]),
            achievement='delivered impactful results',
            reason='the innovative work your team is doing'
        )
        
        return cold_dm.strip()
    
    def _format_as_html(self, text: str, user_profile: Dict[str, Any]) -> str:
        """Format plain text as HTML email."""
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .content { margin: 20px 0; }
        .content p { margin: 15px 0; }
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
            {% if linkedin %}<a href="{{ linkedin }}">LinkedIn Profile</a><br>{% endif %}
            {% if github %}<a href="{{ github }}">GitHub Profile</a>{% endif %}
            </p>
        </div>
    </div>
</body>
</html>
        """)
        
        # Convert plain text paragraphs to HTML
        paragraphs = text.strip().split('\n\n')
        body_html = '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
        
        return template.render(
            body_text=body_html,
            name=user_profile.get('full_name', ''),
            email=user_profile.get('email', ''),
            phone=user_profile.get('phone', ''),
            linkedin=user_profile.get('linkedin_url', ''),
            github=user_profile.get('github_url', '')
        )
