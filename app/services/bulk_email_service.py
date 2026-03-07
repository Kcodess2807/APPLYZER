"""Service for sending bulk emails with tracking."""
from typing import List, Dict, Any
from loguru import logger
import asyncio
from time import sleep

from app.services.gmail_service import GmailService
from app.services.email_tracker_service import EmailTrackerService


class BulkEmailService:
    """Service for sending bulk emails with rate limiting."""
    
    def __init__(self, spreadsheet_id: str = None):
        """Initialize bulk email service."""
        self.gmail_service = GmailService()
        self.tracker_service = EmailTrackerService(spreadsheet_id)
    
    async def send_bulk_emails(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send emails to multiple recipients with tracking."""
        results = []
        errors = []
        
        logger.info(f"Starting bulk email send to {len(recipients)} recipients")
        
        for i, recipient in enumerate(recipients):
            try:
                # Rate limiting: sleep between emails to avoid 429 errors
                if i > 0 and i % 10 == 0:
                    logger.info(f"Processed {i} emails, pausing for rate limit...")
                    await asyncio.sleep(2)  # 2 second pause every 10 emails
                
                # Send email
                result = self.gmail_service.send_email(
                    to=recipient,
                    subject=subject,
                    body_html=body
                )
                
                if result.get('success'):
                    # Track in Google Sheets
                    thread_id = result.get('thread_id')
                    message_id = result.get('message_id')
                    
                    self.tracker_service.add_email_tracking(
                        email=recipient,
                        subject=subject,
                        thread_id=thread_id,
                        message_id=message_id,
                        status="SENT"
                    )
                    
                    results.append({
                        'email': recipient,
                        'subject': subject,
                        'thread_id': thread_id,
                        'status': 'SENT',
                        'sent_at': '',
                        'message_id': message_id
                    })
                    
                    logger.info(f"✓ Sent email to {recipient}")
                else:
                    errors.append({
                        'email': recipient,
                        'error': result.get('error', 'Unknown error')
                    })
                    logger.error(f"✗ Failed to send email to {recipient}: {result.get('error')}")
                
                # Small delay between each email
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error sending email to {recipient}: {e}")
                errors.append({
                    'email': recipient,
                    'error': str(e)
                })
        
        success_count = len(results)
        failed_count = len(errors)
        
        logger.info(f"Bulk email complete: {success_count} sent, {failed_count} failed")

        return {
            'success': success_count > 0,
            'total_sent': success_count,
            'failed': failed_count,
            'results': results,
            'errors': errors if errors else None
        }

    async def send_bulk_emails_with_attachments(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        attachment_paths: List[str]
    ) -> Dict[str, Any]:
        """Send emails with file attachments to multiple recipients with tracking."""
        results = []
        errors = []

        logger.info(f"Starting bulk email with attachments to {len(recipients)} recipients")

        for i, recipient in enumerate(recipients):
            try:
                if i > 0 and i % 10 == 0:
                    logger.info(f"Processed {i} emails, pausing for rate limit...")
                    await asyncio.sleep(2)

                result = self.gmail_service.send_email(
                    to=recipient,
                    subject=subject,
                    body_html=body,
                    attachments=attachment_paths if attachment_paths else None,
                )

                if result.get('success'):
                    thread_id = result.get('thread_id')
                    message_id = result.get('message_id')

                    self.tracker_service.add_email_tracking(
                        email=recipient,
                        subject=subject,
                        thread_id=thread_id,
                        message_id=message_id,
                        status="SENT"
                    )

                    results.append({
                        'email': recipient,
                        'subject': subject,
                        'thread_id': thread_id,
                        'status': 'SENT',
                        'sent_at': '',
                        'message_id': message_id,
                    })

                    logger.info(f"✓ Sent email with attachments to {recipient}")
                else:
                    errors.append({'email': recipient, 'error': result.get('error', 'Unknown error')})
                    logger.error(f"✗ Failed to send to {recipient}: {result.get('error')}")

                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error sending to {recipient}: {e}")
                errors.append({'email': recipient, 'error': str(e)})

        success_count = len(results)
        failed_count = len(errors)

        logger.info(f"Bulk email with attachments complete: {success_count} sent, {failed_count} failed")

        return {
            'success': success_count > 0,
            'total_sent': success_count,
            'failed': failed_count,
            'results': results,
            'errors': errors if errors else None,
        }
