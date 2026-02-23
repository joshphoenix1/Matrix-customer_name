"""
SQLite database layer — schema, init, and helper functions.
"""

import sqlite3
import json
from datetime import datetime, date
from contextlib import contextmanager
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
