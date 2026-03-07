"""AI service for intelligent project selection and follow-up generation using Groq."""
import json
from typing import List, Dict, Any, Optional
from loguru import logger
import requests

from app.core.config import settings


class AIService:
    """Service for AI-powered features using Groq API."""
    
    def __init__(self):
        """Initialize AI service with Groq API."""
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Updated to current model
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. AI features will not work.")
    
    def _call_groq_api(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """Make API call to Groq."""
        if not self.api_key:
            logger.error("GROQ_API_KEY not configured")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2000
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return None
    
    def select_relevant_projects(
        self,
        projects: List[Dict[str, Any]],
        job_description: str,
        job_title: str,
        max_projects: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Select the most relevant projects for a job application using AI.
        
        Args:
            projects: List of user's projects
            job_description: The job description
            job_title: The job title/role
            max_projects: Maximum number of projects to select
            
        Returns:
            List of selected projects with relevance scores
        """
        if not projects:
            logger.warning("No projects provided for selection")
            return []
        
        if not self.api_key:
            logger.warning("AI not configured, returning first projects")
            return projects[:max_projects]
        
        logger.info(f"Selecting relevant projects for: {job_title}")
        
        # Prepare project summaries for AI
        project_summaries = []
        for idx, project in enumerate(projects):
            summary = {
                "index": idx,
                "title": project.get("title", ""),
                "description": project.get("description", ""),
                "technologies": project.get("technologies", []),
                "skills_demonstrated": project.get("skills_demonstrated", []),
                "achievements": project.get("achievements", [])
            }
            project_summaries.append(summary)
        
        # Create prompt for AI
        prompt = f"""You are an expert career advisor helping select the most relevant projects for a job application.

Job Title: {job_title}

Job Description:
{job_description}

Available Projects:
{json.dumps(project_summaries, indent=2)}

Task: Analyze the job requirements and select the {max_projects} most relevant projects that best demonstrate the candidate's fit for this role. Consider:
1. Technical skills match (technologies, frameworks)
2. Relevant experience and achievements
3. Problem-solving abilities demonstrated
4. Impact and scale of projects

Return ONLY a JSON array of the selected project indices (0-based) in order of relevance, like this:
[0, 2, 4]

Do not include any explanation, just the JSON array."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert career advisor specializing in matching candidate projects to job requirements. You analyze technical skills, achievements, and relevance to provide the best project selections."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Call AI
        response = self._call_groq_api(messages, temperature=0.3)
        
        if not response:
            logger.warning("AI selection failed, using fallback")
            return projects[:max_projects]
        
        try:
            # Parse AI response
            response = response.strip()
            # Extract JSON array from response
            if '[' in response and ']' in response:
                start = response.index('[')
                end = response.rindex(']') + 1
                json_str = response[start:end]
                selected_indices = json.loads(json_str)
            else:
                selected_indices = json.loads(response)
            
            # Get selected projects
            selected_projects = []
            for idx in selected_indices[:max_projects]:
                if 0 <= idx < len(projects):
                    selected_projects.append(projects[idx])
            
            logger.info(f"AI selected {len(selected_projects)} projects: {[p.get('title') for p in selected_projects]}")
            
            return selected_projects if selected_projects else projects[:max_projects]
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.debug(f"AI response was: {response}")
            return projects[:max_projects]
    
    def generate_followup_email(
        self,
        original_subject: str,
        job_title: str,
        company_name: str,
        followup_count: int,
        user_name: str,
        days_since_sent: int
    ) -> str:
        """
        Generate a personalized follow-up email using AI.
        
        Args:
            original_subject: Subject of the original email
            job_title: The job title applied for
            company_name: Name of the company
            followup_count: Which follow-up this is (1, 2, etc.)
            user_name: Applicant's name
            days_since_sent: Days since last email
            
        Returns:
            HTML formatted follow-up email body
        """
        if not self.api_key:
            logger.warning("AI not configured, using template-based follow-up")
            return self._generate_template_followup(followup_count)
        
        logger.info(f"Generating AI follow-up #{followup_count} for {job_title} at {company_name}")
        
        # Create prompt based on follow-up count
        if followup_count == 1:
            tone_instruction = "polite and professional, expressing continued interest without being pushy"
            context = f"This is the first follow-up after {days_since_sent} days of no response."
        else:
            tone_instruction = "respectful and understanding, acknowledging they may be busy while maintaining interest"
            context = f"This is follow-up #{followup_count} after {days_since_sent} days since the last email."
        
        prompt = f"""Write a professional follow-up email for a job application.

Context:
- Job Title: {job_title}
- Company: {company_name}
- Applicant Name: {user_name}
- {context}
- Original Subject: {original_subject}

Requirements:
1. Keep it brief (3-4 short paragraphs)
2. Tone: {tone_instruction}
3. Reaffirm interest in the position
4. Add value by mentioning willingness to provide additional information
5. Include a clear call-to-action
6. Do NOT include signature (it will be added automatically)
7. Return ONLY the email body in HTML format using <p> tags

Write the follow-up email body now:"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert professional email writer specializing in job application follow-ups. You write concise, professional, and effective follow-up emails that maintain interest without being pushy."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Call AI
        response = self._call_groq_api(messages, temperature=0.7)
        
        if not response:
            logger.warning("AI generation failed, using template")
            return self._generate_template_followup(followup_count)
        
        # Clean up response
        email_body = response.strip()
        
        # Ensure HTML formatting
        if not email_body.startswith('<'):
            # Convert plain text to HTML
            paragraphs = email_body.split('\n\n')
            email_body = '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
        
        logger.info(f"Generated AI follow-up email ({len(email_body)} chars)")
        
        return email_body
    
    def _generate_template_followup(self, followup_count: int) -> str:
        """Fallback template-based follow-up generation."""
        if followup_count == 1:
            return """
            <p>Hi,</p>
            <p>I wanted to follow up on my previous email regarding the opportunity. I remain very interested in this position and would welcome the chance to discuss how my skills and experience align with your needs.</p>
            <p>Please let me know if you need any additional information from my end.</p>
            <p>Thank you for your consideration.</p>
            """
        else:
            return """
            <p>Hi,</p>
            <p>I wanted to reach out one more time regarding my interest in this opportunity. I understand you may be busy, but I remain enthusiastic about the possibility of contributing to your team.</p>
            <p>If the timing isn't right or if you need any additional information, please don't hesitate to let me know.</p>
            <p>Thank you again for your time and consideration.</p>
            """
