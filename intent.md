# ApplyBot - Project Intent & Architecture

## What It Is

ApplyBot is a FastAPI backend that automates the job application process end-to-end. It manages a user's professional profile, fetches job listings, generates tailored resumes and cover letters, sends applications via Gmail, and tracks responses in Google Sheets.

---

## Core Problem It Solves

Applying to many jobs is repetitive and time-consuming. ApplyBot automates:
- Fetching relevant jobs from job boards
- Selecting which of your projects best match each specific job
- Generating a tailored LaTeX resume for each job
- Writing a personalized cover letter
- Composing a cold outreach email
- Sending it all via Gmail with attachments
- Logging each application in Google Sheets
- Detecting replies and sending automated follow-ups

---

## Architecture

```
app/
├── api/v1/endpoints/       # HTTP route handlers (one file per domain)
├── agents/                 # Agent-based pipeline (LangGraph style)
│   ├── base.py             # BaseAgent class
│   ├── job_fetcher.py      # Fetches jobs from sources
│   ├── project_matcher.py  # Matches user projects to job requirements
│   ├── resume_generator.py # Generates resume data
│   └── cover_letter_writer.py
├── orchestrator/
│   ├── workflow.py         # Chains agents into full pipeline
│   └── review_workflow.py  # Human-in-the-loop review variant
├── services/               # Business logic
│   ├── job_service.py      # Job CRUD + RemoteOK fetch
│   ├── project_service.py  # Project CRUD + AI selection
│   ├── resume_generator.py # LaTeX resume → PDF
│   ├── dynamic_resume_generator.py  # Role-specific resume with AI
│   ├── cover_letter_generator.py   # Cover letter templating
│   ├── cold_dm_generator.py        # Cold outreach email body
│   ├── gmail_service.py    # Gmail API send/read
│   ├── bulk_email_service.py       # Send + track bulk emails
│   ├── email_tracker_service.py    # Google Sheets tracking
│   ├── job_application_service.py  # Full application pipeline
│   ├── application_orchestrator.py # Bulk apply via DB
│   ├── ai_service.py               # Groq AI calls
│   └── matching/           # TF-IDF project matching
│       ├── TFIDF_matcher.py
│       ├── base_matcher.py
│       └── cache_service.py        # Redis caching for matches
├── models/                 # SQLAlchemy ORM models
│   ├── user.py
│   ├── project.py
│   ├── job.py
│   ├── application.py
│   ├── skill.py
│   ├── education.py
│   └── experience.py
├── schemas/                # Pydantic request/response schemas
├── database/               # SQLAlchemy setup + Supabase client
├── core/
│   ├── config.py           # Settings from environment variables
│   ├── gmail_auth.py       # Gmail OAuth2 helpers
│   └── sheets_auth.py      # Google Sheets OAuth2 helpers
├── workers/
│   ├── reply_checker.py    # Background worker: check Gmail for replies
│   └── followup_scheduler.py  # Background worker: send follow-ups
└── templates/
    ├── resume.cls              # LaTeX class file
    └── cover_letter_template.txt
```

**Database**: PostgreSQL (via Supabase), managed with Alembic migrations
**Cache**: Redis (for project-matching result caching)
**AI**: Groq API (LLaMA models) for text generation; OpenAI optionally
**Email**: Gmail API (OAuth2)
**Tracking**: Google Sheets API (OAuth2)

---

## Feature Breakdown

### 1. User Profile Management
Full CRUD for a user's professional identity:
- **User** - name, email, phone, LinkedIn, GitHub, professional summary
- **Skills** - categorized skill groups (e.g., "Programming Languages": ["Python", "Go"])
- **Education** - degree, institution, year, coursework
- **Experience** - role, company, location, duration, bullet achievements
- **Projects** - title, description, technologies, category, URL, skills demonstrated, achievements

Profile completeness scoring at `/profile/{user_id}/summary`.

### 2. Job Management
- Fetch jobs from **RemoteOK API** (`POST /jobs/fetch`) with keyword filtering
- Search/filter stored jobs by keyword, location, company (`GET /jobs/`)
- Job source enable/disable management (`GET /jobs/sources`)
- Job statistics (`GET /jobs/statistics`)

### 3. Resume Generation
Two modes:

**Standard Resume** (`/resume/generate`):
- Takes user data + optional job_id + optional selected project IDs
- Generates LaTeX `.tex` file, compiles to PDF with `pdflatex`
- Falls back to ReportLab/WeasyPrint if LaTeX unavailable
- Stores files organized by job_id

**Bulk Resume** (`/resume/bulk-generate`):
- Takes up to 10 job IDs
- For each job, scores all user projects against job keywords (title/description/requirements/technologies)
- Selects top N projects and generates a tailored resume
- Returns download URLs for all generated PDFs

**Dynamic Resume** (`/dynamic-resume/generate`):
- Takes user_id + target role (e.g., "Machine Learning Engineer")
- Pulls complete profile from DB
- Uses AI (Groq) or keyword matching to select most relevant projects
- Generates LaTeX resume tailored to that role

### 4. Cover Letter Generation
- Per-job cover letter generation (`POST /cover-letters/{job_id}`)
- Bulk generation for multiple jobs (`POST /cover-letters/bulk`)
- Quick generation via query params (`POST /cover-letters/generate`)
- Bulk ZIP download (`POST /cover-letters/bulk/download`)
- Downloads individual cover letters as text files

### 5. Project-to-Job Matching (TF-IDF)
- ML-powered matching at `/match/{job_id}`
- Algorithm: TF-IDF similarity + keyword overlap + technology alignment
- **Redis caching** for repeated queries (1-hour TTL)
- **MLflow experiment tracking** for algorithm performance monitoring
- Per-project explanation endpoint (`POST /match/{job_id}/explain`)
- Cache statistics and invalidation endpoints

### 6. Gmail Integration
- OAuth2 flow: `/gmail/authenticate` → browser → `/gmail/callback`
- Authentication status check: `/gmail/status`
- Credentials stored in `credentials/gmail_token.json`

### 7. Google Sheets Integration
- OAuth2 flow: `/sheets/authenticate` → browser → `/sheets/callback`
- Used as a CRM to track all sent emails with status (SENT/REPLIED)
- Tracks thread IDs for reply detection

### 8. Bulk Email System
- Send bulk cold emails to multiple recipients (`POST /bulk-email/send-bulk-emails`)
- Each email is: sent via Gmail, tracked in Google Sheets with thread_id
- Manual reply check trigger (`POST /bulk-email/check-replies`)
- Manual follow-up trigger (`POST /bulk-email/send-followups`)
- Email tracking statistics (`GET /bulk-email/tracking-status`)
- Initialize tracking sheet (`POST /bulk-email/initialize-tracking`)

### 9. Full Job Application Pipeline
**Single application** (`POST /bulk-email/send-job-application`):
1. AI selects relevant projects for the job
2. Generates tailored resume PDF
3. Generates personalized cover letter
4. Generates cold DM email body
5. Sends via Gmail with resume + cover letter attached
6. Logs in Google Sheets

**Bulk applications** (`POST /bulk-email/send-bulk-job-applications`):
- Same pipeline for multiple jobs with rate limiting

**DB-based bulk apply** (`POST /applications/bulk-apply`):
- Takes stored job IDs from database
- Runs full pipeline per job
- Stores Application records in DB with gmail_thread_id
- Tracks reply status per application

### 10. AI Features (Groq-powered)
- **AI Project Selection** (`POST /ai/select-projects`): Given a job description, ranks and selects the most relevant user projects
- **AI Follow-up Generation** (`POST /ai/generate-followup`): Generates personalized follow-up emails based on job context and follow-up count
- **Test AI connection** (`GET /ai/test-ai`): Verifies Groq API is configured and responding

### 11. Human-in-the-Loop Review Workflow
- Start a review session for a job application (`POST /review/start`):
  - Generates resume + cover letter
  - Pauses for human review
  - Returns documents + thread_id
- Submit decision (`POST /review/{thread_id}/submit`):
  - `approved`: sends the application
  - `edit`: regenerates with specified edits
  - `rejected`: skips this application
- Get review status (`GET /review/{thread_id}/status`)
- Batch start reviews for multiple jobs (`POST /review/batch-start`)

### 12. Workflow Orchestration (Agent Pipeline)
Chains four agents in sequence:
1. **JobFetcherAgent**: Fetches jobs from CSV, LinkedIn, Google Sheets
2. **ProjectMatcherAgent**: Matches user projects to job requirements
3. **ResumeGeneratorAgent**: Generates resume for the job
4. **CoverLetterWriterAgent**: Writes personalized cover letter

Endpoints:
- `POST /workflow/run-full-workflow`: Runs entire pipeline
- `POST /workflow/upload-jobs-csv`: Upload CSV job list
- `POST /workflow/fetch-jobs`: Fetch jobs only
- `POST /workflow/match-projects`: Match projects only
- `POST /workflow/generate-resume`: Generate resume only
- `POST /workflow/write-cover-letter`: Write cover letter only
- `POST /workflow/process-single-job`: Run full pipeline for one job

### 13. Test Generation Endpoints
Development/testing endpoints under `/test/`:
- `POST /test/resume`: Test resume generation agent with sample data
- `POST /test/cover-letter`: Test cover letter agent
- `POST /test/both`: Test both agents together
- `GET /test/sample-data`: Get sample user/job/projects data
- `POST /test/quick-test`: One-click full test with pre-filled sample data

---

## Data Flow: Full Application Send

```
User profile (DB)
        ↓
AI selects projects (Groq/TF-IDF)
        ↓
Resume Generator → LaTeX → PDF
        ↓
Cover Letter Generator → .txt file
        ↓
Cold DM Generator → email body text
        ↓
Gmail API → send email with PDF + cover letter attached
        ↓
Google Sheets → log row (email, company, status=SENT, thread_id)
        ↓
DB → Application record (user_id, job_id, gmail_thread_id)
        ↓
Background Workers:
  ReplyChecker → polls Gmail for thread replies → updates status=REPLIED
  FollowUpScheduler → sends follow-up after N days if no reply
```

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `REDIS_URL` | Redis URL (default: `redis://localhost:6379/0`) |
| `GROQ_API_KEY` | Groq AI API key (for text generation) |
| `OPENAI_API_KEY` | OpenAI API key (optional alternative) |
| `GMAIL_CLIENT_ID` | Gmail OAuth2 client ID |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth2 client secret |
| `SHEETS_CLIENT_ID` | Google Sheets OAuth2 client ID |
| `SHEETS_CLIENT_SECRET` | Google Sheets OAuth2 client secret |
| `SHEETS_SPREADSHEET_ID` | Target Google Spreadsheet ID |
| `API_BASE_URL` | This server's base URL (for OAuth callbacks) |
| `FOLLOWUP_DAYS_INTERVAL` | Days before sending follow-up (default: 7) |
| `MAX_FOLLOWUP_COUNT` | Max follow-ups per application (default: 2) |
| `REPLY_CHECK_INTERVAL_MINUTES` | Reply check frequency (default: 30) |
| `SECRET_KEY` | App secret key |
| `LOG_LEVEL` | Logging level (default: INFO) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Language | Python 3.10+ |
| Database | PostgreSQL via Supabase |
| ORM | SQLAlchemy + Alembic |
| Cache | Redis |
| AI | Groq API (LLaMA models) |
| Resume | LaTeX (`pdflatex`), fallback: ReportLab |
| Email | Gmail API (OAuth2) |
| Tracking | Google Sheets API (OAuth2) |
| ML Matching | TF-IDF (scikit-learn) |
| Experiment tracking | MLflow |
| Logging | Loguru |
