"""
Telegram channel — Telethon client with interactive auth (phone→code),
fetch user's messages from all dialogs for persona training.
"""

import os
import json
import hashlib
import asyncio
import db
from services.persona_engine import _chunk_text
from config import BASE_DIR

SESSION_PATH = os.path.join(BASE_DIR, "data", "telegram")

# Module-level pending client for two-step auth
_pending_client = None


def _get_event_loop():
    """Get or create an event loop for sync wrappers."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def test_connection() -> tuple:
    """Check if Telethon can connect with stored credentials. Returns (bool, str)."""
    api_id = db.get_setting("telegram_api_id")
    api_hash = db.get_setting("telegram_api_hash")

    if not api_id or not api_hash:
        return False, "Telegram API credentials not configured."

    # Check if session file exists (auth completed)
    if not os.path.exists(SESSION_PATH + ".session"):
        return False, "Not authenticated. Complete the auth flow first."

    try:
        from telethon import TelegramClient

        loop = _get_event_loop()

        async def _test():
            client = TelegramClient(SESSION_PATH, int(api_id), api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                return False, "Session expired. Re-authenticate."
            me = await client.get_me()
            await client.disconnect()
            name = me.first_name or ""
            if me.last_name:
                name += f" {me.last_name}"
            return True, f"Connected as {name} ({me.phone})"

        return loop.run_until_complete(_test())
    except Exception as e:
        return False, f"Connection error: {e}"


def start_auth(phone: str) -> tuple:
    """Send auth code to phone. Returns (success, message)."""
    global _pending_client

    api_id = db.get_setting("telegram_api_id")
    api_hash = db.get_setting("telegram_api_hash")

    if not api_id or not api_hash:
        return False, "Set API ID and API Hash first."

    try:
        from telethon import TelegramClient

        loop = _get_event_loop()

        async def _start():
            global _pending_client
            client = TelegramClient(SESSION_PATH, int(api_id), api_hash)
            await client.connect()
            result = await client.send_code_request(phone)
            _pending_client = client
            return True, f"Code sent to {phone}. Enter it below."

        return loop.run_until_complete(_start())
    except Exception as e:
        return False, f"Failed to send code: {e}"


def complete_auth(code: str) -> tuple:
    """Complete auth with the code user received. Returns (success, message)."""
    global _pending_client

    if _pending_client is None:
        return False, "No pending auth. Click 'Send Code' first."

    phone = db.get_setting("telegram_phone", "")

    try:
        loop = _get_event_loop()

        async def _complete():
            global _pending_client
            await _pending_client.sign_in(phone, code)
            me = await _pending_client.get_me()
            await _pending_client.disconnect()
            _pending_client = None
            name = me.first_name or ""
            if me.last_name:
                name += f" {me.last_name}"
            return True, f"Authenticated as {name}."

        return loop.run_until_complete(_complete())
    except Exception as e:
        return False, f"Auth failed: {e}"


def ingest() -> dict:
    """Fetch user's messages from all dialogs.
    Returns {"ingested": count}.
    """
    api_id = db.get_setting("telegram_api_id")
    api_hash = db.get_setting("telegram_api_hash")

    if not api_id or not api_hash:
        return {"ingested": 0, "error": "Telegram not configured"}

    if not os.path.exists(SESSION_PATH + ".session"):
        return {"ingested": 0, "error": "Not authenticated"}

    # Build dedup set
    existing = db.get_persona_samples(source_type="telegram", limit=5000)
    existing_hashes = set()
    for s in existing:
        meta = json.loads(s.get("metadata", "{}"))
        if meta.get("content_hash"):
            existing_hashes.add(meta["content_hash"])

    ingested = 0

    try:
        from telethon import TelegramClient

        loop = _get_event_loop()

        async def _ingest():
            nonlocal ingested
            client = TelegramClient(SESSION_PATH, int(api_id), api_hash)
            await client.connect()

            if not await client.is_user_authorized():
                await client.disconnect()
                return {"ingested": 0, "error": "Session expired"}

            me = await client.get_me()
            my_id = me.id

            dialog_count = 0
            async for dialog in client.iter_dialogs():
                if dialog_count >= 50:
                    break
                dialog_count += 1

                try:
                    msg_count = 0
                    async for message in client.iter_messages(dialog.entity, limit=200):
                        if msg_count >= 200:
                            break
                        msg_count += 1

                        # Only user's own messages
                        if not message.sender_id or message.sender_id != my_id:
                            continue

                        # Skip media-only (no text)
                        text = message.text or ""
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
                                "dialog": dialog.name or "Unknown",
                                "content_hash": content_hash,
                            })
                            db.save_persona_sample(chunk, source_type="telegram", metadata=metadata)
                            ingested += 1
                except Exception:
                    continue

            await client.disconnect()

        loop.run_until_complete(_ingest())
    except Exception as e:
        return {"ingested": ingested, "error": str(e)}

    return {"ingested": ingested}
