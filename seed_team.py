"""
Seed script — populates employees, projects, and project board tasks.
Run once: python3 seed_team.py
"""

from datetime import date, timedelta
import db

TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
IN_3_DAYS = (date.today() + timedelta(days=3)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()
IN_2_WEEKS = (date.today() + timedelta(days=14)).isoformat()
LAST_WEEK = (date.today() - timedelta(days=5)).isoformat()


def seed_employees():
    """Create 8 employees across departments."""
    employees = [
        {"name": "Alex Rivera", "email": "alex@m8trx.ai", "role": "CEO", "department": "Executive", "avatar_color": "#6C5CE7"},
        {"name": "Priya Sharma", "email": "priya@m8trx.ai", "role": "CTO", "department": "Engineering", "avatar_color": "#00B894"},
        {"name": "Marcus Chen", "email": "marcus@m8trx.ai", "role": "VP Engineering", "department": "Engineering", "avatar_color": "#0984E3"},
        {"name": "Sarah Kim", "email": "sarah@m8trx.ai", "role": "Product Lead", "department": "Product", "avatar_color": "#E17055"},
        {"name": "James Wilson", "email": "james@m8trx.ai", "role": "Senior Engineer", "department": "Engineering", "avatar_color": "#FDCB6E"},
        {"name": "Elena Rodriguez", "email": "elena@m8trx.ai", "role": "UX Designer", "department": "Design", "avatar_color": "#FD79A8"},
        {"name": "David Park", "email": "david@m8trx.ai", "role": "DevOps Lead", "department": "Engineering", "avatar_color": "#55EFC4"},
        {"name": "Maya Johnson", "email": "maya@m8trx.ai", "role": "Marketing Director", "department": "Marketing", "avatar_color": "#A29BFE"},
    ]

    emp_ids = {}
    for e in employees:
        eid = db.create_employee(**e)
        emp_ids[e["name"]] = eid
        status = "active"
        if e["name"] == "James Wilson":
            status = "away"
        if e["name"] == "David Park":
            status = "away"
        if status != "active":
            with db.get_db() as conn:
                conn.execute("UPDATE employees SET status = ? WHERE id = ?", (status, eid))
        print(f"  Created employee #{eid}: {e['name']} — {e['role']}")

    return emp_ids


def seed_projects(emp_ids):
    """Create 3 active projects."""
    projects = [
        {
            "name": "Platform V2.0",
            "key": "PLAT",
            "description": "Next-gen platform with multi-tenant architecture and enterprise features",
            "lead_id": emp_ids.get("Priya Sharma"),
        },
        {
            "name": "AI Engine",
            "key": "AI",
            "description": "Core AI capabilities — document analysis, smart summarization, context engine",
            "lead_id": emp_ids.get("Marcus Chen"),
        },
        {
            "name": "Go-to-Market",
            "key": "GTM",
            "description": "Sales enablement, marketing campaigns, and customer acquisition",
            "lead_id": emp_ids.get("Maya Johnson"),
        },
    ]

    proj_ids = {}
    for p in projects:
        pid = db.create_project(**p)
        proj_ids[p["key"]] = pid
        print(f"  Created project #{pid}: [{p['key']}] {p['name']}")

    return proj_ids


def seed_board_tasks(proj_ids):
    """Create project-specific tasks spread across kanban columns."""

    # ── PLAT: Platform V2.0 tasks ──
    plat_id = proj_ids["PLAT"]
    plat_tasks = [
        {"title": "Design multi-tenant data isolation layer", "description": "Implement row-level security and tenant-scoped queries for all database operations.", "priority": "critical", "status": "in_progress", "due_date": IN_3_DAYS, "assigned_to": "Priya Sharma"},
        {"title": "Implement SSO/SAML authentication", "description": "Add enterprise SSO support with SAML 2.0 and OIDC. Support Okta, Azure AD, Google Workspace.", "priority": "high", "status": "in_progress", "due_date": NEXT_WEEK, "assigned_to": "James Wilson"},
        {"title": "Build tenant admin dashboard", "description": "Dashboard for tenant admins to manage users, roles, permissions, and usage analytics.", "priority": "high", "status": "pending", "due_date": IN_2_WEEKS, "assigned_to": "Sarah Kim"},
        {"title": "Set up staging environment with tenant simulation", "description": "Deploy multi-tenant staging env with 3 simulated tenants for QA testing.", "priority": "medium", "status": "pending", "due_date": NEXT_WEEK, "assigned_to": "David Park"},
        {"title": "Database migration plan for v1 → v2 schema", "description": "Zero-downtime migration strategy for existing single-tenant customers.", "priority": "high", "status": "pending", "due_date": IN_2_WEEKS, "assigned_to": "Marcus Chen"},
        {"title": "Load testing: 100 concurrent tenants", "description": "Performance benchmarks with 100 tenants, 1000 concurrent users, and mixed workloads.", "priority": "medium", "status": "pending", "due_date": IN_2_WEEKS, "assigned_to": "David Park"},
        {"title": "API rate limiting per tenant", "description": "Implement configurable rate limits per tenant with Redis-based token bucket.", "priority": "medium", "status": "completed", "due_date": LAST_WEEK, "assigned_to": "James Wilson"},
        {"title": "Tenant onboarding wizard UI", "description": "Step-by-step wizard for new tenant setup: branding, users, integrations.", "priority": "low", "status": "pending", "due_date": IN_2_WEEKS, "assigned_to": "Elena Rodriguez"},
    ]

    for t in plat_tasks:
        status = t.pop("status")
        tid = db.create_task(**t, project_id=plat_id)
        if status != "pending":
            db.update_task(tid, status=status)
        print(f"  [{proj_ids['PLAT']}:PLAT-{tid}] {t['title'][:50]}  ({status})")

    # ── AI: AI Engine tasks ──
    ai_id = proj_ids["AI"]
    ai_tasks = [
        {"title": "Document analysis pipeline — PDF support", "description": "Add PDF text extraction using pdfplumber. Handle scanned PDFs with OCR fallback.", "priority": "critical", "status": "in_progress", "due_date": TOMORROW, "assigned_to": "Marcus Chen"},
        {"title": "Context window optimization for large documents", "description": "Implement sliding window chunking with overlap for documents exceeding 100K tokens.", "priority": "high", "status": "in_progress", "due_date": IN_3_DAYS, "assigned_to": "Priya Sharma"},
        {"title": "Build evaluation harness for AI accuracy", "description": "Automated evaluation suite: 50 test documents with ground-truth annotations. Track precision/recall/F1.", "priority": "high", "status": "pending", "due_date": NEXT_WEEK, "assigned_to": "James Wilson"},
        {"title": "Smart email thread summarization", "description": "Detect email threads and generate thread-level summaries instead of per-email.", "priority": "medium", "status": "pending", "due_date": NEXT_WEEK, "assigned_to": "Marcus Chen"},
        {"title": "Entity extraction with relationship mapping", "description": "Extract people, orgs, dates, and amounts. Build relationship graph between entities.", "priority": "medium", "status": "pending", "due_date": IN_2_WEEKS, "assigned_to": "Priya Sharma"},
        {"title": "Prompt template versioning system", "description": "Version control for AI prompts with A/B testing support and rollback capability.", "priority": "low", "status": "completed", "due_date": LAST_WEEK, "assigned_to": "Marcus Chen"},
        {"title": "Meeting action item auto-detection accuracy improvement", "description": "Improve action item extraction from meeting notes. Current accuracy: 78%, target: 90%+.", "priority": "high", "status": "completed", "due_date": LAST_WEEK, "assigned_to": "James Wilson"},
    ]

    for t in ai_tasks:
        status = t.pop("status")
        tid = db.create_task(**t, project_id=ai_id)
        if status != "pending":
            db.update_task(tid, status=status)
        print(f"  [{proj_ids['AI']}:AI-{tid}] {t['title'][:50]}  ({status})")

    # ── GTM: Go-to-Market tasks ──
    gtm_id = proj_ids["GTM"]
    gtm_tasks = [
        {"title": "Launch Acme Corp expansion campaign", "description": "Personalized outreach to 3 Acme departments. Create tailored demo environments per dept.", "priority": "critical", "status": "in_progress", "due_date": TOMORROW, "assigned_to": "Maya Johnson"},
        {"title": "Create product demo video (5-10 min)", "description": "Professional walkthrough video covering core features: tasks, meetings, email triage, document analysis.", "priority": "high", "status": "in_progress", "due_date": IN_3_DAYS, "assigned_to": "Elena Rodriguez"},
        {"title": "Build investor metrics dashboard", "description": "One-page live dashboard showing MRR, growth rate, retention, pipeline — for Series A conversations.", "priority": "high", "status": "pending", "due_date": NEXT_WEEK, "assigned_to": "Sarah Kim"},
        {"title": "Write 3 customer case studies", "description": "Case studies from Acme Corp, NexGen Analytics, and TechFlow. Include ROI metrics and quotes.", "priority": "medium", "status": "pending", "due_date": IN_2_WEEKS, "assigned_to": "Maya Johnson"},
        {"title": "Design enterprise pricing page", "description": "Three-tier pricing: Starter ($29/user), Pro ($79/user), Enterprise (custom). Feature comparison matrix.", "priority": "medium", "status": "pending", "due_date": NEXT_WEEK, "assigned_to": "Elena Rodriguez"},
        {"title": "Competitive analysis document", "description": "Deep dive on 5 competitors: features, pricing, market positioning, strengths/weaknesses.", "priority": "low", "status": "completed", "due_date": LAST_WEEK, "assigned_to": "Sarah Kim"},
        {"title": "Set up HubSpot CRM pipeline", "description": "Configure deal stages, automate lead scoring, set up email sequences for inbound leads.", "priority": "medium", "status": "completed", "due_date": LAST_WEEK, "assigned_to": "Maya Johnson"},
    ]

    for t in gtm_tasks:
        status = t.pop("status")
        tid = db.create_task(**t, project_id=gtm_id)
        if status != "pending":
            db.update_task(tid, status=status)
        print(f"  [{proj_ids['GTM']}:GTM-{tid}] {t['title'][:50]}  ({status})")


def main():
    print("Initializing database (adding new tables + project_id column)...")
    db.init_db()

    print("\nSeeding employees...")
    emp_ids = seed_employees()

    print("\nSeeding projects...")
    proj_ids = seed_projects(emp_ids)

    print("\nSeeding board tasks...")
    seed_board_tasks(proj_ids)

    # Assign existing tasks to projects where relevant
    print("\nLinking existing tasks to projects...")
    existing_tasks = db.get_tasks()
    for t in existing_tasks:
        if t.get("project_id"):
            continue
        title_lower = t["title"].lower()
        if any(kw in title_lower for kw in ["pitch deck", "series a", "okr", "partnership", "offsite"]):
            db.update_task(t["id"], project_id=proj_ids["GTM"])
            print(f"  Linked task #{t['id']} to GTM")
        elif any(kw in title_lower for kw in ["security", "infrastructure", "cloud"]):
            db.update_task(t["id"], project_id=proj_ids["PLAT"])
            print(f"  Linked task #{t['id']} to PLAT")
        elif any(kw in title_lower for kw in ["blog", "engineering", "vp"]):
            db.update_task(t["id"], project_id=proj_ids["AI"])
            print(f"  Linked task #{t['id']} to AI")

    print("\nDone! Team data populated successfully.")
    print(f"  Employees: 8")
    print(f"  Projects: 3")
    total_board = sum(len(db.get_tasks_by_project(pid)) for pid in proj_ids.values())
    print(f"  Board tasks: {total_board}")


if __name__ == "__main__":
    main()
