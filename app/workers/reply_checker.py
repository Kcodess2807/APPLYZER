"""Background worker for checking email replies."""
import asyncio
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any

from app.services.gmail_service import GmailService
from app.services.email_tracker_service import EmailTrackerService
from app.core.config import settings


class ReplyChecker:
    """Worker for checking email replies in tracked threads."""
    
    def __init__(self, spreadsheet_id: str = None):
        """Initialize reply checker."""
        self.gmail_service = GmailService()
        self.tracker_service = EmailTrackerService(spreadsheet_id)
        self.batch_size = 20  # Process 20 threads per cycle
    
    async def check_replies(self) -> Dict[str, Any]:
        """Check for replies in tracked email threads."""
        logger.info("Starting reply check cycle...")
        
        # Get emails with SENT status
        sent_emails = self.tracker_service.get_emails_by_status("SENT")
        
        if not sent_emails:
            logger.info("No emails to check for replies")
            return {
                'checked': 0,
                'replies_found': 0,
                'errors': 0
            }
        
        # Process in batches
        total_checked = 0
        replies_found = 0
        errors = 0
        
        # Limit to batch_size to avoid rate limits
        emails_to_check = sent_emails[:self.batch_size]
        
        logger.info(f"Checking {len(emails_to_check)} threads for replies")
        
        for email_data in emails_to_check:
            try:
                thread_id = email_data.get('thread_id')
                row = email_data.get('row')
                recipient = email_data.get('email')
                
                if not thread_id:
                    logger.warning(f"No thread_id for row {row}")
                    continue
                
                # Check if thread has replies
                has_reply = self.gmail_service.check_thread_replies(thread_id)
                
                if has_reply:
                    # Update status to REPLIED
                    self.tracker_service.update_email_status(row, "REPLIED")
                    replies_found += 1
                    logger.info(f"✓ Reply detected for {recipient} (thread: {thread_id})")
                
                total_checked += 1
                
                # Rate limiting: small delay between checks
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error checking thread {email_data.get('thread_id')}: {e}")
                errors += 1
        
        result = {
            'checked': total_checked,
            'replies_found': replies_found,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Reply check complete: {total_checked} checked, {replies_found} replies found")

        # After checking replies, fire any due DB-backed auto follow-ups
        await self._process_due_followups()

        return result

    async def _process_due_followups(self):
        """Send auto follow-ups for DB applications whose scheduled time has passed."""
        try:
            from app.database.base import SessionLocal
            from app.services.followup_service import FollowUpService

            db = SessionLocal()
            try:
                service = FollowUpService(db)
                due = service.get_due_followups()
                if not due:
                    return
                logger.info(f"Found {len(due)} application(s) with due auto follow-ups")
                for app in due:
                    try:
                        result = service.send_followup(str(app.id))
                        if result.get("success"):
                            logger.info(f"✓ Auto follow-up sent for application {app.id}")
                        else:
                            logger.warning(f"✗ Auto follow-up failed for {app.id}: {result.get('error')}")
                        await asyncio.sleep(2)  # rate limit
                    except ValueError as e:
                        # Business-rule violation (e.g. reply arrived between checks) — skip silently
                        logger.debug(f"Skipping auto follow-up for {app.id}: {e}")
                    except Exception as e:
                        logger.error(f"Error sending auto follow-up for {app.id}: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in _process_due_followups: {e}")

    async def run_continuous(self):
        """Run reply checker continuously with configured interval."""
        interval_seconds = settings.REPLY_CHECK_INTERVAL_MINUTES * 60
        
        logger.info(f"Starting continuous reply checker (interval: {settings.REPLY_CHECK_INTERVAL_MINUTES} minutes)")
        
        while True:
            try:
                await self.check_replies()
            except Exception as e:
                logger.error(f"Error in reply checker cycle: {e}")
            
            logger.info(f"Sleeping for {settings.REPLY_CHECK_INTERVAL_MINUTES} minutes...")
            await asyncio.sleep(interval_seconds)


async def start_reply_checker(spreadsheet_id: str = None):
    """Start the reply checker worker."""
    checker = ReplyChecker(spreadsheet_id)
    await checker.run_continuous()
