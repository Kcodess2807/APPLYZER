"""Gmail API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from loguru import logger

from app.core.gmail_auth import (
    create_oauth_flow,
    save_credentials,
    is_authenticated
)
from app.core.config import settings

router = APIRouter()


@router.get("/authenticate")
async def start_gmail_auth():
    """Start Gmail OAuth flow."""
    try:
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/gmail/callback"
        flow = create_oauth_flow(redirect_uri)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return {
            "authorization_url": authorization_url,
            "message": "Visit this URL to authorize Gmail"
        }
        
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def gmail_oauth_callback(code: str, state: str):
    """OAuth callback endpoint."""
    try:
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/gmail/callback"
        flow = create_oauth_flow(redirect_uri)
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        save_credentials(creds)
        
        return {"success": True, "message": "Gmail authenticated"}
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def check_gmail_status():
    """Check Gmail authentication status."""
    authenticated = is_authenticated()
    
    return {
        "authenticated": authenticated,
        "message": "Gmail authenticated" if authenticated else "Not authenticated"
    }
