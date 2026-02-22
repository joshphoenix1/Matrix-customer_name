"""
Email ingestion placeholder — manual input for V1, future: IMAP/webhook.
"""

import json
import db
from services.claude_client import process_email


def check_inbox():
    """
    Stub: In a real deployment, this would poll an IMAP inbox or
    receive webhooks from an email service (SendGrid, Mailgun, etc.).
    For V1, emails are manually entered via the dashboard form.
    """
    return []


def process_incoming_email(sender, subject, body):
    """
    Process an incoming email: AI triage, save to DB, optionally create tasks.
    Returns the processing result dict.
    """
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

    result["email_id"] = email_id
    return result
