"""
Google Calendar channel — parse .ics uploads, extract event titles/descriptions/notes
for persona training.
"""

import json
import hashlib
import db
from services.persona_engine import _chunk_text


def parse_ics(text: str) -> list:
    """Parse .ics content, extract text from events.
    Returns list of event text strings.
    """
    try:
        from icalendar import Calendar
    except ImportError:
        return []

    events = []

    try:
        cal = Calendar.from_ical(text)
    except Exception:
        return []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("SUMMARY", "")) if component.get("SUMMARY") else ""
        description = str(component.get("DESCRIPTION", "")) if component.get("DESCRIPTION") else ""
        location = str(component.get("LOCATION", "")) if component.get("LOCATION") else ""

        parts = []
        if summary:
            parts.append(f"Meeting: {summary}")
        if description:
            parts.append(description)
        if location:
            parts.append(f"Location: {location}")

        event_text = "\n".join(parts).strip()

        # Filter out trivial entries
        if len(event_text) < 20:
            continue

        events.append(event_text)

    return events


def ingest(text: str) -> dict:
    """Parse .ics, chunk event texts, save as source_type='calendar'.
    Returns {"ingested": count}.
    """
    events = parse_ics(text)
    if not events:
        return {"ingested": 0, "error": "No events found in the .ics file."}

    # Build dedup set
    existing = db.get_persona_samples(source_type="calendar", limit=5000)
    existing_hashes = set()
    for s in existing:
        meta = json.loads(s.get("metadata", "{}"))
        if meta.get("content_hash"):
            existing_hashes.add(meta["content_hash"])

    # Combine events and chunk
    combined = "\n\n---\n\n".join(events)
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
            "source": "calendar_ics",
            "content_hash": content_hash,
        })
        db.save_persona_sample(chunk, source_type="calendar", metadata=metadata)
        ingested += 1

    return {"ingested": ingested}
