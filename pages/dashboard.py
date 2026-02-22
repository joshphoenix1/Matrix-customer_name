"""
Dashboard page — daily priorities, KPIs, agenda, email digest, quick actions.
"""

import json
import os
import shutil
import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from datetime import date, datetime
from config import COLORS, COMPANY_NAME, EMAIL_ADDRESS, ANTHROPIC_API_KEY, BASE_DIR
import db
from components.kpi_card import kpi_card
from services.claude_client import generate_daily_priorities
from services.email_ingestion import process_incoming_email

dash.register_page(__name__, path="/", name="Dashboard", order=1)


def _greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


# ── Layout ──

layout = html.Div(
    children=[
        dcc.Store(id="dashboard-refresh-trigger", data=0),

        # Hero greeting
        html.Div(
            style={
                "background": f"linear-gradient(135deg, {COLORS['card_bg']} 0%, #2D1B69 100%)",
                "borderRadius": "16px",
                "padding": "32px 40px",
                "marginBottom": "24px",
            },
            children=[
                html.H1(
                    id="dashboard-greeting",
                    style={"color": COLORS["text_primary"], "fontSize": "1.8rem", "margin": "0 0 8px 0", "fontWeight": "800"},
                ),
                html.P(
                    "Here's your daily briefing.",
                    style={"color": COLORS["text_secondary"], "fontSize": "1rem", "margin": 0},
                ),
            ],
        ),

        # KPI row
        html.Div(
            id="kpi-row",
            style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"},
        ),

        # Main grid: priorities + agenda
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Daily Priorities card
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['accent']}",
                            },
                            children=[
                                html.Div(
                                    style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"},
                                    children=[
                                        html.H3("Daily Priorities", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                                        dbc.Button(
                                            "Refresh",
                                            id="btn-refresh-priorities",
                                            size="sm",
                                            outline=True,
                                            color="light",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                    ],
                                ),
                                html.Div(id="daily-priorities-content"),
                            ],
                        ),
                    ],
                    md=7,
                ),
                dbc.Col(
                    [
                        # Today's Agenda
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['info']}",
                            },
                            children=[
                                html.H3("Today's Agenda", style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1.1rem"}),
                                html.Div(id="todays-agenda"),
                            ],
                        ),
                        # Quick Actions
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['success']}",
                            },
                            children=[
                                html.H3("Quick Actions", style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1.1rem"}),
                                html.Div(
                                    style={"display": "flex", "flexDirection": "column", "gap": "8px"},
                                    children=[
                                        dcc.Link(
                                            dbc.Button("Add Task", color="primary", size="sm", style={"width": "100%", "background": COLORS["accent"], "border": "none"}),
                                            href="/tasks",
                                        ),
                                        dcc.Link(
                                            dbc.Button("Log Meeting Notes", color="info", size="sm", outline=True, style={"width": "100%"}),
                                            href="/meetings",
                                        ),
                                        dcc.Link(
                                            dbc.Button("Chat with Agent", color="success", size="sm", outline=True, style={"width": "100%"}),
                                            href="/chat",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                    md=5,
                ),
            ],
            className="mb-4",
        ),

        # System Status: Storage + API Connections + Revenue
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Storage Monitor
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['info']}",
                            },
                            children=[
                                html.H3(
                                    [html.I(className="bi bi-hdd-stack", style={"marginRight": "10px"}), "Storage"],
                                    style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1.1rem"},
                                ),
                                html.Div(id="storage-monitor"),
                            ],
                        ),
                        # API Connections
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['success']}",
                            },
                            children=[
                                html.H3(
                                    [html.I(className="bi bi-plug", style={"marginRight": "10px"}), "API Connections"],
                                    style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1.1rem"},
                                ),
                                html.Div(id="api-connections"),
                            ],
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        # Revenue & Financials
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['success']}",
                            },
                            children=[
                                html.H3(
                                    [html.I(className="bi bi-currency-dollar", style={"marginRight": "10px"}), "Revenue & Financials"],
                                    style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1.1rem"},
                                ),
                                html.Div(id="revenue-financials"),
                            ],
                        ),
                    ],
                    md=8,
                ),
            ],
            className="mb-4",
        ),

        # Email section
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Email input form
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "borderLeft": f"4px solid {COLORS['warning']}",
                            },
                            children=[
                                html.H3("Process Email", style={"color": COLORS["text_primary"], "margin": "0 0 4px 0", "fontSize": "1.1rem"}),
                                html.P(
                                    f"Paste email content below or forward to {EMAIL_ADDRESS}",
                                    style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "marginBottom": "16px"},
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Input(id="email-sender", placeholder="From (sender)", style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]}),
                                            md=6,
                                        ),
                                        dbc.Col(
                                            dbc.Input(id="email-subject", placeholder="Subject", style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]}),
                                            md=6,
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                dbc.Textarea(
                                    id="email-body",
                                    placeholder="Paste email body here...",
                                    style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "minHeight": "120px"},
                                    className="mb-2",
                                ),
                                dbc.Button("Process with AI", id="btn-process-email", color="warning", style={"border": "none"}),
                                html.Div(id="email-processing-result", style={"marginTop": "16px"}),
                            ],
                        ),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        # Recent email digest
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "borderLeft": f"4px solid {COLORS['info']}",
                            },
                            children=[
                                html.H3("Recent Email Digest", style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1.1rem"}),
                                html.Div(id="email-digest"),
                            ],
                        ),
                    ],
                    md=6,
                ),
            ],
        ),
    ]
)


# ── Callbacks ──

URGENCY_COLORS = {
    "critical": COLORS["danger"],
    "important": COLORS["warning"],
    "routine": COLORS["info"],
    "fyi": COLORS["text_muted"],
}


@callback(
    Output("dashboard-greeting", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_greeting(_):
    return f"{_greeting()}."


@callback(
    Output("kpi-row", "children"),
    Input("dashboard-refresh-trigger", "data"),
    Input("btn-process-email", "n_clicks"),
    Input("btn-refresh-priorities", "n_clicks"),
)
def update_kpis(*_):
    all_tasks = db.get_tasks()
    active = [t for t in all_tasks if t["status"] not in ("completed", "cancelled")]
    due_today = db.get_tasks_due_today()
    meetings_today = db.get_todays_meetings()
    emails = db.get_emails(limit=100)

    return [
        kpi_card("Open Tasks", len(active), f"{len(all_tasks)} total", COLORS["accent"]),
        kpi_card("Due Today", len(due_today), "tasks due", COLORS["warning"]),
        kpi_card("Meetings Today", len(meetings_today), "scheduled", COLORS["info"]),
        kpi_card("Emails Processed", len(emails), "total received", COLORS["success"]),
    ]


@callback(
    Output("todays-agenda", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_agenda(_):
    meetings = db.get_todays_meetings()
    if not meetings:
        return html.P("No meetings scheduled today.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem"})
    return html.Div(
        [
            html.Div(
                style={"padding": "8px 0", "borderBottom": f"1px solid {COLORS['border']}"},
                children=[
                    html.Span(m["title"], style={"color": COLORS["text_primary"], "fontSize": "0.9rem"}),
                ],
            )
            for m in meetings
        ]
    )


@callback(
    Output("daily-priorities-content", "children"),
    Input("btn-refresh-priorities", "n_clicks"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_priorities(*_):
    tasks = db.get_tasks()
    active_tasks = [t for t in tasks if t["status"] not in ("completed", "cancelled")]
    meetings = db.get_todays_meetings()
    emails = db.get_emails(5)

    if not active_tasks and not meetings and not emails:
        return html.P(
            "No data yet. Add tasks, log meetings, or process emails to get AI-generated priorities.",
            style={"color": COLORS["text_muted"], "fontSize": "0.9rem"},
        )

    # Generate priorities
    briefing = generate_daily_priorities(active_tasks, meetings, emails)
    return dcc.Markdown(
        briefing,
        style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.6"},
    )


@callback(
    Output("email-processing-result", "children"),
    Output("email-sender", "value"),
    Output("email-subject", "value"),
    Output("email-body", "value"),
    Output("email-digest", "children", allow_duplicate=True),
    Input("btn-process-email", "n_clicks"),
    State("email-sender", "value"),
    State("email-subject", "value"),
    State("email-body", "value"),
    prevent_initial_call=True,
)
def process_email_form(n, sender, subject, body):
    if not n or not sender or not subject or not body:
        return no_update, no_update, no_update, no_update, no_update

    result = process_incoming_email(sender.strip(), subject.strip(), body.strip())

    urgency_color = URGENCY_COLORS.get(result.get("urgency", "routine"), COLORS["text_muted"])

    result_card = html.Div(
        style={
            "background": COLORS["body_bg"],
            "borderRadius": "8px",
            "padding": "16px",
            "borderLeft": f"4px solid {urgency_color}",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "8px"},
                children=[
                    html.Span(
                        result.get("urgency", "routine").upper(),
                        style={"background": urgency_color, "color": "#fff", "padding": "2px 8px", "borderRadius": "4px", "fontSize": "0.7rem", "fontWeight": "600"},
                    ),
                    html.Span("Email processed successfully", style={"color": COLORS["success"], "fontSize": "0.85rem"}),
                ],
            ),
            html.P(result.get("summary", ""), style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "marginBottom": "8px"}),
        ] + (
            [html.P(
                f"Task created: {result.get('suggested_task_title', '')}",
                style={"color": COLORS["accent"], "fontSize": "0.85rem"},
            )] if result.get("created_task_id") else []
        ),
    )

    return result_card, "", "", "", _render_email_digest()


@callback(
    Output("email-digest", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_digest(_):
    return _render_email_digest()


@callback(
    Output("storage-monitor", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_storage(_):
    # Disk usage
    total, used, free = shutil.disk_usage("/")
    total_gb = total / (1024 ** 3)
    used_gb = used / (1024 ** 3)
    free_gb = free / (1024 ** 3)
    pct = (used / total) * 100

    # DB file size
    db_path = os.path.join(BASE_DIR, "data", "m8trx.db")
    db_size_mb = os.path.getsize(db_path) / (1024 ** 2) if os.path.exists(db_path) else 0

    # Uploads dir size
    uploads_dir = os.path.join(BASE_DIR, "data", "uploads")
    uploads_size = 0
    if os.path.exists(uploads_dir):
        for f in os.listdir(uploads_dir):
            fp = os.path.join(uploads_dir, f)
            if os.path.isfile(fp):
                uploads_size += os.path.getsize(fp)
    uploads_mb = uploads_size / (1024 ** 2)

    bar_color = COLORS["success"] if pct < 70 else (COLORS["warning"] if pct < 90 else COLORS["danger"])

    return html.Div([
        # Disk usage bar
        html.Div(
            style={"marginBottom": "16px"},
            children=[
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between", "marginBottom": "6px"},
                    children=[
                        html.Span("Disk Usage", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                        html.Span(f"{pct:.1f}%", style={"color": bar_color, "fontSize": "0.85rem", "fontWeight": "700"}),
                    ],
                ),
                html.Div(
                    style={"background": COLORS["body_bg"], "borderRadius": "6px", "height": "10px", "overflow": "hidden"},
                    children=[
                        html.Div(style={"width": f"{pct:.1f}%", "height": "100%", "background": bar_color, "borderRadius": "6px", "transition": "width 0.5s"}),
                    ],
                ),
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between", "marginTop": "6px"},
                    children=[
                        html.Span(f"{used_gb:.1f} GB used", style={"color": COLORS["text_muted"], "fontSize": "0.75rem"}),
                        html.Span(f"{free_gb:.1f} GB free", style={"color": COLORS["text_muted"], "fontSize": "0.75rem"}),
                    ],
                ),
            ],
        ),
        # Breakdown
        html.Div(
            style={"display": "flex", "flexDirection": "column", "gap": "8px"},
            children=[
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between"},
                    children=[
                        html.Span([html.I(className="bi bi-database", style={"marginRight": "6px"}), "Database"], style={"color": COLORS["text_secondary"], "fontSize": "0.8rem"}),
                        html.Span(f"{db_size_mb:.2f} MB", style={"color": COLORS["text_primary"], "fontSize": "0.8rem", "fontWeight": "600"}),
                    ],
                ),
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between"},
                    children=[
                        html.Span([html.I(className="bi bi-folder", style={"marginRight": "6px"}), "Uploads"], style={"color": COLORS["text_secondary"], "fontSize": "0.8rem"}),
                        html.Span(f"{uploads_mb:.2f} MB", style={"color": COLORS["text_primary"], "fontSize": "0.8rem", "fontWeight": "600"}),
                    ],
                ),
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between"},
                    children=[
                        html.Span([html.I(className="bi bi-hdd", style={"marginRight": "6px"}), "Total Disk"], style={"color": COLORS["text_secondary"], "fontSize": "0.8rem"}),
                        html.Span(f"{total_gb:.1f} GB", style={"color": COLORS["text_primary"], "fontSize": "0.8rem", "fontWeight": "600"}),
                    ],
                ),
            ],
        ),
    ])


@callback(
    Output("api-connections", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_api_connections(_):
    def _status_dot(connected):
        color = COLORS["success"] if connected else COLORS["danger"]
        label = "Connected" if connected else "Not Configured"
        return html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "8px 0", "borderBottom": f"1px solid {COLORS['border']}"},
            children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                    html.Span(style={"width": "10px", "height": "10px", "borderRadius": "50%", "background": color, "flexShrink": "0", "boxShadow": f"0 0 6px {color}"}),
                ]),
                html.Span(label, style={"color": color, "fontSize": "0.75rem", "fontWeight": "600"}),
            ],
        )

    apis = [
        ("Anthropic (Claude AI)", bool(ANTHROPIC_API_KEY)),
        ("SQLite Database", True),
        ("Slack Integration", False),
        ("HubSpot CRM", False),
        ("Google Workspace", False),
    ]

    items = []
    for name, connected in apis:
        color = COLORS["success"] if connected else COLORS["danger"]
        label = "Connected" if connected else "Not Configured"
        items.append(
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "8px 0", "borderBottom": f"1px solid rgba(45,52,54,0.3)"},
                children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                        html.Span(style={"width": "10px", "height": "10px", "borderRadius": "50%", "background": color, "flexShrink": "0", "boxShadow": f"0 0 6px {color}"}),
                        html.Span(name, style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    ]),
                    html.Span(label, style={"color": color, "fontSize": "0.75rem", "fontWeight": "600"}),
                ],
            )
        )
    return html.Div(items)


@callback(
    Output("revenue-financials", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_revenue(_):
    # Synthetic financial data
    mrr = 84000
    arr = mrr * 12
    mrr_growth = 34
    nrr = 125
    customers = 12
    avg_deal = 7000

    projected_q1 = 280000
    projected_q2 = 375000
    projected_annual = 1320000

    outstanding_invoices = [
        {"client": "Acme Corp", "amount": 18000, "due": "Mar 1, 2026", "status": "pending"},
        {"client": "NexGen Analytics", "amount": 12000, "due": "Mar 5, 2026", "status": "pending"},
        {"client": "TechFlow Inc", "amount": 8000, "due": "Feb 28, 2026", "status": "overdue"},
        {"client": "DataVault", "amount": 5500, "due": "Mar 10, 2026", "status": "pending"},
        {"client": "Meridian Group", "amount": 15000, "due": "Feb 15, 2026", "status": "overdue"},
    ]

    total_outstanding = sum(i["amount"] for i in outstanding_invoices)
    total_overdue = sum(i["amount"] for i in outstanding_invoices if i["status"] == "overdue")

    def _metric(label, value, subtitle=None, color=COLORS["text_primary"]):
        children = [
            html.P(label, style={"color": COLORS["text_muted"], "fontSize": "0.7rem", "margin": "0 0 4px 0", "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.P(value, style={"color": color, "fontSize": "1.3rem", "margin": 0, "fontWeight": "800"}),
        ]
        if subtitle:
            children.append(html.P(subtitle, style={"color": COLORS["text_muted"], "fontSize": "0.7rem", "margin": "2px 0 0 0"}))
        return html.Div(style={"textAlign": "center", "padding": "12px", "background": COLORS["body_bg"], "borderRadius": "8px"}, children=children)

    return html.Div([
        # Revenue metrics row
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "12px", "marginBottom": "20px"},
            children=[
                _metric("MRR", f"${mrr:,.0f}", f"+{mrr_growth}% QoQ", COLORS["success"]),
                _metric("ARR", f"${arr:,.0f}", f"{customers} customers"),
                _metric("Net Revenue Retention", f"{nrr}%", "target: >120%", COLORS["success"]),
                _metric("Avg Deal Size", f"${avg_deal:,.0f}", "/month"),
            ],
        ),
        # Projected income
        html.Div(
            style={"marginBottom": "20px"},
            children=[
                html.H4("Projected Income", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "marginBottom": "12px", "fontWeight": "600"}),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "12px"},
                    children=[
                        _metric("Q1 2026", f"${projected_q1:,.0f}", "current quarter"),
                        _metric("Q2 2026", f"${projected_q2:,.0f}", "+34% projected"),
                        _metric("FY 2026", f"${projected_annual / 1000:.0f}K", "annual target"),
                    ],
                ),
            ],
        ),
        # Outstanding invoices
        html.Div(children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"},
                children=[
                    html.H4("Outstanding Invoices", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "margin": 0, "fontWeight": "600"}),
                    html.Div(style={"display": "flex", "gap": "12px"}, children=[
                        html.Span(f"Total: ${total_outstanding:,.0f}", style={"color": COLORS["warning"], "fontSize": "0.8rem", "fontWeight": "600"}),
                        html.Span(f"Overdue: ${total_overdue:,.0f}", style={"color": COLORS["danger"], "fontSize": "0.8rem", "fontWeight": "600"}),
                    ]),
                ],
            ),
        ] + [
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "8px 0", "borderBottom": f"1px solid rgba(45,52,54,0.3)"},
                children=[
                    html.Div(children=[
                        html.Span(inv["client"], style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "600"}),
                        html.Span(f"  Due: {inv['due']}", style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "marginLeft": "8px"}),
                    ]),
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                        html.Span(
                            f"${inv['amount']:,.0f}",
                            style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "600"},
                        ),
                        html.Span(
                            inv["status"].upper(),
                            style={
                                "background": COLORS["danger"] if inv["status"] == "overdue" else COLORS["warning"],
                                "color": "#fff",
                                "padding": "2px 8px",
                                "borderRadius": "4px",
                                "fontSize": "0.65rem",
                                "fontWeight": "700",
                            },
                        ),
                    ]),
                ],
            )
            for inv in outstanding_invoices
        ]),
    ])


def _render_email_digest():
    emails = db.get_emails(10)
    if not emails:
        return html.P("No emails processed yet.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem"})

    items = []
    for e in emails:
        urgency_color = URGENCY_COLORS.get(e.get("urgency", "routine"), COLORS["text_muted"])
        items.append(
            html.Div(
                style={"padding": "10px 0", "borderBottom": f"1px solid {COLORS['border']}"},
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "4px"},
                        children=[
                            html.Span(
                                e.get("urgency", "routine").upper(),
                                style={"background": urgency_color, "color": "#fff", "padding": "1px 6px", "borderRadius": "3px", "fontSize": "0.65rem", "fontWeight": "600"},
                            ),
                            html.Span(e["subject"], style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "600"}),
                        ],
                    ),
                    html.P(
                        f"From: {e['sender']}",
                        style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "margin": "0 0 4px 0"},
                    ),
                    html.P(
                        e.get("processed_summary", ""),
                        style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "margin": 0, "lineHeight": "1.4"},
                    ),
                ],
            )
        )
    return html.Div(items)
