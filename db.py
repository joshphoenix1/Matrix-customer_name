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
    assigned_to TEXT DEFAULT '',
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

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    avatar_color TEXT DEFAULT '#6C5CE7',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'away', 'offline')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    key TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    lead_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (lead_id) REFERENCES employees(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channel_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    sender_name TEXT NOT NULL,
    sender_avatar_color TEXT DEFAULT '#6C5CE7',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
);
"""


def init_db():
    """Initialize the database schema."""
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)
        # Add project_id column to tasks if it doesn't exist
        cols = [row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "project_id" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL")


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

def create_task(title, description="", priority="medium", due_date=None, assigned_to="", project_id=None):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, priority, due_date, assigned_to, project_id) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, priority, due_date, assigned_to, project_id),
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
        allowed = {"title", "description", "priority", "status", "due_date", "assigned_to", "project_id"}
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


# ── Employees ──

def create_employee(name, email, role, department, avatar_color="#6C5CE7", status="active"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO employees (name, email, role, department, avatar_color, status) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, role, department, avatar_color, status),
        )
        return cur.lastrowid


def get_employees():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM employees ORDER BY name ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_employee(employee_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        return dict(row) if row else None


# ── Projects ──

def create_project(name, key, description="", lead_id=None, status="active"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO projects (name, key, description, lead_id) VALUES (?, ?, ?, ?)",
            (name, key, description, lead_id),
        )
        return cur.lastrowid


def get_projects(status=None):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_project(project_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return dict(row) if row else None


def get_tasks_by_project(project_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, created_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Channels ──

def create_channel(name, description=""):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO channels (name, description) VALUES (?, ?)",
            (name, description),
        )
        return cur.lastrowid


def get_channels():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM channels ORDER BY name ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_channel(channel_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM channels WHERE id = ?", (channel_id,)
        ).fetchone()
        return dict(row) if row else None


def send_channel_message(channel_id, sender_name, content, sender_avatar_color="#6C5CE7"):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO channel_messages (channel_id, sender_name, sender_avatar_color, content) VALUES (?, ?, ?, ?)",
            (channel_id, sender_name, sender_avatar_color, content),
        )
        return cur.lastrowid


def get_channel_messages(channel_id, limit=100):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM channel_messages WHERE channel_id = ? ORDER BY created_at ASC LIMIT ?",
            (channel_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_channel_messages(channel_id):
    with get_db() as conn:
        conn.execute("DELETE FROM channel_messages WHERE channel_id = ?", (channel_id,))
