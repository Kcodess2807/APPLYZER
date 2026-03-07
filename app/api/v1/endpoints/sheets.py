"""Google Sheets API endpoints."""
from fastapi import APIRouter, HTTPException
from loguru import logger
import json
import secrets
import time
from typing import Dict

import requests as req
from google.oauth2.credentials import Credentials

from app.core.sheets_auth import (
    create_oauth_flow,
    save_credentials,
    is_authenticated,
)
from app.core.config import settings

router = APIRouter()

# In-memory OAuth state store: {state_token: issued_at_timestamp}
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
async def start_sheets_auth():
    """Start Google Sheets OAuth flow."""
    try:
        redirect_uri = f"{settings.API_BASE_URL}/api/v1/sheets/callback"
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
            "message": "Visit this URL to authorize Google Sheets",
        }

    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start Sheets authentication")


@router.get("/callback")
async def sheets_oauth_callback(code: str, state: str):
    """OAuth callback endpoint."""
    try:
        if not _consume_state(state):
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

        redirect_uri = f"{settings.API_BASE_URL}/api/v1/sheets/callback"

        with open("credentials/sheets_credentials.json", "r") as f:
            client_config = json.load(f)

        client_id = client_config["web"]["client_id"]
        client_secret = client_config["web"]["client_secret"]

        token_url = "https://oauth2.googleapis.com/token"
        response = req.post(
            token_url,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_data = response.json()

        if "error" in token_data:
            logger.error(f"Token exchange failed: {token_data['error']}")
            raise HTTPException(status_code=400, detail="Token exchange failed")

        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=token_data.get("scope", "").split(),
        )

        save_credentials(creds)
        logger.info("Google Sheets authenticated successfully")

        return {
            "success": True,
            "message": "Google Sheets authenticated successfully! You can close this window.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail="Sheets OAuth callback failed")


@router.get("/status")
async def check_sheets_status():
    """Check Google Sheets authentication status."""
    authenticated = is_authenticated()
    
    return {
        "authenticated": authenticated,
        "message": "Sheets authenticated" if authenticated else "Not authenticated"
    }
