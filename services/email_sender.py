"""
SMTP email sender — complement to existing IMAP reader.
Send emails, test connections, send approved drafts.
Enforces read-only mode.
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import db


def _get_smtp_config():
    """Get SMTP config from DB settings, falling back to IMAP creds."""
    server = db.get_setting("smtp_server") or db.get_setting("imap_server", "smtp.gmail.com")
    port = int(db.get_setting("smtp_port", "587"))
    email = db.get_setting("smtp_email") or db.get_setting("imap_email", "")
    password = db.get_setting("smtp_password") or db.get_setting("imap_password", "")

    # Gmail IMAP → SMTP server swap
    if server == "imap.gmail.com":
        server = "smtp.gmail.com"

    return {
        "server": server,
        "port": port,
        "email": email,
        "password": password,
    }


def test_smtp_connection(server, port, email, password):
    """Test SMTP connection. Returns (success: bool, message: str)."""
    try:
        port = int(port)
        with smtplib.SMTP(server, port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(email, password)
        return True, "SMTP connection successful."
    except Exception as e:
        return False, f"SMTP connection failed: {str(e)}"


def send_email(recipient, subject, body, draft_id=None, in_reply_to_email_id=None):
    """Send an email via SMTP. Returns (success: bool, message: str, smtp_message_id: str).
    Blocks sends when read-only mode is active.
    """
    # Check read-only mode
    if db.get_setting("read_only_mode", "false") == "true":
        return False, "Read-only mode is active. Outbound email is disabled.", ""

    config = _get_smtp_config()

    if not config["email"] or not config["password"]:
        return False, "SMTP credentials not configured.", ""

    msg = MIMEMultipart("alternative")
    msg["From"] = config["email"]
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(config["server"], config["port"], timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(config["email"], config["password"])
            smtp.send_message(msg)
            smtp_message_id = msg.get("Message-ID", "")

        db.save_sent_email(
            draft_id=draft_id,
            recipient=recipient,
            subject=subject,
            body=body,
            smtp_message_id=smtp_message_id,
            status="sent",
        )

        return True, "Email sent successfully.", smtp_message_id

    except Exception as e:
        return False, f"Send failed: {str(e)}", ""


def send_approved_draft(draft_id):
    """Fetch a draft, send it via SMTP, and update its status."""
    draft = db.get_email_draft(draft_id)
    if not draft:
        return False, "Draft not found."

    if draft["status"] not in ("pending_review", "auto_approved", "approved"):
        return False, f"Draft status is '{draft['status']}', cannot send."

    success, message, smtp_id = send_email(
        recipient=draft["recipient"],
        subject=draft["subject"],
        body=draft["body"],
        draft_id=draft_id,
        in_reply_to_email_id=draft.get("email_id"),
    )

    if success:
        db.update_email_draft(draft_id, status="sent")

        # Trigger calendar invite creation for meeting_scheduling drafts
        if draft.get("category") == "meeting_scheduling":
            meeting_json = db.get_setting(f"draft_{draft_id}_meeting_details")
            if meeting_json:
                try:
                    from services.calendar_sender import create_event_with_meet
                    details = json.loads(meeting_json)
                    create_event_with_meet(
                        recipient=draft["recipient"],
                        title=details.get("title", draft["subject"]),
                        start_iso=details["start"],
                        end_iso=details["end"],
                        description=draft.get("body", ""),
                        draft_id=draft_id,
                        timezone=details.get("timezone", "UTC"),
                    )
                except Exception as e:
                    print(f"Calendar invite creation failed for draft {draft_id}: {e}")

        return True, "Draft sent successfully."
    else:
        return False, message
