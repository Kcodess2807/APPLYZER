"""View email tracking data from Google Sheets."""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from app.services.email_tracker_service import EmailTrackerService
from app.core.config import settings
from loguru import logger

def main():
    """View tracking data."""
    print("=" * 80)
    print("EMAIL TRACKING DATA")
    print("=" * 80)
    print()
    
    try:
        tracker = EmailTrackerService(settings.SHEETS_SPREADSHEET_ID)
        
        # Get all emails
        sent_emails = tracker.get_emails_by_status("SENT")
        replied_emails = tracker.get_emails_by_status("REPLIED")
        
        all_emails = sent_emails + replied_emails
        
        if not all_emails:
            print("No emails found in tracking sheet.")
            print()
            print("This could mean:")
            print("  1. The EmailTracking sheet doesn't exist")
            print("  2. The sheet is empty")
            print("  3. There's an authentication issue")
            print()
            print("Try running: python initialize_email_tracking.py")
            return
        
        print(f"Total emails tracked: {len(all_emails)}")
        print()
        
        # Display SENT emails
        if sent_emails:
            print(f"📧 SENT Emails ({len(sent_emails)}):")
            print("-" * 80)
            for email in sent_emails:
                print(f"  To: {email['email']}")
                print(f"  Subject: {email['subject']}")
                print(f"  Thread ID: {email['thread_id']}")
                print(f"  Sent: {email['sent_at']}")
                print(f"  Follow-ups: {email['followup_count']}")
                print()
        
        # Display REPLIED emails
        if replied_emails:
            print(f"✅ REPLIED Emails ({len(replied_emails)}):")
            print("-" * 80)
            for email in replied_emails:
                print(f"  To: {email['email']}")
                print(f"  Subject: {email['subject']}")
                print(f"  Thread ID: {email['thread_id']}")
                print(f"  Sent: {email['sent_at']}")
                print()
        
        print("=" * 80)
        print()
        print("View in Google Sheets:")
        print(f"https://docs.google.com/spreadsheets/d/{settings.SHEETS_SPREADSHEET_ID}/edit")
        print()
        print("Look for the 'EmailTracking' tab!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print()
        print("Error reading tracking data.")
        print()
        print("Possible issues:")
        print("  1. EmailTracking sheet doesn't exist")
        print("     Run: python initialize_email_tracking.py")
        print()
        print("  2. Authentication issue")
        print("     Run: python check_auth_status.py")
        print()
        print("  3. Wrong spreadsheet ID")
        print(f"     Current: {settings.SHEETS_SPREADSHEET_ID}")

if __name__ == "__main__":
    main()
