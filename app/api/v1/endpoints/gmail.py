"""Gmail API endpoints."""
from fastapi import APIRouter, HTTPException
from loguru import logger
import secrets
import time
from typing import Dict, Tuple

from app.core.gmail_auth import (
    create_oauth_flow,
    save_credentials,
    is_authenticated,
)
from app.core.config import settings

router = APIRouter()

# In-memory OAuth state store: {state_token: issued_at_timestamp}
# Values older than STATE_TTL_SECONDS are rejected.
_STATE_TTL_SECONDS = 600  # 10 minutes
_oauth_states: Dict[str, float] = {}


def _issue_state() -> str:
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.monotonic()
    return state


def _consume_state(state: str) -> bool:
    """Return True and remove state if valid; False otherwise."""
    issued_at = _oauth_states.pop(state, None)
    if issued_at is None:
        return False
    return (time.monotonic() - issued_at) < _STATE_TTL_SECONDS


@router.get("/authenticate")
async def start_gmail_auth():
    """Start Gmail OAuth flow."""
    try:
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/gmail/callback"
        flow = create_oauth_flow(redirect_uri)
        state = _issue_state()

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        return {
            "authorization_url": authorization_url,
            "message": "Visit this URL to authorize Gmail",
        }

    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start Gmail authentication")


@router.get("/callback")
async def gmail_oauth_callback(code: str, state: str):
    """OAuth callback endpoint."""
    try:
        if not _consume_state(state):
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

        redirect_uri = f"{settings.API_BASE_URL}/api/v1/gmail/callback"
        flow = create_oauth_flow(redirect_uri)

        flow.fetch_token(code=code)
        creds = flow.credentials

        save_credentials(creds)

        return {"success": True, "message": "Gmail authenticated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail="Gmail OAuth callback failed")


@router.get("/status")
async def check_gmail_status():
    """Check Gmail authentication status."""
    authenticated = is_authenticated()
    
    return {
        "authenticated": authenticated,
        "message": "Gmail authenticated" if authenticated else "Not authenticated"
    }
