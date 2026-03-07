"""Gmail OAuth 2.0 authentication."""
import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from loguru import logger

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

CREDENTIALS_FILE = 'credentials/gmail_credentials.json'
TOKEN_FILE = 'credentials/gmail_token.json'


def get_gmail_credentials():
    """Get or refresh Gmail credentials."""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
    
    return creds


def save_credentials(creds):
    """Save credentials to file."""
    Path('credentials').mkdir(exist_ok=True)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    logger.info("Gmail credentials saved")


def create_oauth_flow(redirect_uri: str):
    """Create OAuth flow for authentication."""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow


def is_authenticated():
    """Check if user is authenticated with Gmail."""
    creds = get_gmail_credentials()
    return creds is not None and creds.valid
