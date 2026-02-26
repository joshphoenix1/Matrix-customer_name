"""
SQLite database layer — schema, init, and helper functions.
"""

import sqlite3
import json
from datetime import datetime, date
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    raw_notes TEXT DEFAULT '',
    ai_summary TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS meeting_action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    task_id INTEGER,
    description TEXT NOT NULL,
    owner TEXT DEFAULT '',
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    processed_summary TEXT DEFAULT '',
    urgency TEXT DEFAULT 'routine',
    action_items TEXT DEFAULT '[]',
    received_at TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    ai_analysis TEXT DEFAULT '',
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    company TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'prospect')),
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    value REAL NOT NULL DEFAULT 0,
    stage TEXT NOT NULL DEFAULT 'prospect' CHECK (stage IN ('prospect', 'proposal', 'negotiation', 'won', 'lost')),
    expected_close TEXT,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    closed_at TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client TEXT NOT NULL,
    description TEXT DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    paid_at TEXT
);

CREATE TABLE IF NOT EXISTS revenue_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    entry_type TEXT NOT NULL DEFAULT 'one-time' CHECK (entry_type IN ('recurring', 'one-time')),
    period TEXT DEFAULT '',
    entry_date TEXT NOT NULL DEFAULT (date('now')),
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS persona_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL DEFAULT 'email',
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    embedded_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS email_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'auto_approved', 'approved', 'sent', 'rejected')),
    confidence_score REAL DEFAULT 0.0,
    category TEXT DEFAULT '',
    reasoning TEXT DEFAULT '',
    original_body TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sent_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    smtp_message_id TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'sent',
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (draft_id) REFERENCES email_drafts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS exclusion_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL UNIQUE,
    reason TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS calendar_invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER,
    google_event_id TEXT DEFAULT '',
    recipient TEXT NOT NULL,
    title TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    meet_link TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (draft_id) REFERENCES email_drafts(id) ON DELETE SET NULL
);
"""


def init_db():
    """Initialize the database schema."""
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Conversations ──

def create_conversation(title="New Conversation"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO conversations (title) VALUES (?)", (title,)
        )
        return cur.lastrowid


def get_conversations():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_conversation(conversation_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        return dict(row) if row else None


def update_conversation_title(conversation_id, title):
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conversation_id),
        )


# ── Messages ──

def save_message(conversation_id, role, content):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
        )


def get_messages(conversation_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Tasks ──

def create_task(title, description="", priority="medium", due_date=None):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
            (title, description, priority, due_date),
        )
        return cur.lastrowid


def get_tasks(status=None, priority=None):
    with get_db() as conn:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_tasks_due_today():
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE due_date = ? AND status NOT IN ('completed', 'cancelled')",
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_overdue_tasks():
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE due_date < ? AND status NOT IN ('completed', 'cancelled') AND due_date IS NOT NULL AND due_date != ''",
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_task(task_id, **kwargs):
    with get_db() as conn:
        allowed = {"title", "description", "priority", "status", "due_date"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "status" in updates and updates["status"] == "completed":
            updates["completed_at"] = datetime.now().isoformat()
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)


def delete_task(task_id):
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def get_active_tasks_summary():
    """Short summary string for injecting into AI context."""
    tasks = get_tasks()
    active = [t for t in tasks if t["status"] not in ("completed", "cancelled")]
    if not active:
        return "No active tasks."
    lines = []
    for t in active[:10]:
        due = f" (due {t['due_date']})" if t.get("due_date") else ""
        lines.append(f"- [{t['priority'].upper()}] {t['title']}{due} — {t['status']}")
    if len(active) > 10:
        lines.append(f"  ...and {len(active) - 10} more")
    return "\n".join(lines)


# ── Meetings ──

def save_meeting(title, meeting_date, raw_notes="", ai_summary=""):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO meetings (title, date, raw_notes, ai_summary) VALUES (?, ?, ?, ?)",
            (title, meeting_date, raw_notes, ai_summary),
        )
        return cur.lastrowid


def get_meetings():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM meetings ORDER BY date DESC, created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_meeting(meeting_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        return dict(row) if row else None


def update_meeting_summary(meeting_id, ai_summary):
    with get_db() as conn:
        conn.execute(
            "UPDATE meetings SET ai_summary = ? WHERE id = ?",
            (ai_summary, meeting_id),
        )


def get_todays_meetings():
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM meetings WHERE date = ? ORDER BY created_at ASC",
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_meetings_summary():
    """Short summary for AI context."""
    meetings = get_todays_meetings()
    if not meetings:
        return "No meetings scheduled today."
    lines = [f"- {m['title']} ({m['date']})" for m in meetings]
    return "\n".join(lines)


# ── Meeting Action Items ──

def save_action_item(meeting_id, description, owner="", due_date=None, task_id=None):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO meeting_action_items (meeting_id, task_id, description, owner, due_date) VALUES (?, ?, ?, ?, ?)",
            (meeting_id, task_id, description, owner, due_date),
        )
        return cur.lastrowid


def get_action_items(meeting_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM meeting_action_items WHERE meeting_id = ? ORDER BY id ASC",
            (meeting_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Emails ──

def save_email(sender, subject, body, processed_summary="", urgency="routine", action_items="[]"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO emails (sender, subject, body, processed_summary, urgency, action_items, processed_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            (sender, subject, body, processed_summary, urgency, action_items),
        )
        return cur.lastrowid


def get_emails(limit=20):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM emails ORDER BY received_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_recent_emails_summary():
    """Short summary for AI context."""
    emails = get_emails(5)
    if not emails:
        return "No recent emails."
    lines = []
    for e in emails:
        lines.append(f"- [{e['urgency'].upper()}] From {e['sender']}: {e['subject']}")
    return "\n".join(lines)


# ── Documents ──

def save_document(filename, filepath, file_type, file_size=0):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO documents (filename, filepath, file_type, file_size) VALUES (?, ?, ?, ?)",
            (filename, filepath, file_type, file_size),
        )
        return cur.lastrowid


def get_documents():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_document(doc_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        return dict(row) if row else None


def update_document_analysis(doc_id, ai_analysis):
    with get_db() as conn:
        conn.execute(
            "UPDATE documents SET ai_analysis = ? WHERE id = ?",
            (ai_analysis, doc_id),
        )


# ── Settings ──

def save_setting(key, value):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, value),
        )


def get_setting(key, default=None):
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return dict(row)["value"] if row else default


# ── Auth Credentials ──

def save_auth_credentials(username, password):
    """Save hashed login credentials to the settings table."""
    save_setting("auth_username", username)
    save_setting("auth_password_hash", generate_password_hash(password))


def verify_auth_credentials(username, password):
    """Check username/password against stored credentials. Returns True if valid."""
    stored_user = get_setting("auth_username")
    stored_hash = get_setting("auth_password_hash")
    if not stored_user or not stored_hash:
        return None  # No DB credentials configured
    if username != stored_user:
        return False
    return check_password_hash(stored_hash, password)


# ── Invoices ──

def create_invoice(client, amount, due_date=None, description="", status="pending"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO invoices (client, amount, due_date, description, status) VALUES (?, ?, ?, ?, ?)",
            (client, amount, due_date, description, status),
        )
        return cur.lastrowid


def get_invoices(status=None):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM invoices WHERE status = ? ORDER BY due_date ASC, created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM invoices ORDER BY CASE status WHEN 'overdue' THEN 0 WHEN 'pending' THEN 1 WHEN 'paid' THEN 2 END, due_date ASC"
            ).fetchall()
        return [dict(r) for r in rows]


def update_invoice(invoice_id, **kwargs):
    with get_db() as conn:
        allowed = {"client", "amount", "due_date", "description", "status"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "status" in updates and updates["status"] == "paid":
            updates["paid_at"] = datetime.now().isoformat()
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [invoice_id]
        conn.execute(f"UPDATE invoices SET {set_clause} WHERE id = ?", values)


def delete_invoice(invoice_id):
    with get_db() as conn:
        conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))


def get_invoices_summary():
    invoices = get_invoices()
    outstanding = [i for i in invoices if i["status"] != "paid"]
    total = sum(i["amount"] for i in outstanding)
    overdue = sum(i["amount"] for i in outstanding if i["status"] == "overdue")
    return {"total_outstanding": total, "total_overdue": overdue, "count": len(outstanding)}


# ── Revenue Entries ──

def create_revenue_entry(source, amount, entry_type="one-time", period="", entry_date=None, notes=""):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO revenue_entries (source, amount, entry_type, period, entry_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (source, amount, entry_type, period, entry_date or date.today().isoformat(), notes),
        )
        return cur.lastrowid


def get_revenue_entries(limit=50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM revenue_entries ORDER BY entry_date DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_revenue_entry(entry_id):
    with get_db() as conn:
        conn.execute("DELETE FROM revenue_entries WHERE id = ?", (entry_id,))


def get_revenue_summary():
    entries = get_revenue_entries(limit=1000)
    total = sum(e["amount"] for e in entries)
    recurring = [e for e in entries if e["entry_type"] == "recurring"]
    mrr = sum(e["amount"] for e in recurring)
    return {"total_revenue": total, "mrr": mrr, "entry_count": len(entries)}


# ── Clients ──

def create_client(name, email="", phone="", company="", status="active", notes=""):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO clients (name, email, phone, company, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, phone, company, status, notes),
        )
        return cur.lastrowid


def get_clients(status=None):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM clients WHERE status = ? ORDER BY name", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM clients ORDER BY name"
            ).fetchall()
        return [dict(r) for r in rows]


def get_client(client_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        ).fetchone()
        return dict(row) if row else None


def update_client(client_id, **kwargs):
    with get_db() as conn:
        allowed = {"name", "email", "phone", "company", "status", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [client_id]
        conn.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", values)


def delete_client(client_id):
    with get_db() as conn:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))


# ── Deals ──

def create_deal(client_id, title, value=0, stage="prospect", expected_close=None, notes=""):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO deals (client_id, title, value, stage, expected_close, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (client_id, title, value, stage, expected_close, notes),
        )
        return cur.lastrowid


def get_deals(stage=None):
    with get_db() as conn:
        query = """
            SELECT d.*, c.name AS client_name
            FROM deals d
            JOIN clients c ON d.client_id = c.id
            WHERE 1=1
        """
        params = []
        if stage:
            query += " AND d.stage = ?"
            params.append(stage)
        query += """
            ORDER BY
                CASE d.stage
                    WHEN 'prospect' THEN 0
                    WHEN 'proposal' THEN 1
                    WHEN 'negotiation' THEN 2
                    WHEN 'won' THEN 3
                    WHEN 'lost' THEN 4
                END,
                d.value DESC
        """
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_deal(deal_id):
    with get_db() as conn:
        row = conn.execute(
            """SELECT d.*, c.name AS client_name
               FROM deals d JOIN clients c ON d.client_id = c.id
               WHERE d.id = ?""",
            (deal_id,),
        ).fetchone()
        return dict(row) if row else None


def update_deal(deal_id, **kwargs):
    with get_db() as conn:
        allowed = {"title", "value", "stage", "expected_close", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "stage" in updates and updates["stage"] in ("won", "lost"):
            updates["closed_at"] = datetime.now().isoformat()
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [deal_id]
        conn.execute(f"UPDATE deals SET {set_clause} WHERE id = ?", values)


def delete_deal(deal_id):
    with get_db() as conn:
        conn.execute("DELETE FROM deals WHERE id = ?", (deal_id,))


def get_crm_summary():
    with get_db() as conn:
        total_clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active_deals = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE stage NOT IN ('won', 'lost')"
        ).fetchone()[0]
        pipeline_value = conn.execute(
            "SELECT COALESCE(SUM(value), 0) FROM deals WHERE stage NOT IN ('won', 'lost')"
        ).fetchone()[0]
        won_value = conn.execute(
            "SELECT COALESCE(SUM(value), 0) FROM deals WHERE stage = 'won'"
        ).fetchone()[0]
        return {
            "total_clients": total_clients,
            "active_deals": active_deals,
            "pipeline_value": pipeline_value,
            "won_value": won_value,
        }


# ── Calendar Helpers ──

def get_meetings_for_month(year, month):
    prefix = f"{year}-{month:02d}"
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM meetings WHERE date LIKE ? ORDER BY date ASC, created_at ASC",
            (f"{prefix}%",),
        ).fetchall()
        return [dict(r) for r in rows]


def get_meetings_for_date(date_str):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM meetings WHERE date = ? ORDER BY created_at ASC",
            (date_str,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Persona Samples ──

def save_persona_sample(content, source_type="email", metadata="{}"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO persona_samples (content, source_type, metadata) VALUES (?, ?, ?)",
            (content, source_type, metadata),
        )
        return cur.lastrowid


def get_persona_samples(source_type=None, limit=500):
    with get_db() as conn:
        if source_type:
            rows = conn.execute(
                "SELECT * FROM persona_samples WHERE source_type = ? ORDER BY created_at DESC LIMIT ?",
                (source_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM persona_samples ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_persona_sample_count():
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM persona_samples").fetchone()[0]


def get_persona_sample_count_by_source():
    """Returns dict of {source_type: count}."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT source_type, COUNT(*) as cnt FROM persona_samples GROUP BY source_type"
        ).fetchall()
        return {row["source_type"]: row["cnt"] for row in rows}


def mark_sample_embedded(sample_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE persona_samples SET embedded_at = datetime('now') WHERE id = ?",
            (sample_id,),
        )


def get_unembedded_samples():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM persona_samples WHERE embedded_at IS NULL ORDER BY created_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def clear_persona_samples():
    with get_db() as conn:
        conn.execute("DELETE FROM persona_samples")


# ── Email Drafts ──

def save_email_draft(email_id, recipient, subject, body, status="pending_review",
                     confidence_score=0.0, category="", reasoning="", original_body=""):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO email_drafts
               (email_id, recipient, subject, body, status, confidence_score, category, reasoning, original_body)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (email_id, recipient, subject, body, status, confidence_score, category, reasoning, original_body),
        )
        return cur.lastrowid


def get_email_drafts(status=None, limit=50):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM email_drafts WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM email_drafts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_email_draft(draft_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM email_drafts WHERE id = ?", (draft_id,)
        ).fetchone()
        return dict(row) if row else None


def update_email_draft(draft_id, **kwargs):
    with get_db() as conn:
        allowed = {"body", "status", "confidence_score", "category", "reasoning"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [draft_id]
        conn.execute(f"UPDATE email_drafts SET {set_clause} WHERE id = ?", values)


def get_pending_drafts_count():
    with get_db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM email_drafts WHERE status IN ('pending_review', 'auto_approved', 'approved')"
        ).fetchone()[0]


# ── Sent Emails ──

def save_sent_email(draft_id, recipient, subject, body, smtp_message_id="", status="sent"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO sent_emails (draft_id, recipient, subject, body, smtp_message_id, status) VALUES (?, ?, ?, ?, ?, ?)",
            (draft_id, recipient, subject, body, smtp_message_id, status),
        )
        return cur.lastrowid


def get_sent_emails(limit=50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM sent_emails ORDER BY sent_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Exclusion Rules ──

def add_exclusion(pattern, reason=""):
    """Insert an exclusion pattern (email or @domain). Ignores duplicates."""
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO exclusion_rules (pattern, reason) VALUES (?, ?)",
            (pattern.strip().lower(), reason),
        )


def remove_exclusion(exclusion_id):
    """Delete an exclusion rule by id."""
    with get_db() as conn:
        conn.execute("DELETE FROM exclusion_rules WHERE id = ?", (exclusion_id,))


def get_exclusions():
    """Return all exclusion rules ordered by newest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM exclusion_rules ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_top_emailers(limit=5):
    """Return top senders by email count, most frequent first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT sender, COUNT(*) as cnt FROM emails GROUP BY sender ORDER BY cnt DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"sender": r["sender"], "count": r["cnt"]} for r in rows]


def is_excluded(email_address):
    """Check if an email address matches any exclusion pattern.
    Supports exact match and @domain suffix match.
    """
    if not email_address:
        return False
    email_lower = email_address.strip().lower()
    exclusions = get_exclusions()
    for exc in exclusions:
        pattern = exc["pattern"]
        if pattern.startswith("@"):
            # Domain match
            if email_lower.endswith(pattern):
                return True
        else:
            # Exact match
            if email_lower == pattern:
                return True
    return False


# ── Calendar Invites ──

def save_calendar_invite(draft_id, recipient, title, start_time, end_time,
                         google_event_id="", meet_link="", status="pending"):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO calendar_invites
               (draft_id, google_event_id, recipient, title, start_time, end_time, meet_link, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (draft_id, google_event_id, recipient, title, start_time, end_time, meet_link, status),
        )
        return cur.lastrowid


def get_calendar_invites(limit=50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM calendar_invites ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
