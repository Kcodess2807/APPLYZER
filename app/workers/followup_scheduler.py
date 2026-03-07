"""Background worker for sending follow-up emails."""
import asyncio
from datetime import datetime
from loguru import logger
from typing import Dict, Any

from app.services.gmail_service import GmailService
from app.services.email_tracker_service import EmailTrackerService
from app.services.ai_service import AIService
from app.core.config import settings


class FollowUpScheduler:
    """Worker for sending automated follow-up emails."""
    
    def __init__(self, spreadsheet_id: str = None):
        """Initialize follow-up scheduler."""
        self.gmail_service = GmailService()
        self.tracker_service = EmailTrackerService(spreadsheet_id)
        self.ai_service = AIService()
    
    def generate_followup_body(
        self,
        original_subject: str,
        followup_count: int,
        recipient_email: str = "",
        days_since_sent: int = 5
    ) -> str:
        """Generate follow-up email body using AI."""
        # Extract job info from subject if possible
        job_title = "the position"
        company_name = "your company"
        
        # Try to extract from subject (e.g., "Application for Software Engineer at TechCorp")
        if " at " in original_subject:
            parts = original_subject.split(" at ")
            if len(parts) == 2:
                company_name = parts[1].strip()
                if "for " in parts[0]:
                    job_title = parts[0].split("for ")[-1].strip()
        elif " - " in original_subject:
            parts = original_subject.split(" - ")
            if len(parts) >= 2:
                job_title = parts[0].strip()
                company_name = parts[1].strip() if len(parts) > 1 else company_name
        
        # Use AI to generate personalized follow-up
        followup_body = self.ai_service.generate_followup_email(
            original_subject=original_subject,
            job_title=job_title,
            company_name=company_name,
            followup_count=followup_count,
            user_name="",  # Will be added in signature
            days_since_sent=days_since_sent
        )
        
        return followup_body
    
    async def send_followups(self) -> Dict[str, Any]:
        """
        Send follow-up emails to recipients who haven't replied.
        
        Returns:
            Dict with sent count, error count, and timestamp
        """
        logger.info("Starting follow-up email cycle...")
        
        # Get emails that need follow-up
        try:
            emails_for_followup = self.tracker_service.get_emails_for_followup()
        except Exception as e:
            logger.error(f"Failed to retrieve emails for follow-up: {e}")
            return {
                'sent': 0,
                'errors': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
        
        if not emails_for_followup:
            logger.info("No emails need follow-up at this time")
            return {
                'sent': 0,
                'errors': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        logger.info(f"Found {len(emails_for_followup)} emails needing follow-up")
        
        sent_count = 0
        errors = 0
        error_details = []
        
        for email_data in emails_for_followup:
            try:
                # Validate required fields
                recipient = email_data.get('email')
                original_subject = email_data.get('subject')
                thread_id = email_data.get('thread_id')
                row = email_data.get('row')
                
                if not all([recipient, original_subject, thread_id, row]):
                    logger.warning(f"Skipping email with missing data: {email_data}")
                    errors += 1
                    error_details.append({
                        'email': recipient or 'unknown',
                        'error': 'Missing required fields'
                    })
                    continue
                
                followup_count = email_data.get('followup_count', 0)
                sent_at = email_data.get('sent_at', '')
                
                # Calculate days since sent
                days_since_sent = settings.FOLLOWUP_DAYS_INTERVAL
                try:
                    if sent_at:
                        from dateutil import parser
                        sent_date = parser.parse(sent_at)
                        days_since_sent = (datetime.now() - sent_date.replace(tzinfo=None)).days
                except Exception as date_error:
                    logger.warning(f"Could not parse date for {recipient}: {date_error}")
                
                # Generate follow-up subject
                followup_subject = f"Re: {original_subject}"
                
                # Generate follow-up body using AI
                try:
                    followup_body = self.generate_followup_body(
                        original_subject=original_subject,
                        followup_count=followup_count + 1,
                        recipient_email=recipient,
                        days_since_sent=days_since_sent
                    )
                except Exception as ai_error:
                    logger.error(f"AI generation failed for {recipient}: {ai_error}")
                    errors += 1
                    error_details.append({
                        'email': recipient,
                        'error': f'AI generation failed: {str(ai_error)}'
                    })
                    continue
                
                # Send follow-up email using the same thread
                result = self._send_followup_in_thread(
                    to=recipient,
                    subject=followup_subject,
                    body=followup_body,
                    thread_id=thread_id
                )
                
                if result.get('success'):
                    # Update tracking: increment followup_count and update sent_at
                    try:
                        self.tracker_service.increment_followup_count(row)
                        sent_count += 1
                        logger.info(f"✓ Sent follow-up #{followup_count + 1} to {recipient}")
                    except Exception as update_error:
                        logger.error(f"Failed to update tracking for {recipient}: {update_error}")
                        # Email was sent but tracking update failed
                        sent_count += 1
                        logger.warning(f"Follow-up sent to {recipient} but tracking update failed")
                else:
                    errors += 1
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"✗ Failed to send follow-up to {recipient}: {error_msg}")
                    error_details.append({
                        'email': recipient,
                        'error': error_msg
                    })
                
                # Rate limiting: delay between follow-ups to avoid Gmail API limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error sending follow-up to {email_data.get('email', 'unknown')}: {e}", exc_info=True)
                errors += 1
                error_details.append({
                    'email': email_data.get('email', 'unknown'),
                    'error': str(e)
                })
        
        result = {
            'sent': sent_count,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }
        
        # Include error details if there were any errors
        if error_details:
            result['error_details'] = error_details[:10]  # Limit to first 10 errors
        
        logger.info(f"Follow-up cycle complete: {sent_count} sent, {errors} errors")
        
        return result
    
    def _send_followup_in_thread(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Send follow-up email in existing thread.
        
        Args:
            to: Recipient email address
            subject: Email subject (should start with "Re:")
            body: HTML email body
            thread_id: Gmail thread ID to reply to
            
        Returns:
            Dict with success status, message_id, thread_id, or error
        """
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            
            # Validate inputs
            if not to or not subject or not body or not thread_id:
                raise ValueError("Missing required parameters for sending follow-up")
            
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Attach HTML body
            msg_html = MIMEText(body, 'html')
            message.attach(msg_html)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send with threadId to keep in same conversation
            send_result = self.gmail_service.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': thread_id
                }
            ).execute()
            
            logger.info(f"Follow-up sent successfully to {to} in thread {thread_id}")
            
            return {
                'success': True,
                'message_id': send_result.get('id'),
                'thread_id': send_result.get('threadId')
            }
            
        except ValueError as ve:
            logger.error(f"Validation error sending follow-up: {ve}")
            return {'success': False, 'error': str(ve)}
        except Exception as error:
            logger.error(f"Error sending follow-up to {to}: {error}", exc_info=True)
            return {'success': False, 'error': str(error)}
    
    async def run_continuous(self):
        """Run follow-up scheduler continuously (once per day)."""
        interval_seconds = 24 * 60 * 60  # 24 hours
        
        logger.info("Starting continuous follow-up scheduler (runs daily)")
        
        while True:
            try:
                await self.send_followups()
            except Exception as e:
                logger.error(f"Error in follow-up scheduler cycle: {e}")
            
            logger.info("Sleeping for 24 hours until next follow-up cycle...")
            await asyncio.sleep(interval_seconds)


async def start_followup_scheduler(spreadsheet_id: str = None):
    """Start the follow-up scheduler worker."""
    scheduler = FollowUpScheduler(spreadsheet_id)
    await scheduler.run_continuous()
