"""
Seed script — populates all tables with realistic M8TRX.AI business data.
Run once: python3 seed_data.py
"""

import json
from datetime import date, timedelta
import db

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
TWO_DAYS_AGO = (date.today() - timedelta(days=2)).isoformat()
THREE_DAYS_AGO = (date.today() - timedelta(days=3)).isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()
LAST_WEEK = (date.today() - timedelta(days=7)).isoformat()


def seed_tasks():
    """Create ~8 tasks with a mix of priorities, statuses, and due dates."""
    tasks = [
        {
            "title": "Finalize Series A pitch deck",
            "description": "Update financials slide with Q4 actuals, refine go-to-market narrative, and add competitive landscape analysis. Board review on Friday.",
            "priority": "critical",
            "due_date": TODAY,
            "assigned_to": "CEO",
        },
        {
            "title": "Review and sign partnership agreement with DataVault Inc.",
            "description": "Legal has reviewed the MSA. Need CEO signature and return to DataVault by EOD. Key terms: 18-month exclusivity, revenue share 70/30.",
            "priority": "critical",
            "due_date": YESTERDAY,  # overdue
            "assigned_to": "CEO",
        },
        {
            "title": "Prepare Q1 OKR presentation for all-hands",
            "description": "Compile departmental OKRs, highlight key wins from Q4, set company-level objectives for Q1. Include AI product roadmap milestones.",
            "priority": "high",
            "due_date": TOMORROW,
            "assigned_to": "CEO",
        },
        {
            "title": "Interview VP of Engineering candidates",
            "description": "Three finalists scheduled this week. Review resumes, prepare behavioral questions focused on scaling AI teams from 10 to 50 engineers.",
            "priority": "high",
            "due_date": NEXT_WEEK,
            "assigned_to": "CEO",
        },
        {
            "title": "Approve updated cloud infrastructure budget",
            "description": "DevOps submitted revised AWS/GCP spend projection. GPU costs up 40% due to model training. Need to approve or request revisions.",
            "priority": "medium",
            "due_date": TOMORROW,
            "assigned_to": "CTO",
        },
        {
            "title": "Draft blog post on AI-assisted executive workflows",
            "description": "Thought leadership piece for company blog. Cover how M8TRX.AI uses its own product internally. Target 1500 words, include screenshots.",
            "priority": "medium",
            "due_date": NEXT_WEEK,
            "assigned_to": "Marketing",
        },
        {
            "title": "Security audit follow-up: patch critical CVEs",
            "description": "Penetration test flagged 3 critical CVEs in dependencies. Engineering has patches ready — need deployment approval and post-patch verification.",
            "priority": "high",
            "due_date": TWO_DAYS_AGO,  # overdue
            "assigned_to": "CTO",
        },
        {
            "title": "Plan team offsite for Q1 kickoff",
            "description": "Book venue, create agenda, coordinate travel for remote team members. Budget: $15K. Preferred dates: last week of the month.",
            "priority": "low",
            "due_date": NEXT_WEEK,
            "assigned_to": "Operations",
        },
    ]

    task_ids = []
    for t in tasks:
        tid = db.create_task(**t)
        task_ids.append(tid)
        print(f"  Created task #{tid}: {t['title']}")

    # Mark some tasks as in_progress
    db.update_task(task_ids[0], status="in_progress")  # pitch deck
    db.update_task(task_ids[3], status="in_progress")  # VP interviews

    return task_ids


def seed_meetings():
    """Create ~4 meetings — one today, with raw notes and AI summaries."""
    meetings = [
        {
            "title": "Board Strategy Session",
            "date": TODAY,
            "raw_notes": """Attendees: CEO, CTO, CFO, Board Members (3)

1. Revenue Update
- Q4 revenue: $2.1M (up 34% QoQ)
- ARR run rate: $8.4M
- Net revenue retention: 125%
- 3 enterprise deals in pipeline worth $1.2M combined

2. Product Roadmap
- V2.0 launch targeted for March
- Key features: multi-modal document analysis, real-time collaboration, API marketplace
- Engineering headcount needs to grow from 12 to 20 by Q2

3. Fundraising
- Series A target: $15M at $60M pre-money
- 4 term sheets expected by end of month
- Lead investor preference: Tier 1 with AI/SaaS expertise

4. Key Decisions
- Approved hiring plan for 8 additional engineers
- Agreed to pursue enterprise-first GTM strategy
- Set board meeting cadence to monthly through Series A

Action items:
- CEO to finalize pitch deck by Friday
- CFO to prepare detailed financial model with 3 scenarios
- CTO to present technical architecture review next board meeting""",
            "ai_summary": """**Summary:** Board strategy session covered Q4 performance ($2.1M revenue, 34% QoQ growth), V2.0 product roadmap targeting March launch, and Series A fundraising targeting $15M at $60M pre-money valuation. Board approved hiring plan for 8 engineers and enterprise-first go-to-market strategy.

**Key Decisions:**
- Approved hiring plan for 8 additional engineers
- Agreed to pursue enterprise-first GTM strategy
- Set board meeting cadence to monthly through Series A

**Action Items:**
- CEO to finalize pitch deck by Friday
- CFO to prepare detailed financial model with 3 scenarios
- CTO to present technical architecture review next board meeting""",
        },
        {
            "title": "Weekly Product Standup",
            "date": TODAY,
            "raw_notes": """Attendees: CTO, Product Lead, 4 Engineers

Sprint progress:
- Document analysis pipeline: 80% complete, on track
- Chat memory improvements: deployed to staging, testing underway
- API rate limiting: completed and merged
- Mobile responsive fixes: blocked on design review

Blockers:
- Need UX mockups for document viewer by Wednesday
- GPU quota increase pending with AWS — ETA unknown

Next sprint priorities:
- Complete document analysis pipeline
- Begin multi-tenant architecture work
- Security audit remediation (3 critical CVEs)""",
            "ai_summary": """**Summary:** Weekly product standup reviewed sprint progress. Document analysis pipeline is 80% complete and on track. Chat memory improvements are in staging. API rate limiting is done. Mobile responsive work is blocked on design review. Key blockers include pending UX mockups and AWS GPU quota increase.

**Key Decisions:**
- Prioritize document analysis pipeline completion
- Begin multi-tenant architecture in next sprint
- Fast-track security audit remediation

**Action Items:**
- Product Lead to deliver UX mockups for document viewer by Wednesday
- CTO to escalate AWS GPU quota request
- Engineering to begin security CVE patches immediately""",
        },
        {
            "title": "Customer Success Review — Acme Corp",
            "date": YESTERDAY,
            "raw_notes": """Attendees: CEO, Customer Success Lead, Acme Corp VP of Ops

Account health: Green
- Using 3 of 5 modules (Tasks, Meetings, Email)
- 45 active users (up from 20 at launch)
- NPS score: 72

Feature requests:
- Document analysis (top priority for them)
- Slack integration
- Custom reporting dashboard

Expansion opportunity:
- Acme wants to roll out to 3 additional departments (~120 new seats)
- Potential upsell from $5K/mo to $18K/mo
- Need SOC2 compliance for their infosec team

Next steps:
- Send SOC2 timeline and roadmap
- Schedule demo of document analysis beta
- Draft expansion proposal""",
            "ai_summary": """**Summary:** Customer success review with Acme Corp showed strong account health (45 active users, NPS 72). Significant expansion opportunity identified: rollout to 3 additional departments could increase MRR from $5K to $18K. Key blocker is SOC2 compliance requirement. Document analysis is their top feature request.

**Key Decisions:**
- Prioritize SOC2 compliance timeline
- Offer early access to document analysis beta
- Pursue expansion opportunity aggressively

**Action Items:**
- Customer Success Lead to send SOC2 timeline by Friday
- CEO to schedule document analysis beta demo for Acme
- Sales to draft expansion proposal with volume pricing""",
        },
        {
            "title": "Investor Coffee Chat — Sequoia Partner",
            "date": THREE_DAYS_AGO,
            "raw_notes": """Informal meeting with Sarah Chen, Partner at Sequoia

Discussed:
- M8TRX.AI vision and market positioning
- AI executive assistant market sizing ($4.2B TAM by 2027)
- Competitive differentiation (context-aware, multi-modal, enterprise-grade)
- Team background and technical moat

Sarah's feedback:
- Loves the product-led growth angle
- Wants to see more enterprise traction before committing
- Suggested connecting with their portfolio company for a design partnership
- Would participate in Series A if metrics continue trending up

Follow-up:
- Send product demo video and metrics deck
- Schedule formal partner meeting in 3 weeks
- Connect with their portfolio company (NexGen Analytics)""",
            "ai_summary": "",
        },
    ]

    meeting_ids = []
    for m in meetings:
        mid = db.save_meeting(
            title=m["title"],
            meeting_date=m["date"],
            raw_notes=m["raw_notes"],
            ai_summary=m["ai_summary"],
        )
        meeting_ids.append(mid)
        print(f"  Created meeting #{mid}: {m['title']}")

    return meeting_ids


def seed_action_items(meeting_ids, task_ids):
    """Link meeting action items to tasks where appropriate."""
    if len(meeting_ids) >= 1 and len(task_ids) >= 1:
        # Board meeting action items
        db.save_action_item(
            meeting_id=meeting_ids[0],
            description="Finalize pitch deck by Friday",
            owner="CEO",
            due_date=TODAY,
            task_id=task_ids[0],  # linked to pitch deck task
        )
        db.save_action_item(
            meeting_id=meeting_ids[0],
            description="Prepare detailed financial model with 3 scenarios",
            owner="CFO",
            due_date=(date.today() + timedelta(days=5)).isoformat(),
        )
        db.save_action_item(
            meeting_id=meeting_ids[0],
            description="Present technical architecture review next board meeting",
            owner="CTO",
            due_date=(date.today() + timedelta(days=30)).isoformat(),
        )
        print("  Linked board meeting action items")

    if len(meeting_ids) >= 2:
        # Standup action items
        db.save_action_item(
            meeting_id=meeting_ids[1],
            description="Deliver UX mockups for document viewer by Wednesday",
            owner="Product Lead",
            due_date=(date.today() + timedelta(days=2)).isoformat(),
        )
        db.save_action_item(
            meeting_id=meeting_ids[1],
            description="Escalate AWS GPU quota request",
            owner="CTO",
            due_date=TOMORROW,
        )
        print("  Linked standup action items")


def seed_emails():
    """Create ~5 emails with a mix of urgencies and summaries."""
    emails = [
        {
            "sender": "sarah.chen@sequoia.com",
            "subject": "Follow-up: M8TRX.AI Series A Discussion",
            "body": """Hi,

Great meeting last week. I've discussed M8TRX.AI with our partnership team and we're very interested in continuing the conversation.

Could you send over:
1. Updated metrics deck (MRR, growth rate, cohort retention)
2. Product demo video (5-10 min)
3. Technical architecture overview

We'd like to schedule a formal partner meeting in the next 2-3 weeks. I've CC'd my associate who will handle scheduling.

Looking forward to it.

Best,
Sarah Chen
Partner, Sequoia Capital""",
            "processed_summary": "Sequoia partner Sarah Chen following up on Series A discussion. Requesting metrics deck, product demo video, and technical architecture overview. Wants to schedule formal partner meeting in 2-3 weeks. Strong buying signal.",
            "urgency": "important",
            "action_items": json.dumps([
                {"description": "Send updated metrics deck to Sequoia", "owner": "CEO", "due_date": TOMORROW},
                {"description": "Record 5-10 min product demo video", "owner": "Product Lead", "due_date": NEXT_WEEK},
                {"description": "Prepare technical architecture overview doc", "owner": "CTO", "due_date": NEXT_WEEK},
            ]),
        },
        {
            "sender": "legal@datavault.io",
            "subject": "URGENT: Partnership Agreement — Signature Required by EOD",
            "body": """Dear M8TRX.AI Team,

This is a reminder that the Master Service Agreement for the DataVault-M8TRX.AI partnership requires execution by end of business today.

Key terms as agreed:
- 18-month exclusivity period for AI document analysis integration
- Revenue share: 70% M8TRX.AI / 30% DataVault
- Minimum commitment: 500 API calls/month
- SLA: 99.9% uptime guarantee

The DocuSign link was sent to the CEO's email on Monday. Please sign at your earliest convenience to avoid delays in the integration timeline.

Regards,
DataVault Legal Team""",
            "processed_summary": "Urgent reminder from DataVault Legal requiring CEO signature on MSA by end of business today. Key terms: 18-month exclusivity, 70/30 revenue share, 500 API calls/month minimum, 99.9% SLA. DocuSign link was sent Monday.",
            "urgency": "critical",
            "action_items": json.dumps([
                {"description": "Sign DataVault partnership MSA via DocuSign", "owner": "CEO", "due_date": TODAY},
            ]),
        },
        {
            "sender": "cto@m8trx.ai",
            "subject": "Security Audit Results — 3 Critical CVEs Found",
            "body": """Team,

The penetration test results are in. Overall security posture is strong, but we have 3 critical CVEs that need immediate attention:

1. CVE-2024-38816 — Spring Framework path traversal (CVSS 9.1)
   - Affects: API gateway service
   - Fix: Upgrade spring-boot to 3.3.4+

2. CVE-2024-45337 — Go crypto/ssh auth bypass (CVSS 9.1)
   - Affects: Internal tooling SSH connections
   - Fix: Upgrade golang.org/x/crypto

3. CVE-2024-50379 — Apache Tomcat race condition (CVSS 8.1)
   - Affects: Legacy reporting module
   - Fix: Upgrade Tomcat to 11.0.2+

Patches are ready and tested in staging. Need deployment approval for production rollout this week.

— CTO""",
            "processed_summary": "Internal security audit found 3 critical CVEs (CVSS 8.1-9.1) affecting API gateway, SSH tooling, and reporting module. Patches are ready and tested in staging. Production deployment approval needed this week.",
            "urgency": "critical",
            "action_items": json.dumps([
                {"description": "Approve production deployment of security patches", "owner": "CEO", "due_date": TODAY},
                {"description": "Verify post-patch security scan results", "owner": "CTO", "due_date": TOMORROW},
            ]),
        },
        {
            "sender": "hr@m8trx.ai",
            "subject": "VP Engineering Candidates — Interview Schedule",
            "body": """Hi,

Here are the three finalists for the VP of Engineering role, scheduled for this week:

1. Tuesday 2pm — Alex Rivera (ex-Stripe, scaled eng from 15→80)
2. Wednesday 10am — Priya Sharma (ex-Google Brain, ML infrastructure lead)
3. Thursday 3pm — Marcus Chen (ex-Databricks, built data platform team)

Interview format: 45-min CEO conversation + 30-min technical deep dive with CTO.

Please review their resumes (attached) and let me know if any schedule changes are needed.

Best,
HR Team""",
            "processed_summary": "Three VP Engineering finalists scheduled for interviews this week: Alex Rivera (ex-Stripe), Priya Sharma (ex-Google Brain), Marcus Chen (ex-Databricks). 45-min CEO conversation + 30-min CTO technical deep dive format.",
            "urgency": "important",
            "action_items": json.dumps([
                {"description": "Review VP Engineering candidate resumes", "owner": "CEO", "due_date": TODAY},
                {"description": "Prepare interview questions for VP Engineering candidates", "owner": "CEO", "due_date": TOMORROW},
            ]),
        },
        {
            "sender": "newsletter@ainews.com",
            "subject": "AI Weekly: OpenAI launches new reasoning model, Anthropic raises $2B",
            "body": """This Week in AI:

1. OpenAI launches o3-mini reasoning model with improved performance
2. Anthropic closes $2B funding round led by Google
3. EU AI Act enforcement begins — what companies need to know
4. New research: LLMs show emergent planning capabilities
5. Startup spotlight: AI-powered legal document analysis raises $50M

Read more at ainews.com/weekly

Unsubscribe: ainews.com/unsubscribe""",
            "processed_summary": "Weekly AI industry newsletter covering OpenAI's new reasoning model, Anthropic's $2B funding round, EU AI Act enforcement, LLM research updates, and a legal AI startup funding round. General industry awareness — no action required.",
            "urgency": "fyi",
            "action_items": json.dumps([]),
        },
    ]

    for e in emails:
        eid = db.save_email(
            sender=e["sender"],
            subject=e["subject"],
            body=e["body"],
            processed_summary=e["processed_summary"],
            urgency=e["urgency"],
            action_items=e["action_items"],
        )
        print(f"  Created email #{eid}: [{e['urgency'].upper()}] {e['subject']}")


def main():
    print("Initializing database...")
    db.init_db()

    print("\nSeeding tasks...")
    task_ids = seed_tasks()

    print("\nSeeding meetings...")
    meeting_ids = seed_meetings()

    print("\nSeeding meeting action items...")
    seed_action_items(meeting_ids, task_ids)

    print("\nSeeding emails...")
    seed_emails()

    print("\nDone! Seed data populated successfully.")
    print(f"  Tasks: {len(task_ids)}")
    print(f"  Meetings: {len(meeting_ids)}")
    print(f"  Emails: 5")


if __name__ == "__main__":
    main()
