"""
Claude authentication helper — supports both Anthropic API keys and
Claude Code subscription OAuth tokens with auto-refresh.

API key format:    sk-ant-api03-...  (from console.anthropic.com)
OAuth token format: sk-ant-oat01-... (from Claude Pro/Max subscription)
Refresh token:     sk-ant-ort01-...

Usage:
    from services.claude_auth import get_claude_client
    client = get_claude_client()
"""

import json
import time
import httpx
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY
import db

# OAuth refresh endpoint
OAUTH_TOKEN_URL = "https://console.anthropic.com/api/oauth/token"
OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"

# Cache for refreshed tokens
_token_cache = {
    "access_token": None,
    "expires_at": 0,
}


def _is_oauth_token(key):
    """Check if a key is a Claude Code OAuth token (not an API key)."""
    return key and key.startswith("sk-ant-oat")


def _is_refresh_token(key):
    """Check if a key is an OAuth refresh token."""
    return key and key.startswith("sk-ant-ort")


def _get_stored_credentials():
    """Get the stored API key or OAuth token from DB / env."""
    api_key = db.get_setting("anthropic_api_key") or ANTHROPIC_API_KEY
    refresh_token = db.get_setting("claude_refresh_token", "")
    return api_key, refresh_token


def _refresh_oauth_token(refresh_token):
    """Use a refresh token to get a new access token."""
    try:
        response = httpx.post(
            OAUTH_TOKEN_URL,
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": OAUTH_CLIENT_ID,
            },
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token", "")
            expires_in = data.get("expires_in", 28800)

            # Cache the new token
            _token_cache["access_token"] = access_token
            _token_cache["expires_at"] = time.time() + expires_in - 300  # 5min buffer

            # Save the new access token to DB
            db.save_setting("anthropic_api_key", access_token)

            # Update refresh token if a new one was issued
            new_refresh = data.get("refresh_token")
            if new_refresh:
                db.save_setting("claude_refresh_token", new_refresh)

            return access_token
        else:
            print(f"OAuth refresh failed: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        print(f"OAuth refresh error: {e}")
        return None


def _get_valid_token():
    """Get a valid access token, refreshing if needed."""
    api_key, refresh_token = _get_stored_credentials()

    if not api_key:
        return None, "no_key"

    # Standard API key — no refresh needed
    if not _is_oauth_token(api_key):
        return api_key, "api_key"

    # OAuth token — check if cached token is still valid
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"], "oauth"

    # OAuth token — try to use the stored one first
    # If we have a refresh token, refresh proactively
    if refresh_token and _is_refresh_token(refresh_token):
        new_token = _refresh_oauth_token(refresh_token)
        if new_token:
            return new_token, "oauth"

    # Fall back to the stored token (may be expired)
    return api_key, "oauth"


def get_claude_client():
    """Get an Anthropic client configured for the stored auth method.
    Returns None if no credentials are configured.
    """
    token, auth_type = _get_valid_token()
    if not token:
        return None

    if auth_type == "oauth":
        # OAuth tokens use Bearer auth — create client with custom default headers
        return Anthropic(
            api_key=token,
            default_headers={"Authorization": f"Bearer {token}"},
        )
    else:
        # Standard API key
        return Anthropic(api_key=token)


def test_credentials(key_or_token):
    """Test if a key/token works. Returns (success: bool, message: str, token_type: str)."""
    if not key_or_token or not key_or_token.strip():
        return False, "No key provided.", "unknown"

    key = key_or_token.strip()

    if _is_refresh_token(key):
        # It's a refresh token — exchange it for an access token first
        new_token = _refresh_oauth_token(key)
        if not new_token:
            return False, "Failed to exchange refresh token for access token.", "refresh_token"
        # Save both tokens
        db.save_setting("anthropic_api_key", new_token)
        db.save_setting("claude_refresh_token", key)
        key = new_token
        token_type = "oauth_refresh"
    elif _is_oauth_token(key):
        token_type = "oauth"
    else:
        token_type = "api_key"

    # Test the key/token
    try:
        if _is_oauth_token(key):
            client = Anthropic(
                api_key=key,
                default_headers={"Authorization": f"Bearer {key}"},
            )
        else:
            client = Anthropic(api_key=key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        return True, f"Connected successfully ({token_type}).", token_type
    except Exception as e:
        return False, f"Test failed: {str(e)[:150]}", token_type
