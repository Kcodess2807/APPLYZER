"""Google Sheets OAuth 2.0 authentication."""
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
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


def get_sheets_credentials():
    """Get or refresh Sheets credentials."""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.warning(f"Could not load token file: {e}")
            creds = None
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
        except Exception as e:
            logger.warning(f"Could not refresh token: {e}")
            creds = None
    
    return creds


def save_credentials(creds):
    """Save credentials to file."""
    Path('credentials').mkdir(exist_ok=True)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    logger.info("Sheets credentials saved")


def create_oauth_flow(redirect_uri: str):
    """Create OAuth flow for authentication."""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow


def is_authenticated():
    """Check if user is authenticated with Sheets."""
    creds = get_sheets_credentials()
    return creds is not None and creds.valid
