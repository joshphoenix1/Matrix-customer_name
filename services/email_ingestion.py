"""
Email ingestion — IMAP inbox scanning with AI triage.
"""

import json
import email
import re
from email.header import decode_header
from imapclient import IMAPClient
import db
from services.claude_client import process_email


def _decode_header_value(value):
    """Decode an email header value that may be encoded."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _strip_html(html_text):
    """Basic HTML tag stripping for email body fallback."""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_body(msg):
    """Extract plain text body from an email message, with HTML fallback."""
    plain_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
            except Exception:
                continue

            if content_type == "text/plain" and not plain_body:
                plain_body = text
            elif content_type == "text/html" and not html_body:
                html_body = text
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_body = text
                else:
                    plain_body = text
        except Exception:
            pass

    if plain_body:
        return plain_body.strip()
    if html_body:
        return _strip_html(html_body)
    return ""


def test_imap_connection(server, email_addr, password):
    """
    Test IMAP connection with provided credentials.
    Returns (success: bool, message: str).
    """
    try:
        with IMAPClient(server, ssl=True, port=993, timeout=10) as client:
            client.login(email_addr, password)
            client.logout()
        return True, "Connection successful."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def check_inbox():
    """
    Connect to IMAP inbox, fetch ALL recent emails (seen or unseen).
    Deduplicates against already-processed emails in the DB by subject+sender.
    Returns list of {sender, subject, body} dicts for emails not yet processed.
    """
    server = db.get_setting("imap_server")
    email_addr = db.get_setting("imap_email")
    password = db.get_setting("imap_password")

    if not server or not email_addr or not password:
        return []

    # Build set of already-processed emails for dedup
    existing_emails = db.get_emails(limit=200)
    processed_keys = {(e["sender"], e["subject"]) for e in existing_emails}

    try:
        with IMAPClient(server, ssl=True, port=993, timeout=30) as client:
            client.login(email_addr, password)
            client.select_folder("INBOX")

            uids = client.search(["ALL"])
            if not uids:
                return []

            results = []
            raw_messages = client.fetch(uids, ["RFC822"])

            for uid, data in raw_messages.items():
                raw_email = data[b"RFC822"]
                msg = email.message_from_bytes(raw_email)

                sender = _decode_header_value(msg.get("From", ""))
                subject = _decode_header_value(msg.get("Subject", "(No Subject)"))

                # Skip if already processed
                if (sender, subject) in processed_keys:
                    continue

                body = _extract_body(msg)

                # Truncate very long bodies for AI processing
                if len(body) > 10000:
                    body = body[:10000] + "\n\n[... truncated ...]"

                results.append({
                    "sender": sender,
                    "subject": subject,
                    "body": body,
                })

            return results

    except Exception as e:
        print(f"IMAP check_inbox error: {e}")
        return []


def process_incoming_email(sender, subject, body):
    """
    Process an incoming email: AI triage, save to DB, optionally create tasks
    and meetings.
    Returns the processing result dict.
    """
    from datetime import date as _date

    # AI processing
    result = process_email(sender, subject, body)

    # Save to database
    action_items_json = json.dumps(result.get("action_items", []))
    email_id = db.save_email(
        sender=sender,
        subject=subject,
        body=body,
        processed_summary=result.get("summary", ""),
        urgency=result.get("urgency", "routine"),
        action_items=action_items_json,
    )

    # Auto-create task if recommended
    if result.get("should_create_task") and result.get("suggested_task_title"):
        priority_map = {"critical": "critical", "important": "high", "routine": "medium", "fyi": "low"}
        priority = priority_map.get(result.get("urgency", "routine"), "medium")
        task_id = db.create_task(
            title=result["suggested_task_title"],
            description=f"Auto-created from email: {subject}\n\n{result.get('summary', '')}",
            priority=priority,
        )
        result["created_task_id"] = task_id

    # Auto-create meeting if this is a meeting request
    if result.get("is_meeting_request") and result.get("meeting_title"):
        meeting_date = result.get("meeting_date") or _date.today().isoformat()
        meeting_id = db.save_meeting(
            title=result["meeting_title"],
            meeting_date=meeting_date,
            raw_notes=f"Meeting request from: {sender}\n\n{result.get('summary', '')}",
        )
        result["created_meeting_id"] = meeting_id

    result["email_id"] = email_id
    return result


# Automated / robot senders to skip during ingestion
_IGNORED_SENDER_PATTERNS = [
    "no-reply@",
    "noreply@",
    "mailer-daemon@",
    "postmaster@",
    "notifications@",
    "notify@",
    "accounts.google.com",
    "googlemail.com",
]


def _is_robot_sender(sender):
    """Return True if the sender looks like an automated/robot address."""
    sender_lower = sender.lower()
    return any(pat in sender_lower for pat in _IGNORED_SENDER_PATTERNS)


def scan_and_process_inbox():
    """
    Fetch new emails from IMAP and process each through AI pipeline.
    Skips automated/robot senders.
    Returns summary dict: {fetched, processed, tasks_created, errors, skipped, results}.
    """
    emails = check_inbox()
    # Filter out robot / automated senders
    human_emails = [em for em in emails if not _is_robot_sender(em["sender"])]
    skipped = len(emails) - len(human_emails)
    emails = human_emails
    fetched = len(emails)
    tasks_created = 0
    meetings_created = 0
    errors = 0
    results = []

    for em in emails:
        try:
            result = process_incoming_email(em["sender"], em["subject"], em["body"])
            if result.get("created_task_id"):
                tasks_created += 1
            if result.get("created_meeting_id"):
                meetings_created += 1
            results.append(result)
        except Exception as e:
            print(f"Error processing email '{em.get('subject', '?')}': {e}")
            errors += 1

    return {
        "fetched": fetched,
        "processed": fetched - errors,
        "tasks_created": tasks_created,
        "meetings_created": meetings_created,
        "errors": errors,
        "skipped": skipped,
        "results": results,
    }
