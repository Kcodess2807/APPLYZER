"""Gmail API endpoints."""
from fastapi import APIRouter, HTTPException
from loguru import logger
import secrets
import time
from typing import Dict, Optional

from app.core.gmail_auth import (
    create_oauth_flow,
    save_credentials,
    is_authenticated,
)
from app.core.config import settings

router = APIRouter()

# In-memory OAuth state store: {state_token: (user_id, issued_at)}
_STATE_TTL_SECONDS = 600  # 10 minutes
_oauth_states: Dict[str, tuple] = {}


def _issue_state(user_id: str = None) -> str:
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = (user_id, time.monotonic())
    return state


def _consume_state(state: str):
    """Return (user_id, valid) and remove state."""
    entry = _oauth_states.pop(state, None)
    if entry is None:
        return None, False
    user_id, issued_at = entry
    if (time.monotonic() - issued_at) >= _STATE_TTL_SECONDS:
        return None, False
    return user_id, True


@router.get("/authenticate")
async def start_gmail_auth(user_id: Optional[str] = None):
    """Start Gmail OAuth flow for a specific user."""
    try:
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/gmail/callback"
        flow = create_oauth_flow(redirect_uri)
        state = _issue_state(user_id)

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
        user_id, valid = _consume_state(state)
        if not valid:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

        redirect_uri = f"{settings.API_BASE_URL}/api/v1/gmail/callback"
        flow = create_oauth_flow(redirect_uri)

        flow.fetch_token(code=code)
        creds = flow.credentials

        save_credentials(creds, user_id)

        return {"success": True, "message": "Gmail authenticated", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail="Gmail OAuth callback failed")


@router.get("/status")
async def check_gmail_status(user_id: Optional[str] = None):
    """Check Gmail authentication status for a user."""
    authenticated = is_authenticated(user_id)
    return {
        "authenticated": authenticated,
        "user_id": user_id,
        "message": "Gmail authenticated" if authenticated else "Not authenticated",
    }
