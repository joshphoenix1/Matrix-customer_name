"""
Slack channel — Slack SDK fetch user's messages from joined channels
for persona training.
"""

import json
import hashlib
import time
import db
from services.persona_engine import _chunk_text


def test_connection() -> tuple:
    """Call auth.test to verify token, return workspace name. Returns (bool, str)."""
    token = db.get_setting("slack_bot_token")
    if not token:
        return False, "Slack Bot Token not configured."

    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        client = WebClient(token=token)
        response = client.auth_test()

        if response["ok"]:
            team = response.get("team", "Unknown")
            user = response.get("user", "Unknown")
            user_id = response.get("user_id", "")
            # Auto-save user_id
            if user_id:
                db.save_setting("slack_user_id", user_id)
            return True, f"Connected to {team} as {user}"
        return False, "auth.test returned not ok"
    except Exception as e:
        return False, f"Connection failed: {e}"


def fetch_user_id(token: str) -> tuple:
    """Call auth.test, return (success, message, user_id)."""
    try:
        from slack_sdk import WebClient

        client = WebClient(token=token)
        response = client.auth_test()

        if response["ok"]:
            return True, f"Workspace: {response.get('team', 'Unknown')}", response.get("user_id", "")
        return False, "auth.test failed", ""
    except Exception as e:
        return False, f"Error: {e}", ""


def ingest() -> dict:
    """Fetch user's messages from all joined channels.
    Returns {"ingested": count}.
    """
    token = db.get_setting("slack_bot_token")
    user_id = db.get_setting("slack_user_id")

    if not token:
        return {"ingested": 0, "error": "Slack Bot Token not configured"}
    if not user_id:
        return {"ingested": 0, "error": "Slack User ID not set. Test connection first."}

    # Build dedup set
    existing = db.get_persona_samples(source_type="slack", limit=5000)
    existing_hashes = set()
    for s in existing:
        meta = json.loads(s.get("metadata", "{}"))
        if meta.get("content_hash"):
            existing_hashes.add(meta["content_hash"])

    ingested = 0

    try:
        from slack_sdk import WebClient

        client = WebClient(token=token)

        # Get all joined channels
        channels = []
        cursor = None
        for _ in range(10):  # Max 10 pages
            kwargs = {"types": "public_channel,private_channel", "limit": 200}
            if cursor:
                kwargs["cursor"] = cursor
            response = client.conversations_list(**kwargs)
            channels.extend(response.get("channels", []))
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        for channel in channels:
            channel_id = channel["id"]
            channel_name = channel.get("name", "unknown")

            try:
                response = client.conversations_history(
                    channel=channel_id, limit=200
                )
            except Exception:
                continue

            messages = response.get("messages", [])

            for msg in messages:
                # Filter to user's messages only
                if msg.get("user") != user_id:
                    continue
                # Skip bot messages and system messages
                if msg.get("subtype"):
                    continue

                text = msg.get("text", "")
                if not text or len(text) < 20:
                    continue

                content_hash = hashlib.md5(text.encode()).hexdigest()
                if content_hash in existing_hashes:
                    continue
                existing_hashes.add(content_hash)

                chunks = _chunk_text(text)
                for chunk in chunks:
                    if len(chunk) < 20:
                        continue
                    metadata = json.dumps({
                        "channel": channel_name,
                        "content_hash": content_hash,
                    })
                    db.save_persona_sample(chunk, source_type="slack", metadata=metadata)
                    ingested += 1

            # Rate limit: small delay between channels
            time.sleep(0.5)

    except Exception as e:
        return {"ingested": ingested, "error": str(e)}

    return {"ingested": ingested}
