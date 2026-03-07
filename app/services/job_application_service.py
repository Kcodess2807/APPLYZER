"""Service for complete job application workflow with document generation."""
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import asyncio
from datetime import datetime
import uuid

from app.services.gmail_service import GmailService
from app.services.email_tracker_service import EmailTrackerService
from app.services.ai_service import AIService
from app.services.cold_dm_generator import ColdDMGenerator
from app.database.base import get_db
from app.services.project_service import ProjectService


class JobApplicationService:
    """Service for sending job applications with generated documents."""
    
    def __init__(self, spreadsheet_id: str = None):
        """Initialize job application service."""
        self.gmail_service = GmailService()
        self.tracker_service = EmailTrackerService(spreadsheet_id)
        self.ai_service = AIService()
        self.cold_dm_generator = ColdDMGenerator()
        self.output_dir = Path("uploads/applications")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def send_job_application(
        self,
        user_id: str,
        job_data: Dict[str, Any],
        user_data: Dict[str, Any],
        generate_documents: bool = True,
        email_tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Send complete job application with generated documents.
        
        Args:
            user_id: User's ID
            job_data: Job details (title, company, description, hr_email, etc.)
            user_data: User profile data
            generate_documents: Whether to generate and attach documents
            email_tone: Tone for email (professional, friendly, enthusiastic)
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            recipient = job_data.get('hr_email') or job_data.get('email')
            if not recipient:
                return {
                    'success': False,
                    'error': 'No recipient email provided'
                }
            
            job_title = job_data.get('title', 'Position')
            company = job_data.get('company', 'Company')
            job_description = job_data.get('description', '')
            
            logger.info(f"Processing application for {job_title} at {company}")
            
            # Step 1: Select relevant projects using AI
            selected_projects = []
            if generate_documents:
                selected_projects = await self._select_relevant_projects(
                    user_id=user_id,
                    job_title=job_title,
                    job_description=job_description
                )
                logger.info(f"Selected {len(selected_projects)} relevant projects")
            
            # Step 2: Generate documents
            attachments = []
            if generate_documents:
                attachments = await self._generate_documents(
                    user_data=user_data,
                    job_data=job_data,
                    selected_projects=selected_projects,
                    job_title=job_title,
                    company=company
                )
                logger.info(f"Generated {len(attachments)} documents")
            
            # Step 3: Generate email body
            email_body = self.cold_dm_generator.generate(
                user_profile=user_data,
                job_data=job_data,
                tone=email_tone
            )
            
            # Step 4: Create subject line
            subject = f"Application for {job_title} Position"
            if company:
                subject = f"Application for {job_title} at {company}"
            
            # Step 5: Send email with attachments
            result = self.gmail_service.send_email(
                to=recipient,
                subject=subject,
                body_html=email_body,
                attachments=attachments
            )
            
            if result.get('success'):
                # Track in Google Sheets
                thread_id = result.get('thread_id')
                message_id = result.get('message_id')
                
                self.tracker_service.add_email_tracking(
                    email=recipient,
                    subject=subject,
                    thread_id=thread_id,
                    message_id=message_id,
                    status="SENT"
                )
                
                logger.info(f"✓ Application sent to {recipient}")
                
                return {
                    'success': True,
                    'email': recipient,
                    'subject': subject,
                    'thread_id': thread_id,
                    'message_id': message_id,
                    'attachments': [Path(a).name for a in attachments],
                    'selected_projects': [p.get('title') for p in selected_projects]
                }
            else:
                logger.error(f"✗ Failed to send application: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error in job application: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_bulk_applications(
        self,
        user_id: str,
        jobs: List[Dict[str, Any]],
        user_data: Dict[str, Any],
        generate_documents: bool = True,
        email_tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Send applications to multiple jobs with generated documents.
        
        Args:
            user_id: User's ID
            jobs: List of job dictionaries
            user_data: User profile data
            generate_documents: Whether to generate documents for each job
            email_tone: Email tone
            
        Returns:
            Summary of results
        """
        results = []
        errors = []
        
        logger.info(f"Starting bulk applications for {len(jobs)} jobs")
        
        for i, job in enumerate(jobs):
            try:
                # Rate limiting
                if i > 0 and i % 5 == 0:
                    logger.info(f"Processed {i} applications, pausing...")
                    await asyncio.sleep(3)
                
                result = await self.send_job_application(
                    user_id=user_id,
                    job_data=job,
                    user_data=user_data,
                    generate_documents=generate_documents,
                    email_tone=email_tone
                )
                
                if result.get('success'):
                    results.append(result)
                else:
                    errors.append({
                        'job': job.get('title'),
                        'company': job.get('company'),
                        'error': result.get('error')
                    })
                
                # Small delay between applications
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing job {job.get('title')}: {e}")
                errors.append({
                    'job': job.get('title'),
                    'company': job.get('company'),
                    'error': str(e)
                })
        
        success_count = len(results)
        failed_count = len(errors)
        
        logger.info(f"Bulk applications complete: {success_count} sent, {failed_count} failed")
        
        return {
            'success': success_count > 0,
            'total_sent': success_count,
            'failed': failed_count,
            'results': results,
            'errors': errors if errors else None
        }
    
    async def _select_relevant_projects(
        self,
        user_id: str,
        job_title: str,
        job_description: str,
        max_projects: int = 3
    ) -> List[Dict[str, Any]]:
        """Select relevant projects using AI."""
        try:
            # Get database session
            db = next(get_db())
            project_service = ProjectService(db)
            
            # Get AI-selected projects
            selected_projects = project_service.select_relevant_projects_for_job(
                user_id=user_id,
                job_description=job_description,
                job_title=job_title,
                max_projects=max_projects
            )
            
            # Convert to dict format
            projects_data = []
            for project in selected_projects:
                projects_data.append({
                    "id": str(project.id),
                    "title": project.title,
                    "description": project.description,
                    "technologies": project.technologies or [],
                    "skills_demonstrated": project.skills_demonstrated or [],
                    "achievements": project.achievements or [],
                    "project_url": project.project_url
                })
            
            return projects_data
            
        except Exception as e:
            logger.warning(f"Could not select projects with AI: {e}")
            return []
    
    async def _generate_documents(
        self,
        user_data: Dict[str, Any],
        job_data: Dict[str, Any],
        selected_projects: List[Dict[str, Any]],
        job_title: str,
        company: str
    ) -> List[str]:
        """Generate resume, cover letter, and save them as files."""
        attachments = []
        
        try:
            # Create unique application ID
            app_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generate resume (simple text version for now)
            resume_path = await self._generate_resume_file(
                user_data=user_data,
                selected_projects=selected_projects,
                job_title=job_title,
                filename=f"resume_{company}_{app_id}.txt"
            )
            if resume_path:
                attachments.append(str(resume_path))
            
            # Generate cover letter
            cover_letter_path = await self._generate_cover_letter_file(
                user_data=user_data,
                job_data=job_data,
                selected_projects=selected_projects,
                filename=f"cover_letter_{company}_{app_id}.txt"
            )
            if cover_letter_path:
                attachments.append(str(cover_letter_path))
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error generating documents: {e}")
            return []
    
    async def _generate_resume_file(
        self,
        user_data: Dict[str, Any],
        selected_projects: List[Dict[str, Any]],
        job_title: str,
        filename: str
    ) -> Optional[Path]:
        """Generate resume file."""
        try:
            file_path = self.output_dir / filename
            
            # Generate resume content
            content = self._format_resume_content(user_data, selected_projects, job_title)
            
            # Write to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Generated resume: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating resume file: {e}")
            return None
    
    async def _generate_cover_letter_file(
        self,
        user_data: Dict[str, Any],
        job_data: Dict[str, Any],
        selected_projects: List[Dict[str, Any]],
        filename: str
    ) -> Optional[Path]:
        """Generate cover letter file using AI."""
        try:
            file_path = self.output_dir / filename
            
            # Generate cover letter using AI
            cover_letter = await self._generate_ai_cover_letter(
                user_data=user_data,
                job_data=job_data,
                selected_projects=selected_projects
            )
            
            # Write to file
            with open(file_path, 'w') as f:
                f.write(cover_letter)
            
            logger.info(f"Generated cover letter: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating cover letter file: {e}")
            return None
    
    def _format_resume_content(
        self,
        user_data: Dict[str, Any],
        selected_projects: List[Dict[str, Any]],
        job_title: str
    ) -> str:
        """Format resume content as text."""
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"{user_data.get('full_name', 'Applicant').upper()}")
        lines.append("=" * 60)
        lines.append(f"Email: {user_data.get('email', '')}")
        lines.append(f"Phone: {user_data.get('phone', '')}")
        if user_data.get('linkedin_url'):
            lines.append(f"LinkedIn: {user_data.get('linkedin_url')}")
        if user_data.get('github_url'):
            lines.append(f"GitHub: {user_data.get('github_url')}")
        lines.append("")
        
        # Professional Summary
        if user_data.get('professional_summary'):
            lines.append("PROFESSIONAL SUMMARY")
            lines.append("-" * 60)
            lines.append(user_data.get('professional_summary'))
            lines.append("")
        
        # Skills
        if user_data.get('skills'):
            lines.append("SKILLS")
            lines.append("-" * 60)
            for skill_category in user_data.get('skills', []):
                category = skill_category.get('category', 'Skills')
                items = skill_category.get('items', [])
                lines.append(f"{category}: {', '.join(items)}")
            lines.append("")
        
        # Experience
        if user_data.get('experiences'):
            lines.append("EXPERIENCE")
            lines.append("-" * 60)
            for exp in user_data.get('experiences', []):
                lines.append(f"{exp.get('role')} - {exp.get('company')}")
                lines.append(f"{exp.get('duration')} | {exp.get('location', '')}")
                for achievement in exp.get('achievements', []):
                    lines.append(f"  • {achievement}")
                lines.append("")
        
        # Selected Projects
        if selected_projects:
            lines.append("RELEVANT PROJECTS")
            lines.append("-" * 60)
            for project in selected_projects:
                lines.append(f"{project.get('title')}")
                lines.append(f"  {project.get('description')}")
                if project.get('technologies'):
                    lines.append(f"  Technologies: {', '.join(project.get('technologies', []))}")
                if project.get('achievements'):
                    for achievement in project.get('achievements', []):
                        lines.append(f"  • {achievement}")
                lines.append("")
        
        # Education
        if user_data.get('education'):
            lines.append("EDUCATION")
            lines.append("-" * 60)
            for edu in user_data.get('education', []):
                lines.append(f"{edu.get('degree')} - {edu.get('institution')}")
                lines.append(f"{edu.get('year')}")
                if edu.get('coursework'):
                    lines.append(f"Relevant Coursework: {edu.get('coursework')}")
                lines.append("")
        
        return "\n".join(lines)
    
    async def _generate_ai_cover_letter(
        self,
        user_data: Dict[str, Any],
        job_data: Dict[str, Any],
        selected_projects: List[Dict[str, Any]]
    ) -> str:
        """Generate cover letter using AI."""
        try:
            job_title = job_data.get('title', 'Position')
            company = job_data.get('company', 'Company')
            job_description = job_data.get('description', '')
            
            # Create prompt for AI
            prompt = f"""Write a professional cover letter for the following job application:

Job Title: {job_title}
Company: {company}
Job Description: {job_description}

Applicant Information:
Name: {user_data.get('full_name', 'Applicant')}
Professional Summary: {user_data.get('professional_summary', '')}

Relevant Projects:
{self._format_projects_for_prompt(selected_projects)}

Requirements:
1. Professional tone
2. Highlight relevant experience and projects
3. Show enthusiasm for the role
4. Keep it concise (3-4 paragraphs)
5. Include proper greeting and closing
6. Do NOT include applicant's contact information (will be added separately)

Write the cover letter now:"""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert cover letter writer specializing in technical positions. You write compelling, professional cover letters that highlight relevant experience and demonstrate genuine interest."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Call AI
            cover_letter = self.ai_service._call_groq_api(messages, temperature=0.7)
            
            if cover_letter:
                # Add contact information
                header = f"{user_data.get('full_name', '')}\n"
                header += f"{user_data.get('email', '')}\n"
                header += f"{user_data.get('phone', '')}\n"
                if user_data.get('linkedin_url'):
                    header += f"{user_data.get('linkedin_url')}\n"
                header += f"\n{datetime.now().strftime('%B %d, %Y')}\n\n"
                
                return header + cover_letter
            else:
                return self._generate_template_cover_letter(user_data, job_data)
                
        except Exception as e:
            logger.error(f"Error generating AI cover letter: {e}")
            return self._generate_template_cover_letter(user_data, job_data)
    
    def _format_projects_for_prompt(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects for AI prompt."""
        if not projects:
            return "No specific projects provided"
        
        lines = []
        for project in projects:
            lines.append(f"- {project.get('title')}: {project.get('description')}")
            if project.get('technologies'):
                lines.append(f"  Technologies: {', '.join(project.get('technologies', []))}")
        
        return "\n".join(lines)
    
    def _generate_template_cover_letter(
        self,
        user_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """Generate template-based cover letter as fallback."""
        job_title = job_data.get('title', 'Position')
        company = job_data.get('company', 'Company')
        
        return f"""{user_data.get('full_name', '')}
{user_data.get('email', '')}
{user_data.get('phone', '')}

{datetime.now().strftime('%B %d, %Y')}

Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my background in software development and proven track record of delivering high-quality solutions, I am confident I would be a valuable addition to your team.

{user_data.get('professional_summary', 'I bring relevant experience and skills to this role.')}

I am particularly excited about this opportunity at {company} and would welcome the chance to discuss how my skills and experience align with your needs.

Thank you for considering my application. I look forward to the opportunity to speak with you.

Sincerely,
{user_data.get('full_name', '')}
"""
