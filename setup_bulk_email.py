"""Setup script for bulk email system."""
import sys
import os
from loguru import logger

# Add app to path
sys.path.insert(0, '.')


def check_env_variables():
    """Check if required environment variables are set."""
    logger.info("Checking environment variables...")
    
    required_vars = [
        'SHEETS_SPREADSHEET_ID',
        'FOLLOWUP_DAYS_INTERVAL',
        'MAX_FOLLOWUP_COUNT',
        'REPLY_CHECK_INTERVAL_MINUTES'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"  ✓ {var}: {value}")
        else:
            logger.warning(f"  ✗ {var}: NOT SET")
            missing.append(var)
    
    return len(missing) == 0, missing


def check_credentials():
    """Check if API credentials exist."""
    logger.info("\nChecking API credentials...")
    
    credentials = {
        'Gmail': 'credentials/gmail_token.json',
        'Sheets': 'credentials/sheets_credentials.json'
    }
    
    all_exist = True
    for name, path in credentials.items():
        if os.path.exists(path):
            logger.info(f"  ✓ {name} credentials found: {path}")
        else:
            logger.warning(f"  ✗ {name} credentials missing: {path}")
            all_exist = False
    
    return all_exist


def create_tracking_sheet():
    """Create the email tracking sheet."""
    logger.info("\nInitializing email tracking sheet...")
    
    try:
        from app.services.email_tracker_service import EmailTrackerService
        from app.core.config import settings
        
        if not settings.SHEETS_SPREADSHEET_ID:
            logger.error("  ✗ SHEETS_SPREADSHEET_ID not set")
            return False
        
        tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)
        tracker.create_tracking_sheet()
        
        logger.info("  ✓ Email tracking sheet initialized")
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Failed to create tracking sheet: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS")
    logger.info("=" * 60)
    
    logger.info("\n1. Start the FastAPI server:")
    logger.info("   uvicorn app.main:app --reload")
    
    logger.info("\n2. Test the bulk email endpoint:")
    logger.info("   curl -X POST http://localhost:8000/api/v1/bulk-email/send-bulk-emails \\")
    logger.info("     -H 'Content-Type: application/json' \\")
    logger.info("     -d '{")
    logger.info('       "recipients": ["test@example.com"],')
    logger.info('       "subject": "Test Email",')
    logger.info('       "body": "<p>This is a test email</p>"')
    logger.info("     }'")
    
    logger.info("\n3. Check tracking status:")
    logger.info("   curl http://localhost:8000/api/v1/bulk-email/tracking-status")
    
    logger.info("\n4. Enable background workers (optional):")
    logger.info("   Add to .env: ENABLE_BACKGROUND_WORKERS=true")
    logger.info("   Then restart the server")
    
    logger.info("\n5. View API documentation:")
    logger.info("   http://localhost:8000/docs")
    
    logger.info("\nFor more information, see BULK_EMAIL_GUIDE.md")


def main():
    """Run setup checks."""
    logger.info("=" * 60)
    logger.info("BULK EMAIL SYSTEM SETUP")
    logger.info("=" * 60 + "\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment variables
    env_ok, missing_vars = check_env_variables()
    
    # Check credentials
    creds_ok = check_credentials()
    
    # Create tracking sheet
    sheet_ok = False
    if env_ok and creds_ok:
        sheet_ok = create_tracking_sheet()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SETUP SUMMARY")
    logger.info("=" * 60)
    
    if env_ok:
        logger.info("✓ Environment variables configured")
    else:
        logger.warning(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        logger.info("  Add these to your .env file")
    
    if creds_ok:
        logger.info("✓ API credentials found")
    else:
        logger.warning("✗ API credentials missing")
        logger.info("  Run authentication scripts:")
        logger.info("    - For Gmail: See GMAIL_SETUP_GUIDE.md")
        logger.info("    - For Sheets: Run ./authenticate_apis.sh")
    
    if sheet_ok:
        logger.info("✓ Email tracking sheet initialized")
    else:
        logger.warning("✗ Email tracking sheet not initialized")
    
    # Print next steps
    if env_ok and creds_ok and sheet_ok:
        logger.info("\n✓ Setup complete! System is ready to use.")
        print_next_steps()
    else:
        logger.warning("\n⚠️  Setup incomplete. Please resolve the issues above.")


if __name__ == "__main__":
    main()
