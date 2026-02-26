"""
Google Calendar API client — create events with Google Meet links
using a service account with domain-wide delegation.
"""

import json
import uuid
import db


def _get_calendar_service():
    """Build Google Calendar API service from service account key stored in settings."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    key_json = db.get_setting("google_service_account_key")
    if not key_json:
        return None

    key_data = json.loads(key_json)
    user_email = db.get_setting("imap_email")
    if not user_email:
        return None

    creds = service_account.Credentials.from_service_account_info(
        key_data,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    creds = creds.with_subject(user_email)

    return build("calendar", "v3", credentials=creds)


def create_event_with_meet(recipient, title, start_iso, end_iso,
                           description="", draft_id=None, timezone="UTC"):
    """Create a Google Calendar event with Google Meet link.

    Args:
        recipient: Attendee email address.
        title: Event summary/title.
        start_iso: Start datetime in ISO 8601 format.
        end_iso: End datetime in ISO 8601 format.
        description: Optional event description.
        draft_id: Optional email draft ID for linking.
        timezone: IANA timezone string (default UTC).

    Returns:
        (success: bool, meet_link: str, event_id: str)
    """
    service = _get_calendar_service()
    if not service:
        return False, "", ""

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": timezone},
        "end": {"dateTime": end_iso, "timeZone": timezone},
        "attendees": [{"email": recipient}],
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",
        ).execute()

        event_id = event.get("id", "")
        meet_link = ""
        conf_data = event.get("conferenceData", {})
        for ep in conf_data.get("entryPoints", []):
            if ep.get("entryPointType") == "video":
                meet_link = ep.get("uri", "")
                break

        # Save to calendar_invites table
        db.save_calendar_invite(
            draft_id=draft_id,
            recipient=recipient,
            title=title,
            start_time=start_iso,
            end_time=end_iso,
            google_event_id=event_id,
            meet_link=meet_link,
            status="created",
        )

        return True, meet_link, event_id

    except Exception as e:
        print(f"Google Calendar API error: {e}")
        # Save failed attempt
        db.save_calendar_invite(
            draft_id=draft_id,
            recipient=recipient,
            title=title,
            start_time=start_iso,
            end_time=end_iso,
            status=f"error: {str(e)[:200]}",
        )
        return False, "", ""
