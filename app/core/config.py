"""Application configuration settings."""
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    """Application settings loaded from environment variables."""
    
    # Basic app settings
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ApplyBot")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    API_V1_STR: str = "/api/v1"
    
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from environment variable."""
        origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
        return [origin.strip() for origin in origins.split(",")]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    @property
    def getDatabaseUrl(self) -> str:
        """Get database URL with validation."""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required. Please set up your database credentials in .env file.")
        url = self.DATABASE_URL
        # Supabase requires SSL; add sslmode=require if not already present.
        if ("supabase.com" in url or "supabase.co" in url) and "sslmode" not in url:
            url += ("&" if "?" in url else "?") + "sslmode=require"
        return url
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # External API settings
    REMOTEOK_API_URL: str = "https://remoteok.io/api"
    
    # AI Service settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    # GitHub API — optional token increases rate limit from 60 to 5000 req/hr
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    
    # Gmail API settings
    GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Google Sheets API settings
    SHEETS_CLIENT_ID: str = os.getenv("SHEETS_CLIENT_ID", "")
    SHEETS_CLIENT_SECRET: str = os.getenv("SHEETS_CLIENT_SECRET", "")
    SHEETS_SPREADSHEET_ID: str = os.getenv("SHEETS_SPREADSHEET_ID", "")
    
    # Follow-up settings
    FOLLOWUP_DAYS_INTERVAL: int = int(os.getenv("FOLLOWUP_DAYS_INTERVAL", "7"))
    MAX_FOLLOWUP_COUNT: int = int(os.getenv("MAX_FOLLOWUP_COUNT", "2"))
    REPLY_CHECK_INTERVAL_MINUTES: int = int(os.getenv("REPLY_CHECK_INTERVAL_MINUTES", "30"))
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    # Set REQUIRE_AUTH=true in production to enforce JWT auth on all endpoints.
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
    # Supabase JWT secret: Settings → API → JWT Secret in the Supabase dashboard.
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # File storage settings
    UPLOAD_DIR: str = "uploads"
    RESUME_DIR: str = "generated/resumes"
    COVER_LETTER_DIR: str = "uploads/cover_letters"
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"


settings = Settings()