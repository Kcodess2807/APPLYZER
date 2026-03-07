"""Example usage of the bulk email system."""
import asyncio
import sys
from loguru import logger

# Add app to path
sys.path.insert(0, '.')

from app.services.bulk_email_service import BulkEmailService
from app.core.config import settings


async def example_send_bulk_emails():
    """Example: Send bulk emails to multiple recipients."""
    logger.info("Example: Sending bulk emails")
    
    # Initialize service
    bulk_service = BulkEmailService(settings.SHEETS_SPREADSHEET_ID)
    
    # Prepare email data
    recipients = [
        "hr@company1.com",
        "jobs@company2.com",
        "careers@company3.com"
    ]
    
    subject = "Application for Software Engineer Position"
    
    body = """
    <html>
    <body>
        <p>Dear Hiring Manager,</p>
        
        <p>I am writing to express my strong interest in the Software Engineer position at your company.</p>
        
        <p>With 5 years of experience in full-stack development and a proven track record of delivering 
        high-quality software solutions, I am confident I would be a valuable addition to your team.</p>
        
        <p>Key highlights of my experience:</p>
        <ul>
            <li>Proficient in Python, JavaScript, and modern web frameworks</li>
            <li>Experience with cloud platforms (AWS, GCP)</li>
            <li>Strong background in API design and microservices</li>
            <li>Excellent problem-solving and communication skills</li>
        </ul>
        
        <p>I would welcome the opportunity to discuss how my skills and experience align with your needs.</p>
        
        <p>Thank you for your consideration. I look forward to hearing from you.</p>
        
        <p>Best regards,<br>
        [Your Name]<br>
        [Your Email]<br>
        [Your Phone]</p>
    </body>
    </html>
    """
    
    # Send bulk emails
    logger.info(f"Sending emails to {len(recipients)} recipients...")
    result = await bulk_service.send_bulk_emails(
        recipients=recipients,
        subject=subject,
        body=body
    )
    
    # Display results
    logger.info(f"\nResults:")
    logger.info(f"  Total sent: {result['total_sent']}")
    logger.info(f"  Failed: {result['failed']}")
    
    if result['results']:
        logger.info(f"\nSuccessfully sent emails:")
        for email_result in result['results']:
            logger.info(f"  ✓ {email_result['email']} (Thread: {email_result['thread_id']})")
    
    if result.get('errors'):
        logger.warning(f"\nFailed emails:")
        for error in result['errors']:
            logger.warning(f"  ✗ {error['email']}: {error['error']}")
    
    return result


async def example_check_replies():
    """Example: Check for replies to sent emails."""
    logger.info("\nExample: Checking for replies")
    
    from app.workers.reply_checker import ReplyChecker
    
    checker = ReplyChecker(settings.SHEETS_SPREADSHEET_ID)
    result = await checker.check_replies()
    
    logger.info(f"\nReply Check Results:")
    logger.info(f"  Threads checked: {result['checked']}")
    logger.info(f"  Replies found: {result['replies_found']}")
    logger.info(f"  Errors: {result['errors']}")
    
    return result


async def example_send_followups():
    """Example: Send follow-up emails."""
    logger.info("\nExample: Sending follow-up emails")
    
    from app.workers.followup_scheduler import FollowUpScheduler
    
    scheduler = FollowUpScheduler(settings.SHEETS_SPREADSHEET_ID)
    result = await scheduler.send_followups()
    
    logger.info(f"\nFollow-up Results:")
    logger.info(f"  Follow-ups sent: {result['sent']}")
    logger.info(f"  Errors: {result['errors']}")
    
    return result


async def example_get_statistics():
    """Example: Get email tracking statistics."""
    logger.info("\nExample: Getting tracking statistics")
    
    from app.services.email_tracker_service import EmailTrackerService
    
    tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)
    
    sent_emails = tracker.get_emails_by_status("SENT")
    replied_emails = tracker.get_emails_by_status("REPLIED")
    followup_emails = tracker.get_emails_for_followup()
    
    total = len(sent_emails) + len(replied_emails)
    reply_rate = (len(replied_emails) / total * 100) if total > 0 else 0
    
    logger.info(f"\nStatistics:")
    logger.info(f"  Total sent: {len(sent_emails)}")
    logger.info(f"  Total replied: {len(replied_emails)}")
    logger.info(f"  Pending follow-up: {len(followup_emails)}")
    logger.info(f"  Reply rate: {reply_rate:.1f}%")
    
    return {
        'sent': len(sent_emails),
        'replied': len(replied_emails),
        'pending_followup': len(followup_emails),
        'reply_rate': reply_rate
    }


async def main():
    """Run examples."""
    logger.info("=" * 60)
    logger.info("BULK EMAIL SYSTEM - USAGE EXAMPLES")
    logger.info("=" * 60)
    
    # Check configuration
    if not settings.SHEETS_SPREADSHEET_ID:
        logger.error("\n✗ SHEETS_SPREADSHEET_ID not set in .env file")
        logger.info("Please set SHEETS_SPREADSHEET_ID and try again")
        return
    
    logger.info(f"\nUsing spreadsheet: {settings.SHEETS_SPREADSHEET_ID}")
    
    # Example 1: Send bulk emails
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 1: Send Bulk Emails")
    logger.info("=" * 60)
    logger.info("\nNote: This will send actual emails!")
    logger.info("Comment out this example if you don't want to send emails now.\n")
    
    # Uncomment to run:
    # await example_send_bulk_emails()
    logger.info("(Skipped - uncomment in code to run)")
    
    # Example 2: Check for replies
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 2: Check for Replies")
    logger.info("=" * 60)
    await example_check_replies()
    
    # Example 3: Send follow-ups
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 3: Send Follow-up Emails")
    logger.info("=" * 60)
    logger.info("\nNote: This will send actual follow-up emails!")
    logger.info("Comment out this example if you don't want to send emails now.\n")
    
    # Uncomment to run:
    # await example_send_followups()
    logger.info("(Skipped - uncomment in code to run)")
    
    # Example 4: Get statistics
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 4: Get Tracking Statistics")
    logger.info("=" * 60)
    await example_get_statistics()
    
    logger.info("\n" + "=" * 60)
    logger.info("Examples completed!")
    logger.info("=" * 60)
    logger.info("\nTo use these functions in your code:")
    logger.info("  1. Import the services you need")
    logger.info("  2. Initialize with your spreadsheet ID")
    logger.info("  3. Call the async methods with await")
    logger.info("\nSee BULK_EMAIL_GUIDE.md for more information")


if __name__ == "__main__":
    asyncio.run(main())
