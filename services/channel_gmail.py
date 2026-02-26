"""
Gmail Sent Mail channel — IMAP fetch from [Gmail]/Sent Mail + Inbox,
stream user's messages for persona training.
"""

import json
import hashlib
import email
from imapclient import IMAPClient
import db
from services.email_ingestion import _extract_body, _decode_header_value
from services.persona_engine import _chunk_text


def test_connection() -> tuple:
    """Test IMAP connection using existing settings. Returns (bool, str)."""
    server = db.get_setting("imap_server")
    email_addr = db.get_setting("imap_email")
    password = db.get_setting("imap_password")

    if not server or not email_addr or not password:
        return False, "IMAP not configured. Set up credentials on the Setup page."

    try:
        with IMAPClient(server, ssl=True, port=993, timeout=10) as client:
            client.login(email_addr, password)
            client.logout()
        return True, f"Connected as {email_addr}"
    except Exception as e:
        return False, f"Connection failed: {e}"


def ingest() -> dict:
    """Fetch from [Gmail]/Sent Mail + INBOX (user's messages only).
    Returns {"ingested": count}.
    """
    server = db.get_setting("imap_server")
    email_addr = db.get_setting("imap_email")
    password = db.get_setting("imap_password")

    if not server or not email_addr or not password:
        return {"ingested": 0, "error": "IMAP not configured"}

    user_email_lower = email_addr.lower()

    # Build dedup set from existing samples
    existing = db.get_persona_samples(source_type="gmail_sent", limit=5000)
    existing_hashes = set()
    for s in existing:
        meta = json.loads(s.get("metadata", "{}"))
        if meta.get("content_hash"):
            existing_hashes.add(meta["content_hash"])

    ingested = 0

    try:
        with IMAPClient(server, ssl=True, port=993, timeout=60) as client:
            client.login(email_addr, password)

            # Fetch from Sent Mail
            for folder in ["[Gmail]/Sent Mail", "INBOX"]:
                try:
                    client.select_folder(folder, readonly=True)
                except Exception:
                    continue

                uids = client.search(["ALL"])
                if not uids:
                    continue

                # Last 200 messages
                uids = sorted(uids)[-200:]

                for i in range(0, len(uids), 10):
                    batch = uids[i:i + 10]
                    try:
                        raw_messages = client.fetch(batch, ["RFC822"])
                    except Exception:
                        continue

                    for uid, data in raw_messages.items():
                        raw_email = data[b"RFC822"]
                        msg = email.message_from_bytes(raw_email)

                        sender = _decode_header_value(msg.get("From", ""))
                        sender_lower = sender.lower()

                        # For INBOX, only keep messages FROM the user
                        if folder == "INBOX" and user_email_lower not in sender_lower:
                            continue

                        body = _extract_body(msg)
                        if not body or len(body) < 20:
                            continue

                        content_hash = hashlib.md5(body.encode()).hexdigest()
                        if content_hash in existing_hashes:
                            continue
                        existing_hashes.add(content_hash)

                        subject = _decode_header_value(msg.get("Subject", ""))

                        chunks = _chunk_text(body)
                        for chunk in chunks:
                            if len(chunk) < 20:
                                continue
                            metadata = json.dumps({
                                "subject": subject,
                                "folder": folder,
                                "content_hash": content_hash,
                            })
                            db.save_persona_sample(chunk, source_type="gmail_sent", metadata=metadata)
                            ingested += 1

    except Exception as e:
        return {"ingested": ingested, "error": str(e)}

    return {"ingested": ingested}
