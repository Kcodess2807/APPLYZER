"""Google Sheets API endpoints."""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.sheets_auth import (
    create_oauth_flow,
    save_credentials,
    is_authenticated
)
from app.core.config import settings

router = APIRouter()


@router.get("/authenticate")
async def start_sheets_auth():
    """Start Google Sheets OAuth flow."""
    try:
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/sheets/callback"
        flow = create_oauth_flow(redirect_uri)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return {
            "authorization_url": authorization_url,
            "message": "Visit this URL to authorize Google Sheets"
        }
        
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def sheets_oauth_callback(code: str, state: str = None):
    """OAuth callback endpoint."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        import requests as req
        
        # Exchange code for token directly
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/sheets/callback"
        
        # Get client config
        import json
        with open('credentials/sheets_credentials.json', 'r') as f:
            client_config = json.load(f)
        
        client_id = client_config['web']['client_id']
        client_secret = client_config['web']['client_secret']
        
        # Exchange authorization code for tokens
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = req.post(token_url, data=data)
        token_data = response.json()
        
        if 'error' in token_data:
            raise Exception(f"Token exchange failed: {token_data['error']}")
        
        # Create credentials object
        creds = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=token_data.get('scope', '').split()
        )
        
        save_credentials(creds)
        
        logger.info("✓ Google Sheets authenticated successfully")
        
        return {
            "success": True, 
            "message": "Google Sheets authenticated successfully! You can close this window."
        }
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def check_sheets_status():
    """Check Google Sheets authentication status."""
    authenticated = is_authenticated()
    
    return {
        "authenticated": authenticated,
        "message": "Sheets authenticated" if authenticated else "Not authenticated"
    }
