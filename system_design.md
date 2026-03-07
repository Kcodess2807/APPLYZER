# ApplyBot — System Design

## 1. High-Level Architecture

```mermaid
graph TD
    Client["Client / API Consumer"]

    subgraph FastAPI["FastAPI Application (main.py)"]
        Router["API Router (api/v1/api.py)"]
        MW["CORS Middleware"]
    end

    subgraph Endpoints["API Endpoints (/api/v1/)"]
        EP_USER["users / profile / skills\neducation / experiences / projects"]
        EP_JOB["jobs"]
        EP_APP["applications / bulk-email"]
        EP_DOC["resume / cover-letters\ndynamic-resume / ai"]
        EP_WF["workflow / review"]
        EP_EXT["gmail / sheets / health"]
    end

    subgraph Services["Service Layer"]
        UserSvc["UserService"]
        ProfileSvc["ProfileService"]
        ProjectSvc["ProjectService"]
        ResumeGen["ResumeGenerator"]
        CoverLetterGen["CoverLetterGenerator"]
        ColdDMGen["ColdDMGenerator"]
        BulkEmailSvc["BulkEmailService"]
        EmailTrackerSvc["EmailTrackerService"]
        JobAppSvc["JobApplicationService"]
        AISvc["AIService"]
        DynResumeSvc["DynamicResumeGenerator"]
    end

    subgraph Orchestrators["Orchestrators"]
        AppOrch["ApplicationOrchestrator"]
        JobAppOrch["JobApplicationOrchestrator"]
        ReviewWF["HumanReviewWorkflow (LangGraph)"]
    end

    subgraph Agents["AI Agents"]
        JobFetcher["JobFetcherAgent"]
        ProjMatcher["ProjectMatcherAgent"]
        ResumeAgent["ResumeGeneratorAgent"]
        CLAgent["CoverLetterWriterAgent"]
    end

    subgraph Workers["Background Workers"]
        ReplyChecker["ReplyChecker"]
        FollowUpSched["FollowUpScheduler"]
        SchedMgr["SchedulerManager"]
    end

    subgraph External["External Services"]
        GmailAPI["Gmail API"]
        SheetsAPI["Google Sheets API"]
        ClaudeAI["Claude AI (Anthropic)"]
    end

    subgraph DB["Database (PostgreSQL / Supabase)"]
        Models["User / Skill / Education\nExperience / Project / Job / Application"]
    end

    Client --> MW --> Router --> Endpoints
    EP_USER --> UserSvc & ProfileSvc & ProjectSvc
    EP_APP --> BulkEmailSvc & JobAppSvc & AppOrch
    EP_DOC --> ResumeGen & CoverLetterGen & DynResumeSvc & AISvc
    EP_WF --> JobAppOrch & ReviewWF
    EP_EXT --> GmailAPI & SheetsAPI

    JobAppOrch --> JobFetcher & ProjMatcher & ResumeAgent & CLAgent
    ReviewWF --> ResumeAgent & CLAgent
    AppOrch --> ResumeGen & CoverLetterGen & ColdDMGen

    BulkEmailSvc --> GmailAPI & EmailTrackerSvc
    EmailTrackerSvc --> SheetsAPI
    JobAppSvc --> GmailAPI & SheetsAPI & AISvc

    AISvc & DynResumeSvc & ProjMatcher & ResumeAgent & CLAgent --> ClaudeAI

    UserSvc & ProfileSvc & ProjectSvc & AppOrch --> Models
    SchedMgr --> ReplyChecker & FollowUpSched
    ReplyChecker & FollowUpSched --> GmailAPI & SheetsAPI
```

---

## 2. Application Startup Flow

```mermaid
flowchart TD
    Start["uvicorn starts"] --> Create["create_application()"]
    Create --> MW["Add CORS Middleware"]
    MW --> Routes["Register all routers"]
    Routes --> Lifespan["lifespan() startup"]
    Lifespan --> Logging["setup_logging()"]
    Logging --> DBCheck{"DB reachable?"}
    DBCheck -- Yes --> InitDB["init_db() — create tables"]
    DBCheck -- No --> WarnDB["Log warning, continue"]
    InitDB & WarnDB --> BGCheck{"ENABLE_BACKGROUND_WORKERS?"}
    BGCheck -- true --> StartWorkers["asyncio.create_task(start_schedulers())"]
    BGCheck -- false --> Ready["App Ready"]
    StartWorkers --> Ready
    Ready --> Serve["Serve requests"]
    Serve --> Shutdown["lifespan() shutdown"]
    Shutdown --> CancelWorkers["Cancel background tasks"]
```

---

## 3. Core Application Workflow (Automated Pipeline)

```mermaid
sequenceDiagram
    participant Client
    participant WorkflowEndpoint as /workflow
    participant Orchestrator as JobApplicationOrchestrator
    participant JobFetcher as JobFetcherAgent
    participant ProjMatcher as ProjectMatcherAgent
    participant ResumeAgent as ResumeGeneratorAgent
    participant CLWriter as CoverLetterWriterAgent
    participant Claude as Claude AI

    Client->>WorkflowEndpoint: POST /run-full-workflow
    WorkflowEndpoint->>Orchestrator: run_full_workflow(user_id, profile, config)

    Orchestrator->>JobFetcher: execute(source_config)
    JobFetcher-->>Orchestrator: jobs[]

    loop For each job
        Orchestrator->>ProjMatcher: execute(user_id, job)
        ProjMatcher->>Claude: rank user projects by job relevance
        Claude-->>ProjMatcher: matched_projects[]
        ProjMatcher-->>Orchestrator: matched_projects[]

        Orchestrator->>ResumeAgent: execute(profile, job, matched_projects)
        ResumeAgent->>Claude: generate resume content
        Claude-->>ResumeAgent: resume_data
        ResumeAgent-->>Orchestrator: resume

        Orchestrator->>CLWriter: execute(profile, job, resume, matched_projects)
        CLWriter->>Claude: generate cover letter
        Claude-->>CLWriter: cover_letter
        CLWriter-->>Orchestrator: cover_letter
    end

    Orchestrator-->>WorkflowEndpoint: WorkflowResult
    WorkflowEndpoint-->>Client: applications[]
```

---

## 4. Human-in-the-Loop Review Flow (LangGraph)

```mermaid
stateDiagram-v2
    [*] --> generate_documents : start_application_review()

    generate_documents --> wait_for_review : docs ready
    wait_for_review --> wait_for_review : INTERRUPT (paused for human)

    wait_for_review --> process_approval : decision = approved
    wait_for_review --> process_edits : decision = edit
    wait_for_review --> process_rejection : decision = rejected

    process_edits --> generate_documents : loop back with edits
    process_approval --> [*] : approved
    process_rejection --> [*] : rejected
```

---

## 5. Bulk Job Application Flow

```mermaid
sequenceDiagram
    participant Client
    participant BulkEmailEP as /bulk-email
    participant AppOrch as ApplicationOrchestrator
    participant ResumeGen as ResumeGenerator
    participant CLGen as CoverLetterGenerator
    participant ColdDM as ColdDMGenerator
    participant Gmail as GmailService
    participant DB as PostgreSQL
    participant Sheets as Google Sheets

    Client->>BulkEmailEP: POST /send-bulk-job-applications
    BulkEmailEP->>AppOrch: bulk_apply(user_id, job_ids)
    AppOrch->>DB: fetch user + profile

    loop For each job_id
        AppOrch->>DB: fetch job details
        AppOrch->>ResumeGen: generate_for_job(profile, job)
        AppOrch->>CLGen: generate(profile, job)
        AppOrch->>ColdDM: generate(profile, job, tone)

        AppOrch->>Gmail: send_email(hr_email, subject, body, attachments)
        Gmail-->>AppOrch: message_id, thread_id

        AppOrch->>DB: INSERT Application record
        AppOrch->>Sheets: add_application row (optional)
    end

    AppOrch-->>BulkEmailEP: results summary
    BulkEmailEP-->>Client: { total, successful, failed, applications[] }
```

---

## 6. Dynamic Resume Generation Flow

```mermaid
flowchart TD
    Client["POST /dynamic-resume/generate"] --> EP["dynamic_resume endpoint"]
    EP --> ProfSvc["ProfileService.get_profile_as_dict(user_id)"]
    ProfSvc --> DB[("PostgreSQL")]
    DB --> ProfSvc

    ProfSvc --> DynGen["DynamicResumeGenerator.generate_resume()"]
    DynGen --> AICheck{"use_ai_selection?"}

    AICheck -- Yes --> Claude["Claude AI\n(select best projects\nfor target_role)"]
    Claude --> DynGen

    AICheck -- No --> Template["Use role template projects"]
    Template --> DynGen

    DynGen --> LaTeX["Render LaTeX template"]
    LaTeX --> PDFCheck{"pdflatex available?"}
    PDFCheck -- Yes --> PDF["Compile to PDF"]
    PDFCheck -- No --> TEX["Return .tex file"]
    PDF & TEX --> Response["Return file paths + download URL"]
    Response --> Client
```

---

## 7. Email Tracking & Follow-up Workers

```mermaid
flowchart TD
    subgraph Startup["App Startup (if ENABLE_BACKGROUND_WORKERS=true)"]
        SchedMgr["SchedulerManager"] --> RC["ReplyChecker task"]
        SchedMgr --> FS["FollowUpScheduler task"]
    end

    subgraph ReplyCheckerLoop["ReplyChecker (periodic)"]
        RC --> GetSent["Get all SENT emails from Sheets"]
        GetSent --> CheckGmail["Check Gmail threads for replies"]
        CheckGmail --> UpdateSheet["Update status to REPLIED in Sheets"]
    end

    subgraph FollowUpLoop["FollowUpScheduler (periodic)"]
        FS --> GetEligible["Get emails: SENT + no reply\n+ past interval + followup_count < max"]
        GetEligible --> SendFollowUp["Send follow-up via Gmail"]
        SendFollowUp --> IncrCount["Increment followup_count in Sheets"]
    end

    subgraph ManualTrigger["Manual API Triggers"]
        MRC["POST /bulk-email/check-replies"] --> RC
        MFS["POST /bulk-email/send-followups"] --> FS
    end
```

---

## 8. Database Models

```mermaid
erDiagram
    User {
        uuid id PK
        string full_name
        string email
        string phone
        string linkedin_url
        string github_url
        string professional_summary
    }

    Skill {
        uuid id PK
        uuid user_id FK
        string category
        array items
    }

    Education {
        uuid id PK
        uuid user_id FK
        string degree
        string institution
        string year
        string coursework
    }

    Experience {
        uuid id PK
        uuid user_id FK
        string role
        string company
        string location
        string duration
        array achievements
    }

    Project {
        uuid id PK
        uuid user_id FK
        string title
        string description
        array technologies
        string project_url
    }

    Job {
        uuid id PK
        string title
        string company
        string description
        string requirements
        string contact_email
    }

    Application {
        uuid id PK
        uuid user_id FK
        uuid job_id FK
        string status
        string gmail_message_id
        string gmail_thread_id
        string resume_path
        string cover_letter_path
        datetime email_sent_at
        string sheets_row_id
    }

    User ||--o{ Skill : has
    User ||--o{ Education : has
    User ||--o{ Experience : has
    User ||--o{ Project : has
    User ||--o{ Application : submits
    Job ||--o{ Application : receives
```

---

## 9. API Endpoint Map

```mermaid
mindmap
  root((API /api/v1))
    Profile
      GET /users
      POST /users
      GET /users/id
      PUT /users/id
      DELETE /users/id
      GET /profile/id
      GET /profile/id/summary
      /skills  /education
      /experiences  /projects
    Jobs
      GET /jobs
      POST /jobs
      GET /jobs/id
      DELETE /jobs/id
    Applications
      POST /applications/bulk-apply
      GET /applications/user/id
    Bulk Email
      POST /bulk-email/send-bulk-emails
      POST /bulk-email/send-job-application
      POST /bulk-email/send-bulk-job-applications
      GET  /bulk-email/tracking-status
      POST /bulk-email/check-replies
      POST /bulk-email/send-followups
      POST /bulk-email/initialize-tracking
    Documents
      POST /resume/generate
      POST /cover-letters/generate
      POST /dynamic-resume/generate
      GET  /dynamic-resume/available-roles
      GET  /dynamic-resume/download/filename
    AI
      POST /ai/...
      POST /match/projects
    Workflow
      POST /workflow/run-full-workflow
      POST /workflow/fetch-jobs
      POST /workflow/match-projects
    Review
      POST /review/start
      POST /review/submit
      GET  /review/status/id
    External
      GET  /gmail/auth-status
      POST /sheets/...
    Utility
      GET  /health
      GET  /test/...
```
