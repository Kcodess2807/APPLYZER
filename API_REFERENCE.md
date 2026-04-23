# ApplyBot API Reference

**Important Note for Frontend Developers**: 
Because this backend is built with FastAPI, you don't need to guess schemas or payloads! When the backend server is running (`make run`), simply navigate to **`http://localhost:8000/docs`**. You will find an interactive Swagger UI to test every endpoint with live response schemas.

**Base URL**: `http://localhost:8000/api/v1`

---

## 1. Authentication (OAuth)

| Method | Endpoint | Description |
|---|---|---|
| **GET** | `/gmail/authenticate` | Starts the Google OAuth2 flow for Gmail API access |
| **GET** | `/gmail/callback` | OAuth2 callback handler (Redirect URI) |
| **GET** | `/gmail/status` | Check if Gmail tokens are active |
| **GET** | `/sheets/authenticate` | Starts the Google OAuth2 flow for Google Sheets API access |

---

## 2. User & Profile Management

| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/users/` | Create a new user profile |
| **GET**  | `/users/{id}` | Fetch basic user details |
| **GET**  | `/profile/{id}` | Get aggregated user profile (Skills, Education, Projects) |
| **POST** | `/projects/?user_id={id}` | Add a new project to the user's profile |
| **GET**  | `/projects/?user_id={id}` | List all projects belonging to the user |

---

## 3. Job Operations

| Method | Endpoint | Description |
|---|---|---|
| **GET**  | `/jobs/` | Fetch stored jobs from the database (paginated) |
| **POST** | `/jobs/fetch` | Synchronously trigger job fetch from RemoteOK API |
| **GET**  | `/jobs/{id}` | Fetch details for a specific job |

---

## 4. AI & Document Generation Pipeline

| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/dynamic-resume/generate` | Generates a role-specific LaTeX PDF resume and returns the download URL or Base64 payload |
| **GET**  | `/dynamic-resume/download/{filename}` | Download the securely generated PDF |
| **POST** | `/cover-letters/generate` | Generates a tailored professional cover letter via Groq/LLaMA |
| **POST** | `/ai/select-projects` | LangGraph agent endpoint: AI ranks user projects against job description keywords |

---

## 5. Application Orchestration & Email

| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/bulk-email/send-job-application`| Execute the complete pipeline (Match -> Gen -> Email -> Sheet Log) for a single job |
| **POST** | `/bulk-email/send-bulk-job-applications`| Triggers the above pipeline recursively across an array of target job IDs |
| **GET**  | `/bulk-email/tracking-status`| Returns Google Sheets CRM row statistics (total sent, replied, etc.) |
| **POST** | `/bulk-email/check-replies` | Force the background worker to immediately poll Gmail for unread recruiter replies |
| **POST** | `/bulk-email/send-followups` | Force the Follow-Up Scheduler to draft and send 7-day follow-up pings to unresponsive recruiters |
