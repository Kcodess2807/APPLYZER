"""Test script for bulk email system."""
import asyncio
import sys
from loguru import logger

# Add app to path
sys.path.insert(0, '.')

from app.services.email_tracker_service import EmailTrackerService
from app.workers.reply_checker import ReplyChecker
from app.workers.followup_scheduler import FollowUpScheduler
from app.core.config import settings


async def test_tracker_service():
    """Test email tracker service."""
    logger.info("Testing EmailTrackerService...")
    
    try:
        tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)
        
        # Test creating tracking sheet
        logger.info("Creating tracking sheet...")
        tracker.create_tracking_sheet()
        logger.info("✓ Tracking sheet created/verified")
        
        # Test getting emails by status
        logger.info("Fetching SENT emails...")
        sent_emails = tracker.get_emails_by_status("SENT")
        logger.info(f"✓ Found {len(sent_emails)} SENT emails")
        
        # Test getting emails for follow-up
        logger.info("Fetching emails needing follow-up...")
        followup_emails = tracker.get_emails_for_followup()
        logger.info(f"✓ Found {len(followup_emails)} emails needing follow-up")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Tracker service test failed: {e}")
        return False


async def test_reply_checker():
    """Test reply checker."""
    logger.info("Testing ReplyChecker...")
    
    try:
        checker = ReplyChecker(settings.SHEETS_SPREADSHEET_ID)
        
        logger.info("Running reply check...")
        result = await checker.check_replies()
        
        logger.info(f"✓ Reply check completed:")
        logger.info(f"  - Checked: {result['checked']}")
        logger.info(f"  - Replies found: {result['replies_found']}")
        logger.info(f"  - Errors: {result['errors']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Reply checker test failed: {e}")
        return False


async def test_followup_scheduler():
    """Test follow-up scheduler."""
    logger.info("Testing FollowUpScheduler...")
    
    try:
        scheduler = FollowUpScheduler(settings.SHEETS_SPREADSHEET_ID)
        
        logger.info("Running follow-up check...")
        result = await scheduler.send_followups()
        
        logger.info(f"✓ Follow-up check completed:")
        logger.info(f"  - Sent: {result['sent']}")
        logger.info(f"  - Errors: {result['errors']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Follow-up scheduler test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("BULK EMAIL SYSTEM TEST SUITE")
    logger.info("=" * 60)
    
    # Check configuration
    logger.info("\nConfiguration:")
    logger.info(f"  - Spreadsheet ID: {settings.SHEETS_SPREADSHEET_ID or 'NOT SET'}")
    logger.info(f"  - Follow-up interval: {settings.FOLLOWUP_DAYS_INTERVAL} days")
    logger.info(f"  - Max follow-ups: {settings.MAX_FOLLOWUP_COUNT}")
    logger.info(f"  - Reply check interval: {settings.REPLY_CHECK_INTERVAL_MINUTES} minutes")
    
    if not settings.SHEETS_SPREADSHEET_ID:
        logger.error("\n✗ SHEETS_SPREADSHEET_ID not set in .env file")
        logger.info("Please set SHEETS_SPREADSHEET_ID in your .env file and try again")
        return
    
    # Run tests
    logger.info("\n" + "=" * 60)
    logger.info("Running Tests...")
    logger.info("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Tracker Service
    results.append(await test_tracker_service())
    logger.info("")
    
    # Test 2: Reply Checker
    results.append(await test_reply_checker())
    logger.info("")
    
    # Test 3: Follow-up Scheduler
    results.append(await test_followup_scheduler())
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✓ All tests passed!")
    else:
        logger.warning(f"✗ {total - passed} test(s) failed")
    
    logger.info("\nNote: This test requires:")
    logger.info("  1. Gmail API authentication (credentials/gmail_token.json)")
    logger.info("  2. Sheets API authentication (credentials/sheets_credentials.json)")
    logger.info("  3. Valid SHEETS_SPREADSHEET_ID in .env")


if __name__ == "__main__":
    asyncio.run(main())
