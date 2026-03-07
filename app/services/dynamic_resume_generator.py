"""Dynamic resume generator with role-specific projects and LaTeX PDF generation."""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Template
from loguru import logger
import uuid
from datetime import datetime

from app.services.ai_service import AIService

# Role-specific template projects used when the user has no projects or AI selection is disabled
_ROLE_PROJECTS: Dict[str, Any] = {
    "Web Developer": {
        "projects": [
            {
                "title": "Full-Stack E-Commerce Platform",
                "description": "Built a scalable e-commerce platform with React, Node.js, and PostgreSQL",
                "technologies": ["React", "Node.js", "PostgreSQL", "Redis"],
                "achievements": ["Handled 10k+ concurrent users", "99.9% uptime"],
            },
            {
                "title": "Real-Time Chat Application",
                "description": "Developed a WebSocket-based chat app with rooms and file sharing",
                "technologies": ["Socket.io", "Express", "MongoDB"],
                "achievements": ["Sub-100ms message latency", "Support for 500+ concurrent connections"],
            },
            {
                "title": "CI/CD Pipeline Automation",
                "description": "Automated deployment pipeline reducing release time by 70%",
                "technologies": ["Docker", "GitHub Actions", "AWS"],
                "achievements": ["70% faster releases", "Zero-downtime deployments"],
            },
        ]
    },
    "ML Engineer": {
        "projects": [
            {
                "title": "NLP Sentiment Analysis Pipeline",
                "description": "End-to-end sentiment analysis system using transformer models",
                "technologies": ["Python", "PyTorch", "HuggingFace", "FastAPI"],
                "achievements": ["94% accuracy", "Processes 1M records/day"],
            },
            {
                "title": "Recommendation Engine",
                "description": "Collaborative filtering recommendation system for an e-commerce platform",
                "technologies": ["Python", "Scikit-learn", "Apache Spark", "Redis"],
                "achievements": ["15% increase in CTR", "Sub-50ms inference"],
            },
            {
                "title": "MLOps Model Monitoring Platform",
                "description": "Built automated model drift detection and retraining pipeline",
                "technologies": ["MLflow", "Kubeflow", "Prometheus", "Grafana"],
                "achievements": ["Reduced model degradation incidents by 80%"],
            },
        ]
    },
    "Data Scientist": {
        "projects": [
            {
                "title": "Customer Churn Prediction Model",
                "description": "Gradient boosting model predicting customer churn with 91% accuracy",
                "technologies": ["Python", "XGBoost", "Pandas", "Tableau"],
                "achievements": ["Saved $2M annually", "91% accuracy"],
            },
            {
                "title": "A/B Testing Framework",
                "description": "Statistical A/B testing framework for product experimentation",
                "technologies": ["Python", "Statsmodels", "SQL", "Airflow"],
                "achievements": ["Reduced experiment cycle time by 40%"],
            },
            {
                "title": "Sales Forecasting Dashboard",
                "description": "Time-series forecasting dashboard with ARIMA and Prophet models",
                "technologies": ["Python", "Prophet", "Plotly", "PostgreSQL"],
                "achievements": ["8% MAPE on 90-day forecasts"],
            },
        ]
    },
    "DevOps Engineer": {
        "projects": [
            {
                "title": "Kubernetes Multi-Cluster Management",
                "description": "Managed 50+ microservices across 3 Kubernetes clusters",
                "technologies": ["Kubernetes", "Helm", "Terraform", "ArgoCD"],
                "achievements": ["99.99% uptime", "40% cost reduction"],
            },
            {
                "title": "Infrastructure as Code Migration",
                "description": "Migrated legacy infrastructure to fully automated Terraform IaC",
                "technologies": ["Terraform", "AWS", "Ansible", "Jenkins"],
                "achievements": ["90% faster provisioning", "Zero config drift"],
            },
            {
                "title": "Observability Stack",
                "description": "Deployed centralized logging and monitoring across all services",
                "technologies": ["Prometheus", "Grafana", "ELK Stack", "PagerDuty"],
                "achievements": ["MTTR reduced by 60%"],
            },
        ]
    },
}

_DEFAULT_PROJECTS = {
    "projects": [
        {
            "title": "Scalable API Service",
            "description": "RESTful API handling high-throughput workloads",
            "technologies": ["Python", "FastAPI", "PostgreSQL"],
            "achievements": ["10k req/s throughput", "99.9% uptime"],
        },
        {
            "title": "Automation Tool",
            "description": "Internal automation tool reducing manual effort by 60%",
            "technologies": ["Python", "Celery", "Redis"],
            "achievements": ["60% time saved", "Used by 50+ team members"],
        },
        {
            "title": "Data Pipeline",
            "description": "ETL pipeline processing and transforming large datasets",
            "technologies": ["Python", "Apache Airflow", "SQL"],
            "achievements": ["Processes 5M records daily"],
        },
    ]
}


def get_projects_for_role(role: str) -> Dict[str, Any]:
    """Return template projects for a given role, falling back to defaults."""
    return _ROLE_PROJECTS.get(role, _DEFAULT_PROJECTS)


def get_all_roles() -> List[str]:
    """Return all roles that have predefined project templates."""
    return list(_ROLE_PROJECTS.keys())


class DynamicResumeGenerator:
    """Generate dynamic resumes with AI-selected projects and LaTeX PDF compilation."""
    
    def __init__(self):
        """Initialize resume generator."""
        self.ai_service = AIService()
        self.template_path = Path("app/templates/resume_template.tex")
        self.output_dir = Path("uploads/resumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_resume(
        self,
        user_data: Dict[str, Any],
        target_role: str,
        user_projects: Optional[List[Dict[str, Any]]] = None,
        use_ai_selection: bool = True,
        output_format: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Generate dynamic resume with role-specific projects.
        
        Args:
            user_data: User profile data (name, email, skills, experience, etc.)
            target_role: Target job role (e.g., "Web Developer", "ML Engineer")
            user_projects: User's actual projects (optional)
            use_ai_selection: Whether to use AI for project selection
            output_format: "pdf" or "tex"
            
        Returns:
            Dictionary with file paths and metadata
        """
        try:
            logger.info(f"Generating resume for role: {target_role}")
            
            # Step 1: Get role-specific template projects
            role_data = get_projects_for_role(target_role)
            template_projects = role_data.get("projects", [])
            
            # Step 2: Select projects (AI or template)
            if use_ai_selection and user_projects:
                # Use AI to select from user's actual projects
                selected_projects = self._ai_select_projects(
                    user_projects=user_projects,
                    target_role=target_role,
                    template_projects=template_projects
                )
            elif user_projects:
                # Use user's projects without AI
                selected_projects = user_projects[:3]
            else:
                # Use template projects
                selected_projects = template_projects[:3]
            
            # Step 3: Format projects for LaTeX
            formatted_projects = self._format_projects_for_latex(selected_projects)
            
            # Step 4: Prepare resume data
            resume_data = self._prepare_resume_data(
                user_data=user_data,
                projects=formatted_projects,
                target_role=target_role
            )
            
            # Step 5: Generate LaTeX file
            resume_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{target_role.replace(' ', '_')}_{timestamp}_{resume_id}"
            
            tex_path = self._generate_latex_file(resume_data, filename)
            
            # Step 6: Compile to PDF if requested
            if output_format == "pdf":
                pdf_path = self._compile_to_pdf(tex_path)
                
                return {
                    "success": True,
                    "resume_id": resume_id,
                    "target_role": target_role,
                    "pdf_path": str(pdf_path) if pdf_path else None,
                    "tex_path": str(tex_path),
                    "selected_projects": [p.get("title") for p in selected_projects],
                    "generation_method": "ai_selected" if use_ai_selection else "template"
                }
            else:
                return {
                    "success": True,
                    "resume_id": resume_id,
                    "target_role": target_role,
                    "tex_path": str(tex_path),
                    "selected_projects": [p.get("title") for p in selected_projects],
                    "generation_method": "ai_selected" if use_ai_selection else "template"
                }
                
        except Exception as e:
            logger.error(f"Error generating resume: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _ai_select_projects(
        self,
        user_projects: List[Dict[str, Any]],
        target_role: str,
        template_projects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use AI to select and adapt projects for the target role."""
        try:
            # Create prompt for AI
            prompt = f"""You are a resume expert. Select and adapt the 3 most relevant projects for a {target_role} position.

User's Actual Projects:
{self._format_projects_for_prompt(user_projects)}

Template Projects for {target_role}:
{self._format_projects_for_prompt(template_projects)}

Task:
1. Select the 3 most relevant projects from the user's actual projects
2. If user projects are relevant, use them
3. If user projects are not relevant enough, adapt template projects to match user's skills
4. Ensure projects demonstrate skills needed for {target_role}

Return ONLY a JSON array of 3 projects with this structure:
[
  {{
    "title": "Project Title",
    "description": "One-line description highlighting relevance to {target_role}",
    "technologies": ["Tech1", "Tech2", "Tech3"],
    "achievements": ["Achievement 1", "Achievement 2"]
  }}
]

Return ONLY the JSON array, no other text."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a resume expert who selects the most relevant projects for job applications. You return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Call AI
            response = self.ai_service._call_groq_api(messages, temperature=0.3)
            
            if response:
                # Parse JSON response
                import json
                # Extract JSON from response
                response = response.strip()
                if '[' in response and ']' in response:
                    start = response.index('[')
                    end = response.rindex(']') + 1
                    json_str = response[start:end]
                    selected_projects = json.loads(json_str)
                    
                    logger.info(f"AI selected {len(selected_projects)} projects")
                    return selected_projects
            
            # Fallback to user projects
            logger.warning("AI selection failed, using user projects")
            return user_projects[:3]
            
        except Exception as e:
            logger.error(f"Error in AI project selection: {e}")
            return user_projects[:3] if user_projects else template_projects[:3]
    
    def _format_projects_for_prompt(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects for AI prompt."""
        lines = []
        for i, project in enumerate(projects, 1):
            lines.append(f"{i}. {project.get('title', 'Untitled')}")
            lines.append(f"   Description: {project.get('description', 'No description')}")
            if project.get('technologies'):
                lines.append(f"   Technologies: {', '.join(project.get('technologies', []))}")
            if project.get('achievements'):
                lines.append(f"   Achievements: {'; '.join(project.get('achievements', [])[:2])}")
            lines.append("")
        return "\n".join(lines)
    
    def _format_projects_for_latex(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format projects for LaTeX template."""
        formatted = []
        for project in projects:
            formatted.append({
                "title": project.get("title", ""),
                "description": project.get("description", ""),
                "url": project.get("project_url") or project.get("url", "")
            })
        return formatted
    
    def _prepare_resume_data(
        self,
        user_data: Dict[str, Any],
        projects: List[Dict[str, Any]],
        target_role: str
    ) -> Dict[str, Any]:
        """Prepare complete data for resume template."""
        # Format skills to ensure items is a list
        skills = user_data.get("skills", [])
        formatted_skills = []
        for skill in skills:
            if isinstance(skill, dict):
                items = skill.get("items", [])
                if isinstance(items, list):
                    formatted_skills.append({
                        "category": skill.get("category", "Skills"),
                        "items": ", ".join(items)
                    })
                else:
                    formatted_skills.append({
                        "category": skill.get("category", "Skills"),
                        "items": str(items)
                    })
        
        return {
            "name": user_data.get("full_name", "Your Name"),
            "phone": user_data.get("phone", "+1234567890"),
            "location": user_data.get("location", "City, State"),
            "email": user_data.get("email", "email@example.com"),
            "linkedin_url": user_data.get("linkedin_url", "https://linkedin.com"),
            "linkedin_display": self._extract_display_url(user_data.get("linkedin_url", "")),
            "website_url": user_data.get("website_url") or user_data.get("github_url", "https://github.com"),
            "website_display": self._extract_display_url(user_data.get("website_url") or user_data.get("github_url", "")),
            "experience_years": user_data.get("experience_years", "3+"),
            "primary_skills": ", ".join(user_data.get("primary_skills", ["Python", "JavaScript", "React"])[:3]),
            "target_role": target_role,
            "education": user_data.get("education", []),
            "skills": formatted_skills,
            "experience": user_data.get("experience", []),
            "projects": projects,
            "extra_curricular": user_data.get("extra_curricular", []),
            "leadership": user_data.get("leadership", [])
        }
    
    def _extract_display_url(self, url: str) -> str:
        """Extract display-friendly URL."""
        if not url:
            return ""
        # Remove protocol
        display = url.replace("https://", "").replace("http://", "")
        # Remove trailing slash
        display = display.rstrip("/")
        return display
    
    def _generate_latex_file(self, resume_data: Dict[str, Any], filename: str) -> Path:
        """Generate LaTeX file from template."""
        try:
            # Load and render template with custom Jinja2 environment
            from jinja2 import Environment, FileSystemLoader
            
            # Create Jinja2 environment with LaTeX-friendly delimiters
            env = Environment(
                loader=FileSystemLoader('app/templates'),
                block_start_string='\\BLOCK{',
                block_end_string='}',
                variable_start_string='\\VAR{',
                variable_end_string='}',
                comment_start_string='\\#{',
                comment_end_string='}',
                line_statement_prefix='%%',
                line_comment_prefix='%#',
                trim_blocks=True,
                autoescape=False
            )
            
            # Load template
            template = env.get_template('resume_template.tex')
            latex_content = template.render(**resume_data)
            
            # Write to file
            tex_path = self.output_dir / f"{filename}.tex"
            with open(tex_path, 'w') as f:
                f.write(latex_content)
            
            logger.info(f"Generated LaTeX file: {tex_path}")
            return tex_path
            
        except Exception as e:
            logger.error(f"Error generating LaTeX file: {e}")
            raise
    
    def _compile_to_pdf(self, tex_path: Path) -> Optional[Path]:
        """Compile LaTeX file to PDF using pdflatex."""
        try:
            # Check if pdflatex is available
            if not self._check_pdflatex():
                logger.warning("pdflatex not available, skipping PDF compilation")
                return None
            
            # Compile LaTeX to PDF
            output_dir = tex_path.parent
            
            # Run pdflatex twice for proper references
            for i in range(2):
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-output-directory", str(output_dir),
                        str(tex_path)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logger.error(f"pdflatex compilation failed: {result.stderr}")
                    return None
            
            # Clean up auxiliary files
            pdf_path = tex_path.with_suffix('.pdf')
            self._cleanup_latex_files(tex_path)
            
            if pdf_path.exists():
                logger.info(f"Generated PDF: {pdf_path}")
                return pdf_path
            else:
                logger.error("PDF file not generated")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("PDF compilation timed out")
            return None
        except Exception as e:
            logger.error(f"Error compiling PDF: {e}")
            return None
    
    def _check_pdflatex(self) -> bool:
        """Check if pdflatex is available."""
        try:
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _cleanup_latex_files(self, tex_path: Path):
        """Clean up auxiliary LaTeX files."""
        extensions = ['.aux', '.log', '.out']
        for ext in extensions:
            aux_file = tex_path.with_suffix(ext)
            if aux_file.exists():
                try:
                    aux_file.unlink()
                except:
                    pass
    
    def get_available_roles(self) -> List[str]:
        """Get list of available job roles."""
        return get_all_roles()


# Global instance
dynamic_resume_generator = DynamicResumeGenerator()
