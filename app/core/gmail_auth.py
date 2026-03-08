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


def _token_file(user_id: str = None) -> str:
    if user_id:
        return f'credentials/gmail_token_{user_id}.json'
    return TOKEN_FILE


def get_gmail_credentials(user_id: str = None):
    """Get or refresh Gmail credentials for a user."""
    creds = None
    token_file = _token_file(user_id)

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds, user_id)

    return creds


def save_credentials(creds, user_id: str = None):
    """Save credentials to file."""
    Path('credentials').mkdir(exist_ok=True)
    token_file = _token_file(user_id)
    with open(token_file, 'w') as token:
        token.write(creds.to_json())
    logger.info(f"Gmail credentials saved{' for user ' + user_id if user_id else ''}")


def create_oauth_flow(redirect_uri: str):
    """Create OAuth flow for authentication."""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow


def is_authenticated(user_id: str = None) -> bool:
    """Check if a user is authenticated with Gmail."""
    creds = get_gmail_credentials(user_id)
    return creds is not None and creds.valid
