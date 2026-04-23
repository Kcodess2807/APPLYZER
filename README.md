# ApplyBot 🤖

> AI-powered job application automation platform that transforms hours of manual work into minutes of intelligent automation.

**ApplyBot** automates your entire job search pipeline: discovers relevant jobs, generates tailored resumes and cover letters, sends personalized applications via Gmail, tracks responses in Google Sheets, and automatically follows up—all powered by AI.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What It Does

> [!WARNING]
> The Frontend UI is currently heavily WIP. The backend is fully functional and can be tested via Swagger UI.

- **Discovers Jobs**: Fetches from RemoteOK, CSV uploads, or manual entry
- **Matches Projects**: AI selects your most relevant projects for each job
- **Generates Documents**: Creates tailored LaTeX resumes and cover letters
- **Sends Applications**: Automated Gmail sending with attachments
- **Tracks Everything**: Google Sheets CRM for all applications
- **Monitors Replies**: Background workers detect responses automatically
- **Follows Up**: Smart follow-up emails after configurable intervals

## 🏗️ Architecture

```mermaid
graph LR
    A[Job Fetcher] --> B[Project Matcher]
    B --> C[Resume Generator Cover Letter]
    C --> D[Human Review / Output]
```

## 📚 Documentation

- **[Intent & Architecture](intent.md)** - Detailed system design and features
- **[System Design](system_design.md)** - Architecture diagrams and data flow
- **[Investor Pitch](INVESTOR_PITCH.md)** - Business model and market analysis
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when running)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (or Supabase account)
- Gmail account with API access
- Google Sheets API access
- Groq API key (for AI features)

### 1. Clone and Install
```bash
git clone https://github.com/yourusername/applybot.git
cd applybot
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:pass@host/applybot

# AI Services
GROQ_API_KEY=your_groq_key

# Gmail API
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# Google Sheets API
SHEETS_CLIENT_ID=your_sheets_client_id
SHEETS_CLIENT_SECRET=your_sheets_client_secret
SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Application
API_BASE_URL=http://localhost:8000
ENABLE_BACKGROUND_WORKERS=true

# Follow-up Settings
FOLLOWUP_DAYS_INTERVAL=5
MAX_FOLLOWUP_COUNT=2
REPLY_CHECK_INTERVAL_MINUTES=30
```

### 3. Initialize Database
```bash
# Run database migrations
alembic upgrade head
```

### 4. Authenticate APIs (One-Time Setup)

```bash
# Authenticate both Gmail and Sheets
./scripts/authenticate_apis.sh

# Or authenticate individually
python scripts/authenticate_sheets.py
curl http://localhost:8000/api/v1/gmail/authenticate  # Open URL in browser

# Verify authentication
python scripts/check_auth_status.py
```

### 5. Start the Server

```bash
# Using Make
make run

# Or directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 7. Running via Swagger UI
Since the frontend is a WIP, you can test the entire pipeline using the built-in Swagger UI:
1. Navigate to `http://localhost:8000/docs`
2. Authenticate the APIs via `/api/v1/gmail/authenticate`
3. Use the `/api/v1/test_generation/quick-test` endpoint for a simulated end-to-end test.

---

## 📖 Usage Examples

### Create a User Profile

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "professional_summary": "Python developer with 3+ years experience"
  }'
```

### Add Projects

```bash
curl -X POST "http://localhost:8000/api/v1/projects/?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-commerce API",
    "description": "RESTful API with payment integration",
    "technologies": ["Python", "FastAPI", "PostgreSQL"],
    "category": "API Development",
    "project_url": "https://github.com/user/ecommerce-api"
  }'
```

### Fetch Jobs

```bash
curl -X POST http://localhost:8000/api/v1/jobs/fetch \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["python", "backend"], "limit_per_source": 50}'
```

### Generate Resume

```bash
curl -X POST http://localhost:8000/api/v1/resume/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "experience_years": "3+",
    "primary_skills": ["Python", "FastAPI"],
    "education": [],
    "skills": []
  }'
```

### Send Job Application (Full Pipeline)

```bash
curl -X POST http://localhost:8000/api/v1/bulk-email/send-job-application \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "job_title": "Backend Engineer",
    "company": "Acme Corp",
    "job_description": "We need a Python developer...",
    "hr_email": "hr@acme.com",
    "generate_documents": true,
    "email_tone": "professional"
  }'
```

### Bulk Apply to Multiple Jobs

```bash
curl -X POST http://localhost:8000/api/v1/applications/bulk-apply \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "job_ids": ["{job_id_1}", "{job_id_2}", "{job_id_3}"],
    "email_tone": "professional"
  }'
```

---

## 🏗️ Project Structure

```
applybot/
├── app/
│   ├── api/v1/endpoints/    # API route handlers
│   ├── agents/              # LangGraph-style AI agents
│   ├── orchestrator/        # Workflow orchestration
│   ├── services/            # Business logic
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── core/                # Config, auth, logging
│   ├── workers/             # Background tasks
│   ├── templates/           # LaTeX and email templates
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
│   ├── integration/         # Integration tests
│   └── unit/                # Unit tests (mock-based)
├── credentials/             # OAuth credentials (gitignored)
├── generated/               # Generated documents (gitignored)
├── logs/                    # Application logs (gitignored)
├── .env                     # Environment variables (gitignored)
├── requirements.txt         # Python dependencies
├── Makefile                 # Common commands
└── README.md                # This file
```

---

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_api_endpoints.py -v
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🎨 Key Features

### 1. Intelligent Profile Management
- Comprehensive user profiles with skills, education, experience, projects
- Profile completeness scoring
- Bulk data import

### 2. AI-Powered Matching
- TF-IDF + ML algorithms for project-to-job matching
- Redis caching for performance
- MLflow experiment tracking

### 3. Document Generation
- LaTeX-compiled professional PDFs
- Role-specific templates
- AI-powered content optimization
- ATS-friendly formatting

### 4. Automated Email Pipeline
- Gmail API integration with OAuth2
- Bulk sending with rate limiting
- Attachment management
- Thread tracking

### 5. CRM & Tracking
- Google Sheets integration
- Status tracking (SENT → REPLIED → INTERVIEW → OFFER)
- Analytics dashboard
- Export capabilities

### 6. Background Workers
- Automated reply detection (every 30 minutes)
- Smart follow-up scheduling
- Configurable intervals and limits

### 7. Human-in-the-Loop Review
- Pre-send document review
- Edit and regenerate workflow
- Batch review support

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python 3.10+ |
| **Database** | PostgreSQL, SQLAlchemy, Alembic |
| **Cache** | Redis |
| **AI** | Groq (LLaMA), Claude (Anthropic) |
| **ML** | scikit-learn (TF-IDF), MLflow |
| **Documents** | LaTeX (pdflatex), ReportLab |
| **Email** | Gmail API (OAuth2) |
| **Tracking** | Google Sheets API (OAuth2) |
| **Testing** | pytest, pytest-cov |
| **Logging** | Loguru |

---

## 📊 API Endpoints Overview

### Core Resources
- `/api/v1/users` - User management
- `/api/v1/profile` - Complete profile with all data
- `/api/v1/skills` - Skills management
- `/api/v1/education` - Education entries
- `/api/v1/experiences` - Work experience
- `/api/v1/projects` - Project portfolio

### Jobs & Applications
- `/api/v1/jobs` - Job search and management
- `/api/v1/applications` - Application tracking
- `/api/v1/match` - Project-to-job matching

### Document Generation
- `/api/v1/resume` - Resume generation
- `/api/v1/cover-letters` - Cover letter generation
- `/api/v1/dynamic-resume` - Role-specific resumes

### Email & Tracking
- `/api/v1/bulk-email` - Bulk email sending
- `/api/v1/gmail` - Gmail authentication
- `/api/v1/sheets` - Sheets authentication

### AI Features
- `/api/v1/ai` - AI-powered features
- `/api/v1/workflow` - Workflow orchestration
- `/api/v1/review` - Human-in-the-loop review

### Utilities
- `/api/v1/health` - Health checks
- `/api/v1/test` - Test endpoints

Full API documentation: http://localhost:8000/docs

---

## 🔐 Security

- OAuth2 for Gmail and Google Sheets
- Environment variables for sensitive data
- SQL injection prevention via SQLAlchemy ORM
- CORS middleware configuration
- Rate limiting on email sending
- Secure credential storage

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Write tests for new features
- Follow PEP 8 style guide
- Add docstrings to all functions
- Update documentation as needed
- Ensure all tests pass before submitting

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Groq for fast AI inference
- Anthropic for Claude AI
- Google for Gmail and Sheets APIs
- The open-source community

---

## 📧 Contact

- **Email**: contact@applybot.ai
- **Website**: https://applybot.ai
- **GitHub**: https://github.com/yourusername/applybot
- **Issues**: https://github.com/yourusername/applybot/issues

---

## 🗺️ Roadmap

### Q2 2024
- [ ] Web UI (React/Next.js)
- [ ] LinkedIn job scraping
- [ ] Payment integration (Stripe)
- [ ] Mobile app (React Native)

### Q3 2024
- [ ] Interview preparation AI
- [ ] Salary negotiation assistant
- [ ] Network effect features
- [ ] Multi-language support

### Q4 2024
- [ ] Enterprise features
- [ ] White-label solution
- [ ] API marketplace
- [ ] Advanced analytics

---

**Built with ❤️ by the ApplyBot Team**

---

## OAuth Setup (One-time)

### Gmail
```bash
# 1. Get auth URL
curl http://localhost:8000/api/v1/gmail/authenticate

# 2. Open the URL in browser and authorize

# 3. Verify
curl http://localhost:8000/api/v1/gmail/status
```
Put `credentials/gmail_credentials.json` (downloaded from Google Cloud Console) in the project root.
Add redirect URI: `http://localhost:8000/api/v1/gmail/callback`

### Google Sheets
```bash
curl http://localhost:8000/api/v1/sheets/authenticate
# Open URL in browser, then:
curl http://localhost:8000/api/v1/sheets/status
```

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

---

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Health check with DB status |

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/detailed
```

---

### Users

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/` | Create user |
| GET | `/users/` | List all users |
| GET | `/users/{user_id}` | Get user by ID |
| PUT | `/users/{user_id}` | Update user |
| DELETE | `/users/{user_id}` | Delete user |

```bash
# Create user
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "github_url": "https://github.com/johndoe",
    "professional_summary": "Python developer with 3+ years experience"
  }'

# Get user
curl http://localhost:8000/api/v1/users/{user_id}
```

---

### Profile

| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile/{user_id}` | Get complete profile (user + skills + education + experiences + projects) |
| GET | `/profile/{user_id}/summary` | Profile completeness score and counts |

```bash
curl http://localhost:8000/api/v1/profile/{user_id}
curl http://localhost:8000/api/v1/profile/{user_id}/summary
```

---

### Skills

| Method | Path | Description |
|--------|------|-------------|
| POST | `/skills/?user_id={id}` | Add skill category |
| GET | `/skills/?user_id={id}` | List user's skills |
| GET | `/skills/{skill_id}?user_id={id}` | Get skill by ID |
| PUT | `/skills/{skill_id}?user_id={id}` | Update skill |
| DELETE | `/skills/{skill_id}?user_id={id}` | Delete skill |

```bash
curl -X POST "http://localhost:8000/api/v1/skills/?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Programming Languages",
    "items": ["Python", "JavaScript", "Go"],
    "display_order": 0
  }'
```

---

### Education

| Method | Path | Description |
|--------|------|-------------|
| POST | `/education/?user_id={id}` | Add education entry |
| GET | `/education/?user_id={id}` | List education |
| GET | `/education/{id}?user_id={id}` | Get by ID |
| PUT | `/education/{id}?user_id={id}` | Update |
| DELETE | `/education/{id}?user_id={id}` | Delete |

```bash
curl -X POST "http://localhost:8000/api/v1/education/?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "degree": "B.S. Computer Science",
    "institution": "MIT",
    "year": "2019 - 2023",
    "coursework": "Algorithms, ML, Distributed Systems",
    "display_order": 0
  }'
```

---

### Experiences

| Method | Path | Description |
|--------|------|-------------|
| POST | `/experiences/?user_id={id}` | Add work experience |
| GET | `/experiences/?user_id={id}` | List experiences |
| GET | `/experiences/{id}?user_id={id}` | Get by ID |
| PUT | `/experiences/{id}?user_id={id}` | Update |
| DELETE | `/experiences/{id}?user_id={id}` | Delete |

```bash
curl -X POST "http://localhost:8000/api/v1/experiences/?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Software Engineer",
    "company": "Acme Corp",
    "location": "Remote",
    "duration": "Jan 2022 - Present",
    "achievements": ["Built microservices for 100K users", "Reduced latency by 40%"],
    "display_order": 0
  }'
```

---

### Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/?user_id={id}` | Create project |
| GET | `/projects/?user_id={id}` | List projects (filter by category, technology) |
| GET | `/projects/{id}?user_id={id}` | Get project |
| PUT | `/projects/{id}?user_id={id}` | Update project |
| DELETE | `/projects/{id}?user_id={id}` | Delete project |
| POST | `/projects/bulk-create?user_id={id}` | Create multiple projects |
| GET | `/projects/categories/list` | Get available project categories |
| GET | `/projects/technologies/popular` | Get popular technology tags |

```bash
# Create project
curl -X POST "http://localhost:8000/api/v1/projects/?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-commerce API",
    "description": "RESTful API with payment integration and inventory management",
    "technologies": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "category": "API Development",
    "project_url": "https://github.com/user/ecommerce-api",
    "skills_demonstrated": ["Backend development", "Database design"]
  }'

# Bulk create (for testing)
curl -X POST "http://localhost:8000/api/v1/projects/bulk-create?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '[{"title": "Project 1", ...}, {"title": "Project 2", ...}]'
```

---

### Jobs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/jobs/` | Search/list jobs (filter: keywords, location, company) |
| POST | `/jobs/fetch` | Fetch new jobs from RemoteOK API |
| GET | `/jobs/statistics` | Job database statistics |
| GET | `/jobs/sources` | Available job sources |
| POST | `/jobs/sources/{source_id}/toggle` | Enable/disable a job source |
| GET | `/jobs/{job_id}` | Get job by ID |

```bash
# Fetch jobs from RemoteOK
curl -X POST http://localhost:8000/api/v1/jobs/fetch \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["python", "fastapi"], "limit_per_source": 50}'

# Search stored jobs
curl "http://localhost:8000/api/v1/jobs/?keywords=python,backend&limit=20"

# Job stats
curl http://localhost:8000/api/v1/jobs/statistics
```

---

### Gmail

| Method | Path | Description |
|--------|------|-------------|
| GET | `/gmail/authenticate` | Start OAuth2 flow, returns auth URL |
| GET | `/gmail/callback` | OAuth2 callback (browser redirect) |
| GET | `/gmail/status` | Check if Gmail is authenticated |

```bash
curl http://localhost:8000/api/v1/gmail/authenticate
curl http://localhost:8000/api/v1/gmail/status
```

---

### Google Sheets

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sheets/authenticate` | Start OAuth2 flow |
| GET | `/sheets/callback` | OAuth2 callback |
| GET | `/sheets/status` | Check authentication status |

```bash
curl http://localhost:8000/api/v1/sheets/authenticate
curl http://localhost:8000/api/v1/sheets/status
```

---

### Resume Generation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/resume/generate` | Generate a single tailored resume PDF |
| POST | `/resume/bulk-generate?user_id={id}` | Generate resumes for multiple jobs |
| GET | `/resume/download/{resume_id}` | Download resume PDF |
| GET | `/resume/job/{job_id}/files` | Get all files for a job |
| DELETE | `/resume/{resume_id}` | Delete resume |
| GET | `/resume/list` | List all generated resumes |
| GET | `/resume/template` | Get resume template structure |
| GET | `/resume/status` | Resume generator status (LaTeX available, etc.) |
| GET | `/resume/jobs/recommended/{user_id}` | Get recommended jobs for bulk resume |
| POST | `/resume/test-bulk-flow?user_id={id}` | Test bulk resume flow |

```bash
# Generate single resume
curl -X POST http://localhost:8000/api/v1/resume/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "+1234567890",
    "location": "San Francisco, CA",
    "email": "john@example.com",
    "experience_years": "3+",
    "primary_skills": ["Python", "FastAPI"],
    "education": [{"degree": "B.S. CS", "institution": "MIT", "year": "2023"}],
    "skills": [{"category": "Languages", "items": ["Python", "Go"]}],
    "projects": [{"title": "API", "description": "...", "technologies": ["Python"]}],
    "job_id": "optional-job-uuid"
  }'

# Bulk resumes for multiple jobs
curl -X POST "http://localhost:8000/api/v1/resume/bulk-generate?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "job_ids": ["job-uuid-1", "job-uuid-2", "job-uuid-3"],
    "name": "John Doe",
    "phone": "+1234567890",
    "location": "SF, CA",
    "email": "john@example.com",
    "experience_years": "3+",
    "primary_skills": ["Python"],
    "education": [],
    "skills": [],
    "max_projects_per_resume": 3
  }'

# Download
curl -O http://localhost:8000/api/v1/resume/download/{resume_id}

# Generator status
curl http://localhost:8000/api/v1/resume/status
```

---

### Dynamic Resume

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dynamic-resume/available-roles` | List roles with pre-defined project templates |
| POST | `/dynamic-resume/generate` | Generate role-specific resume from user DB profile |
| GET | `/dynamic-resume/download/{filename}` | Download generated file |
| POST | `/dynamic-resume/generate-quick` | Quick demo without user account |

```bash
# Get available roles
curl http://localhost:8000/api/v1/dynamic-resume/available-roles

# Generate for a specific role (requires user in DB)
curl -X POST http://localhost:8000/api/v1/dynamic-resume/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "target_role": "Machine Learning Engineer",
    "use_ai_selection": true,
    "output_format": "pdf"
  }'

# Quick demo without account
curl -X POST "http://localhost:8000/api/v1/dynamic-resume/generate-quick?target_role=Backend+Engineer&user_name=John+Doe"
```

---

### Cover Letters

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cover-letters/{job_id}` | Generate cover letter for a specific job |
| GET | `/cover-letters/{cover_letter_id}` | Get cover letter content |
| GET | `/cover-letters/{cover_letter_id}/download` | Download cover letter file |
| POST | `/cover-letters/bulk` | Generate cover letters for multiple jobs |
| POST | `/cover-letters/generate` | Generate via query params (quick) |
| POST | `/cover-letters/bulk/download` | Download multiple as ZIP |

```bash
# Generate for job (job must exist in DB)
curl -X POST http://localhost:8000/api/v1/cover-letters/{job_id} \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "user_phone": "+1234567890",
    "user_location": "SF, CA",
    "experience_years": "3+",
    "primary_skills": ["Python", "FastAPI"]
  }'

# Quick generate via query params
curl -X POST "http://localhost:8000/api/v1/cover-letters/generate?\
job_title=Backend+Engineer\
&company=Acme+Corp\
&user_name=John+Doe\
&user_email=john@example.com\
&experience_years=3%2B\
&primary_skills=Python,FastAPI"

# Bulk generation
curl -X POST http://localhost:8000/api/v1/cover-letters/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "job_ids": ["{job_id_1}", "{job_id_2}"],
    "user_name": "John Doe",
    "user_email": "john@example.com"
  }'
```

---

### Project Matching (TF-IDF)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/match/{job_id}?user_id={id}` | Match user projects to job (TF-IDF) |
| POST | `/match/{job_id}/explain?project_id={id}&user_id={id}` | Explain why project matches job |
| GET | `/match/cache/stats` | Redis cache statistics |
| DELETE | `/match/cache/{user_id}` | Invalidate cache for user |
| GET | `/match/experiments/compare` | Compare algorithm performance (MLflow) |

```bash
# Match projects to a job
curl "http://localhost:8000/api/v1/match/{job_id}?user_id={user_id}&max_results=5&use_cache=true"

# Get explanation for a specific project
curl -X POST "http://localhost:8000/api/v1/match/{job_id}/explain?project_id={project_id}&user_id={user_id}"

# Cache stats
curl http://localhost:8000/api/v1/match/cache/stats
```

---

### AI Features

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/select-projects` | AI picks best projects for a job description |
| POST | `/ai/generate-followup` | Generate follow-up email using AI |
| GET | `/ai/test-ai` | Test Groq API connection |

```bash
# AI project selection
curl -X POST http://localhost:8000/api/v1/ai/select-projects \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "job_title": "ML Engineer",
    "job_description": "We need someone experienced in PyTorch, model deployment...",
    "max_projects": 3
  }'

# Generate follow-up email
curl -X POST http://localhost:8000/api/v1/ai/generate-followup \
  -H "Content-Type: application/json" \
  -d '{
    "original_subject": "Application for ML Engineer role",
    "job_title": "ML Engineer",
    "company_name": "Acme AI",
    "followup_count": 1,
    "user_name": "John Doe",
    "days_since_sent": 7
  }'

# Test AI
curl http://localhost:8000/api/v1/ai/test-ai
```

---

### Bulk Email System

| Method | Path | Description |
|--------|------|-------------|
| POST | `/bulk-email/send-bulk-emails` | Send emails to multiple recipients with tracking |
| POST | `/bulk-email/send-job-application` | Full pipeline for one job (resume + CL + email) |
| POST | `/bulk-email/send-bulk-job-applications` | Full pipeline for multiple jobs |
| POST | `/bulk-email/check-replies` | Manually trigger reply check |
| POST | `/bulk-email/send-followups` | Manually trigger follow-up sends |
| GET | `/bulk-email/tracking-status` | Email tracking statistics |
| POST | `/bulk-email/initialize-tracking` | Initialize Google Sheets tracking tab |

```bash
# Send bulk cold emails
curl -X POST http://localhost:8000/api/v1/bulk-email/send-bulk-emails \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {"email": "hr@company1.com", "name": "HR Team"},
      {"email": "hiring@company2.com", "name": "Hiring Manager"}
    ],
    "subject": "Application for Backend Engineer",
    "body": "Dear Hiring Manager,\n\nI am interested in..."
  }'

# Full job application (generates + sends)
curl -X POST http://localhost:8000/api/v1/bulk-email/send-job-application \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "job_title": "Backend Engineer",
    "company": "Acme Corp",
    "job_description": "We are looking for...",
    "hr_email": "hr@acme.com",
    "generate_documents": true,
    "email_tone": "professional"
  }'

# Check replies
curl -X POST http://localhost:8000/api/v1/bulk-email/check-replies

# Send follow-ups
curl -X POST http://localhost:8000/api/v1/bulk-email/send-followups

# Tracking stats
curl http://localhost:8000/api/v1/bulk-email/tracking-status
```

---

### Applications (DB-tracked)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/applications/bulk-apply` | Apply to multiple stored jobs |
| GET | `/applications/?user_id={id}` | Get user's applications |
| GET | `/applications/{id}` | Get application details |
| GET | `/applications/{id}/status` | Check reply status via Gmail |

```bash
# Bulk apply to jobs stored in DB
curl -X POST http://localhost:8000/api/v1/applications/bulk-apply \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "job_ids": ["{job_id_1}", "{job_id_2}"],
    "email_tone": "professional"
  }'

# Get applications
curl "http://localhost:8000/api/v1/applications/?user_id={user_id}&status=sent&limit=20"

# Check reply status
curl http://localhost:8000/api/v1/applications/{application_id}/status
```

---

### Human-in-the-Loop Review

| Method | Path | Description |
|--------|------|-------------|
| POST | `/review/start` | Generate documents and pause for review |
| POST | `/review/{thread_id}/submit` | Submit decision (approved/edit/rejected) |
| GET | `/review/{thread_id}/status` | Get review status |
| GET | `/review/pending` | List pending reviews |
| POST | `/review/batch-start` | Start reviews for multiple jobs |

```bash
# Start review (generates resume + cover letter, waits for decision)
curl -X POST http://localhost:8000/api/v1/review/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "user_profile": {"name": "John Doe", "skills": ["Python"]},
    "job": {"title": "Backend Engineer", "company": "Acme", "description": "..."},
    "matched_projects": [{"title": "API Project", "description": "..."}]
  }'

# Approve and send
curl -X POST http://localhost:8000/api/v1/review/{thread_id}/submit \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved"}'

# Reject
curl -X POST http://localhost:8000/api/v1/review/{thread_id}/submit \
  -H "Content-Type: application/json" \
  -d '{"decision": "rejected", "reason": "Not a good fit"}'
```

---

### Workflow Orchestration

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workflow/run-full-workflow` | Run full agent pipeline |
| POST | `/workflow/upload-jobs-csv` | Upload CSV with job listings |
| POST | `/workflow/fetch-jobs` | Fetch jobs from a source |
| POST | `/workflow/match-projects` | Match projects to a job |
| POST | `/workflow/generate-resume` | Generate resume only |
| POST | `/workflow/write-cover-letter` | Write cover letter only |
| POST | `/workflow/process-single-job` | Full pipeline for one job |

```bash
# Run full workflow from CSV
curl -X POST http://localhost:8000/api/v1/workflow/upload-jobs-csv \
  -F "file=@jobs.csv"
# CSV columns: job_title, company, job_link, job_description, email

# Full workflow
curl -X POST http://localhost:8000/api/v1/workflow/run-full-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "user_profile": {"name": "John", "skills": ["Python"]},
    "job_source": {"source": "csv", "url": null},
    "options": {"template": "standard", "tone": "professional", "max_projects": 5}
  }'
```

---

### Test Generation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/test/sample-data` | Get sample user/job/project data |
| POST | `/test/resume` | Test resume agent |
| POST | `/test/cover-letter` | Test cover letter agent |
| POST | `/test/both` | Test both agents |
| POST | `/test/quick-test` | One-click test with sample data |

```bash
# Get sample data to use in tests
curl http://localhost:8000/api/v1/test/sample-data

# Quick test (no input needed)
curl -X POST http://localhost:8000/api/v1/test/quick-test

# Test resume with custom data
curl -X POST http://localhost:8000/api/v1/test/resume \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {"name": "John", "email": "j@example.com", "skills": ["Python"]},
    "job": {"title": "Backend Engineer", "company": "Acme", "description": "..."},
    "matched_projects": []
  }'
```

---

## Test Script

Run this script to verify core endpoints work end-to-end:

```bash
python test_api_endpoints.py
```

The script:
1. Checks health endpoint
2. Creates a test user
3. Adds skill, education, experience, project
4. Fetches complete profile and summary

---

## Full Workflow Example

```bash
BASE=http://localhost:8000/api/v1

# 1. Authenticate APIs (one time)
curl $BASE/gmail/authenticate   # open returned URL in browser
curl $BASE/sheets/authenticate  # open returned URL in browser

# 2. Create user
USER=$(curl -s -X POST $BASE/users/ -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","full_name":"Me","phone":"+1234567890"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 3. Add profile data
curl -X POST "$BASE/skills/?user_id=$USER" -H "Content-Type: application/json" \
  -d '{"category":"Languages","items":["Python","Go"],"display_order":0}'

curl -X POST "$BASE/projects/?user_id=$USER" -H "Content-Type: application/json" \
  -d '{"title":"API Platform","description":"High-perf REST API","technologies":["Python","FastAPI","Redis"],"category":"API Development"}'

# 4. Fetch jobs
curl -X POST $BASE/jobs/fetch -H "Content-Type: application/json" \
  -d '{"keywords":["python","backend"],"limit_per_source":20}'

# 5. Get job IDs
JOB=$(curl -s "$BASE/jobs/?keywords=python&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id']) if d else print('')")

# 6. Match projects to job
curl "$BASE/match/$JOB?user_id=$USER"

# 7. Generate tailored resume
curl -X POST $BASE/resume/generate -H "Content-Type: application/json" \
  -d "{\"name\":\"Me\",\"phone\":\"+1234567890\",\"location\":\"SF\",\"email\":\"me@example.com\",\"experience_years\":\"2+\",\"primary_skills\":[\"Python\"],\"education\":[],\"skills\":[],\"job_id\":\"$JOB\"}"

# 8. Send job application (full pipeline)
curl -X POST $BASE/bulk-email/send-job-application -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER\",\"job_title\":\"Backend Engineer\",\"company\":\"Acme\",\"job_description\":\"Python developer...\",\"hr_email\":\"hr@acme.com\",\"generate_documents\":true}"

# 9. Check tracking
curl $BASE/bulk-email/tracking-status
```

---

## Project Structure

```
app/
├── api/v1/endpoints/    # Route handlers
├── agents/              # LangGraph-style agents
├── orchestrator/        # Agent pipeline + review workflow
├── services/            # Business logic
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── core/                # Config, auth helpers
├── workers/             # Background tasks
└── templates/           # LaTeX and email templates
alembic/                 # DB migrations
test_api_endpoints.py    # Basic endpoint test script
```
