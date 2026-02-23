"""
Anthropic API wrapper — system prompt loader, conversation management,
meeting summarization, email processing, daily priorities.
"""

import json
import os
from datetime import date
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, PROMPTS_DIR, COMPANY_NAME
import db


def _load_prompt(filename):
    path = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""


def _build_system_prompt():
    """Build system prompt with dynamic context injected."""
    base_prompt = _load_prompt("system_prompt.md")
    today = date.today().isoformat()
    task_summary = db.get_active_tasks_summary()
    meeting_summary = db.get_meetings_summary()
    email_summary = db.get_recent_emails_summary()

    context_block = f"""## Current Context (Auto-injected)
- Date: {today}
- Company: {COMPANY_NAME}
- Active Tasks:
{task_summary}
- Today's Meetings:
{meeting_summary}
- Recent Emails:
{email_summary}

---

"""
    return context_block + base_prompt


def _get_client():
    if not ANTHROPIC_API_KEY:
        return None
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def chat(user_message, conversation_id):
    """
    Send a message in a conversation, get Claude's response.
    Saves both user and assistant messages to DB.
    Returns the assistant's response text.
    """
    db.save_message(conversation_id, "user", user_message)

    client = _get_client()
    if not client:
        fallback = "I'm unable to respond right now — the ANTHROPIC_API_KEY is not configured. Please add it to your .env file."
        db.save_message(conversation_id, "assistant", fallback)
        return fallback

    # Build message history
    history = db.get_messages(conversation_id)
    messages = []
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    system_prompt = _build_system_prompt()

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )
        assistant_text = response.content[0].text
    except Exception as e:
        assistant_text = f"Error communicating with Claude: {str(e)}"

    db.save_message(conversation_id, "assistant", assistant_text)

    # Auto-title the conversation from the first exchange
    conv = db.get_conversation(conversation_id)
    if conv and conv["title"] == "New Conversation" and len(messages) <= 2:
        title = user_message[:60] + ("..." if len(user_message) > 60 else "")
        db.update_conversation_title(conversation_id, title)

    return assistant_text


def summarize_meeting(raw_notes):
    """
    Summarize meeting notes and extract action items.
    Returns dict: {summary, action_items: [{description, owner, due_date}]}
    """
    client = _get_client()
    if not client:
        return {"summary": "API key not configured.", "action_items": []}

    prompt = f"""Analyze these meeting notes and provide:
1. An executive summary (3-5 sentences)
2. Key decisions made
3. Action items with owners and due dates where mentioned

Meeting notes:
{raw_notes}

Respond with valid JSON only, no markdown fencing:
{{
  "summary": "Executive summary here",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [
    {{"description": "Action item", "owner": "Person name or empty string", "due_date": "YYYY-MM-DD or null"}}
  ]
}}"""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Try to parse JSON, handle potential markdown fencing
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        return {
            "summary": f"Could not parse AI response: {str(e)}",
            "key_decisions": [],
            "action_items": [],
        }


def process_email(sender, subject, body):
    """
    Triage and summarize an email.
    Returns dict: {urgency, summary, action_items, should_create_task, suggested_task_title}
    """
    client = _get_client()
    if not client:
        return {
            "urgency": "routine",
            "summary": "API key not configured.",
            "action_items": [],
            "should_create_task": False,
            "suggested_task_title": None,
        }

    email_prompt = _load_prompt("email_processing_prompt.md")

    prompt = f"""{email_prompt}

## Email to Process

**From:** {sender}
**Subject:** {subject}
**Body:**
{body}"""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except (json.JSONDecodeError, Exception):
        return {
            "urgency": "routine",
            "summary": "Could not process email.",
            "action_items": [],
            "should_create_task": False,
            "suggested_task_title": None,
        }


def analyze_document(filename, content):
    """
    Analyze a document and extract key insights.
    Returns dict: {summary, key_insights, entities, action_items}
    """
    client = _get_client()
    if not client:
        return {
            "summary": "API key not configured.",
            "key_insights": [],
            "entities": [],
            "action_items": [],
        }

    # Truncate to 50K characters
    truncated = content[:50000]
    if len(content) > 50000:
        truncated += "\n\n[... content truncated at 50,000 characters ...]"

    prompt = f"""Analyze this document and provide a structured analysis.

**Filename:** {filename}

**Content:**
{truncated}

Respond with valid JSON only, no markdown fencing:
{{
  "summary": "2-4 sentence executive summary of the document",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "entities": ["Person, company, product, or concept mentioned"],
  "action_items": ["Any action items or next steps implied by the document"]
}}"""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        return {
            "summary": f"Could not analyze document: {str(e)}",
            "key_insights": [],
            "entities": [],
            "action_items": [],
        }


def generate_daily_priorities(tasks, meetings, emails):
    """
    Generate a morning briefing / daily priorities list.
    Returns the briefing as a string.
    """
    client = _get_client()
    if not client:
        return "API key not configured. Add ANTHROPIC_API_KEY to your .env file to enable daily priorities."

    today = date.today().isoformat()
    task_text = ""
    for t in tasks:
        due = f" (due {t['due_date']})" if t.get("due_date") else ""
        task_text += f"- [{t['priority'].upper()}] {t['title']}{due} — {t['status']}\n"

    meeting_text = ""
    for m in meetings:
        meeting_text += f"- {m['title']} ({m['date']})\n"

    email_text = ""
    for e in emails:
        email_text += f"- [{e.get('urgency', 'routine').upper()}] From {e['sender']}: {e['subject']}\n"

    prompt = f"""You are the Matrix AI Assistant for {COMPANY_NAME}. Generate a concise daily priorities briefing for today ({today}).

Active Tasks:
{task_text or "None"}

Today's Meetings:
{meeting_text or "None"}

Recent Emails:
{email_text or "None"}

Provide:
1. A time-aware greeting (morning/afternoon/evening)
2. Top 3-5 priorities for today with brief reasoning
3. Any warnings (overdue tasks, critical emails, scheduling conflicts)

Keep it concise and actionable. Use markdown formatting."""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"Could not generate daily priorities: {str(e)}"


def generate_executive_plan(tasks, meetings, emails, overdue_tasks):
    """
    Generate a structured daily executive plan with time blocks and strategic focus.
    Returns the plan as a markdown string.
    """
    client = _get_client()
    if not client:
        return "API key not configured."

    today = date.today().isoformat()
    from datetime import datetime as _dt
    current_time = _dt.now().strftime("%H:%M")

    task_text = ""
    for t in tasks:
        due = f" (due {t['due_date']})" if t.get("due_date") else ""
        task_text += f"- [{t['priority'].upper()}] {t['title']}{due} — {t['status']}\n"

    overdue_text = ""
    for t in overdue_tasks:
        overdue_text += f"- [{t['priority'].upper()}] {t['title']} (was due {t['due_date']})\n"

    meeting_text = ""
    for m in meetings:
        notes_preview = ""
        if m.get("raw_notes"):
            notes_preview = f" — Notes: {m['raw_notes'][:80]}..."
        meeting_text += f"- {m['title']} ({m['date']}){notes_preview}\n"

    email_text = ""
    for e in emails:
        summary = e.get("processed_summary", "")[:80]
        email_text += f"- [{e.get('urgency', 'routine').upper()}] {e['subject']} — {summary}\n"

    prompt = f"""You are a world-class executive chief of staff for {COMPANY_NAME}. Create a structured Daily Executive Plan for today ({today}, current time: {current_time}).

## Context

Active Tasks ({len(tasks)}):
{task_text or "None"}

Overdue Tasks ({len(overdue_tasks)}):
{overdue_text or "None"}

Today's Meetings:
{meeting_text or "None"}

Recent Emails (unresolved):
{email_text or "None"}

## Instructions

Build a concrete, time-blocked executive plan. Structure it as:

### Morning Block (before 12:00)
- List specific actions with estimated durations
- Prioritize critical/overdue items first

### Afternoon Block (12:00–17:00)
- Strategic work, meetings, follow-ups

### End of Day (17:00+)
- Review, prep for tomorrow, delegation notes

### Key Decisions Needed Today
- List 2-3 decisions the executive should make today based on current context

### Risk Watch
- Flag anything that could derail the day (overdue deadlines, unanswered critical emails, scheduling conflicts)

Be specific — reference actual task names, meeting titles, and email subjects. No generic advice. Use markdown formatting with bold for emphasis. Keep it actionable and tight."""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"Could not generate executive plan: {str(e)}"
