"""Database initialization and connection checks."""
from sqlalchemy import text
from loguru import logger

from app.database.base import engine, SessionLocal


def init_db():
    """Initialize database tables and check configuration."""
    try:
        logger.info("Initializing database...")
        
        # Import all models to ensure they are registered
        from app.models import Profile, Project, Job, Application
        from app.database.base import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Check Row-Level Security status (Supabase specific)
        try:
            db = SessionLocal()
            result = db.execute(text("""
                SELECT tablename, rowsecurity 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('profiles', 'projects', 'jobs', 'applications')
            """))
            
            rls_status = result.fetchall()
            logger.info("Row-Level Security status:")
            for table, rls_enabled in rls_status:
                status = "✅ Enabled" if rls_enabled else "❌ Disabled"
                logger.info(f"  {table}: {status}")
            
            if not all(rls for _, rls in rls_status):
                logger.warning("⚠️  Some tables don't have RLS enabled!")
            
            db.close()
        except Exception as e:
            logger.warning(f"Could not check RLS status: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def check_db_connection():
    """Check if database connection is working. Retries once after a short delay."""
    import time
    for attempt in range(3):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("Database connection successful")
            return True
        except Exception as e:
            if attempt < 2:
                logger.warning(f"DB connection attempt {attempt + 1} failed, retrying in 2s...")
                time.sleep(2)
            else:
                logger.error(f"Database connection failed: {e}")
                return False


if __name__ == "__main__":
    init_db()