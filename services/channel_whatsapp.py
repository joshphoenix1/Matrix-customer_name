"""
WhatsApp channel — parse WhatsApp .txt export files,
filter to user's messages for persona training.
"""

import re
import json
import hashlib
import db
from services.persona_engine import _chunk_text

# Common WhatsApp export line patterns
_PATTERNS = [
    # [MM/DD/YY, HH:MM:SS] Name: message
    re.compile(r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+\d{1,2}:\d{2}(?::\d{2})?\s*[APap]?[Mm]?\]\s+(.+?):\s+(.+)$"),
    # MM/DD/YY, HH:MM - Name: message
    re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+\d{1,2}:\d{2}\s*[APap]?[Mm]?\s*-\s+(.+?):\s+(.+)$"),
]


def parse_export(text: str, user_name: str) -> list:
    """Parse WhatsApp export text, return list of messages from user_name.
    Filters to messages where Name matches user_name (case-insensitive partial match).
    """
    if not text or not user_name:
        return []

    user_lower = user_name.strip().lower()
    messages = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        for pattern in _PATTERNS:
            match = pattern.match(line)
            if match:
                name = match.group(2).strip()
                message = match.group(3).strip()

                # Case-insensitive partial match on user name
                if user_lower in name.lower():
                    # Skip system messages
                    if message in ("<Media omitted>", "This message was deleted",
                                   "You deleted this message"):
                        continue
                    messages.append(message)
                break

    return messages


def ingest(text: str) -> dict:
    """Parse export, chunk user's messages, save as source_type='whatsapp'.
    Gets user_name from db.get_setting('user_name').
    Returns {"ingested": count}.
    """
    user_name = db.get_setting("user_name", "")
    if not user_name:
        # Fallback: try the imap email username part
        email_addr = db.get_setting("imap_email", "")
        if email_addr and "@" in email_addr:
            user_name = email_addr.split("@")[0]
        if not user_name:
            return {"ingested": 0, "error": "Set your name in Settings (user_name) so we can filter your messages."}

    messages = parse_export(text, user_name)
    if not messages:
        return {"ingested": 0, "error": f"No messages found from '{user_name}'. Check the export format and your name."}

    # Build dedup set
    existing = db.get_persona_samples(source_type="whatsapp", limit=5000)
    existing_hashes = set()
    for s in existing:
        meta = json.loads(s.get("metadata", "{}"))
        if meta.get("content_hash"):
            existing_hashes.add(meta["content_hash"])

    # Combine short messages into larger chunks for better training
    combined = "\n\n".join(messages)
    chunks = _chunk_text(combined, max_chars=500)

    ingested = 0
    for chunk in chunks:
        if len(chunk) < 20:
            continue

        content_hash = hashlib.md5(chunk.encode()).hexdigest()
        if content_hash in existing_hashes:
            continue
        existing_hashes.add(content_hash)

        metadata = json.dumps({
            "source": "whatsapp_export",
            "content_hash": content_hash,
        })
        db.save_persona_sample(chunk, source_type="whatsapp", metadata=metadata)
        ingested += 1

    return {"ingested": ingested}
