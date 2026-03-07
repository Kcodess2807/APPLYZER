"""Simple script to initialize the EmailTracking sheet."""
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from loguru import logger

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

CREDENTIALS_FILE = 'credentials/sheets_credentials.json'
TOKEN_FILE = 'credentials/sheets_token.json'


def get_sheets_service():
    """Get authenticated Sheets service."""
    creds = None
    
    # Check if token file exists
    if os.path.exists(TOKEN_FILE):
        logger.info("Loading existing token...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow...")
            logger.info("A browser window will open for authentication.")
            logger.info("Make sure to use port 8000 for the redirect URI.")
            
            # Use port 8000 to match the configured redirect URIs
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, 
                SCOPES,
                redirect_uri='http://localhost:8000'
            )
            
            # Run local server on port 8000
            creds = flow.run_local_server(
                port=8000,
                authorization_prompt_message='Please visit this URL to authorize: {url}',
                success_message='Authentication successful! You can close this window.',
                open_browser=True
            )
        
        # Save credentials
        Path('credentials').mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        logger.info(f"✓ Token saved to {TOKEN_FILE}")
    
    service = build('sheets', 'v4', credentials=creds)
    return service


def create_email_tracking_sheet(spreadsheet_id):
    """Create EmailTracking sheet with headers."""
    service = get_sheets_service()
    
    headers = [
        "email", "subject", "thread_id", "status", 
        "sent_at", "followup_count", "message_id", "last_checked"
    ]
    
    try:
        # Check if sheet exists
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        sheets = spreadsheet.get('sheets', [])
        sheet_exists = any(
            sheet['properties']['title'] == 'EmailTracking' 
            for sheet in sheets
        )
        
        if sheet_exists:
            logger.info("✓ EmailTracking sheet already exists")
        else:
            # Create new sheet
            logger.info("Creating EmailTracking sheet...")
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'EmailTracking'
                        }
                    }
                }]
            }
            
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            logger.info("✓ EmailTracking sheet created")
        
        # Add/update headers
        logger.info("Setting up headers...")
        header_body = {'values': [headers]}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='EmailTracking!A1:H1',
            valueInputOption='USER_ENTERED',
            body=header_body
        ).execute()
        
        logger.info("✓ Headers configured")
        logger.info("\nEmailTracking sheet is ready!")
        logger.info(f"View it at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("EMAIL TRACKING SHEET INITIALIZATION")
    logger.info("=" * 60 + "\n")
    
    # Get spreadsheet ID from environment
    spreadsheet_id = os.getenv('SHEETS_SPREADSHEET_ID')
    
    if not spreadsheet_id:
        logger.error("✗ SHEETS_SPREADSHEET_ID not set in .env file")
        logger.info("\nPlease add your spreadsheet ID to .env:")
        logger.info("  SHEETS_SPREADSHEET_ID=your-spreadsheet-id-here")
        logger.info("\nGet the ID from your spreadsheet URL:")
        logger.info("  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        return
    
    logger.info(f"Spreadsheet ID: {spreadsheet_id}\n")
    
    # Check credentials file
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error(f"✗ Credentials file not found: {CREDENTIALS_FILE}")
        logger.info("\nPlease ensure you have the OAuth credentials file.")
        return
    
    logger.info(f"✓ Credentials file found: {CREDENTIALS_FILE}\n")
    
    # Create tracking sheet
    success = create_email_tracking_sheet(spreadsheet_id)
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✓ SETUP COMPLETE!")
        logger.info("=" * 60)
        logger.info("\nYou can now:")
        logger.info("  1. Start the server: uvicorn app.main:app --reload")
        logger.info("  2. Send bulk emails via API")
        logger.info("  3. Track emails in your Google Sheet")
    else:
        logger.info("\n" + "=" * 60)
        logger.info("✗ SETUP FAILED")
        logger.info("=" * 60)
        logger.info("\nPlease check the error messages above.")


if __name__ == "__main__":
    main()
