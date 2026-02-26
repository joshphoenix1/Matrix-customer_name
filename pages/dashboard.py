"""
Dashboard page — executive assistant daily briefing, KPIs, agenda, email digest, quick actions.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from datetime import date, datetime
from config import COLORS, COMPANY_NAME
import db
from components.kpi_card import kpi_card
from services.claude_client import generate_daily_priorities, generate_executive_plan

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
        dcc.Store(id="digest-task-trigger", data=0),

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

        # Daily Executive Plan
        html.Div(
            style={
                "background": f"linear-gradient(135deg, {COLORS['card_bg']} 0%, #1a1a3e 100%)",
                "borderRadius": "12px",
                "padding": "24px",
                "marginBottom": "24px",
                "borderLeft": f"4px solid {COLORS['warning']}",
                "position": "relative",
            },
            children=[
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "gap": "10px"},
                            children=[
                                html.I(className="bi bi-clipboard2-pulse", style={"color": COLORS["warning"], "fontSize": "1.2rem"}),
                                html.H3("Daily Executive Plan", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                            ],
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "6px"},
                            children=[
                                dbc.Button(
                                    [html.I(className="bi bi-stars", style={"marginRight": "6px"}), "Generate Plan"],
                                    id="btn-generate-exec-plan",
                                    size="sm",
                                    style={"fontSize": "0.75rem", "background": COLORS["warning"], "border": "none", "color": "#1a1a2e", "fontWeight": "700"},
                                ),
                                dbc.Button(
                                    [html.I(className="bi bi-x-lg")],
                                    id="btn-dismiss-exec-plan",
                                    size="sm",
                                    outline=True,
                                    color="secondary",
                                    style={"fontSize": "0.75rem"},
                                    title="Dismiss plan",
                                ),
                            ],
                        ),
                    ],
                ),
                dcc.Loading(
                    id="exec-plan-loading",
                    type="dot",
                    color=COLORS["warning"],
                    children=[html.Div(id="exec-plan-content")],
                ),
            ],
            id="exec-plan-card",
        ),
        # Show-again button for exec plan
        dbc.Collapse(
            id="exec-plan-show-collapse",
            is_open=False,
            children=[
                html.Div(
                    style={"marginBottom": "24px"},
                    children=[
                        dbc.Button(
                            [html.I(className="bi bi-clipboard2-pulse", style={"marginRight": "6px"}), "Show Executive Plan"],
                            id="btn-show-exec-plan",
                            size="sm",
                            outline=True,
                            color="warning",
                            style={"fontSize": "0.8rem"},
                        ),
                    ],
                ),
            ],
        ),

        # Main grid: priorities + agenda / quick actions
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Daily Priorities card (wrapped in collapse for dismiss)
                        dbc.Collapse(
                            id="priorities-collapse",
                            is_open=True,
                            children=[
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
                                                html.Div(
                                                    style={"display": "flex", "gap": "6px"},
                                                    children=[
                                                        dbc.Button(
                                                            [html.I(className="bi bi-arrow-clockwise")],
                                                            id="btn-refresh-priorities",
                                                            size="sm",
                                                            outline=True,
                                                            color="light",
                                                            style={"fontSize": "0.75rem"},
                                                            title="Refresh priorities",
                                                        ),
                                                        dbc.Button(
                                                            [html.I(className="bi bi-x-lg")],
                                                            id="btn-dismiss-priorities",
                                                            size="sm",
                                                            outline=True,
                                                            color="secondary",
                                                            style={"fontSize": "0.75rem"},
                                                            title="Dismiss priorities",
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(id="daily-priorities-content"),
                                    ],
                                ),
                            ],
                        ),
                        # Show-again button (visible when priorities are dismissed)
                        dbc.Collapse(
                            id="priorities-show-collapse",
                            is_open=False,
                            children=[
                                html.Div(
                                    style={"marginBottom": "16px"},
                                    children=[
                                        dbc.Button(
                                            [html.I(className="bi bi-arrow-repeat", style={"marginRight": "6px"}), "Show Daily Priorities"],
                                            id="btn-show-priorities",
                                            size="sm",
                                            outline=True,
                                            color="light",
                                            style={"fontSize": "0.8rem"},
                                        ),
                                    ],
                                ),
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
                                            dbc.Button(
                                                [html.I(className="bi bi-arrow-clockwise", style={"marginRight": "8px"}), "Scan Inbox"],
                                                color="primary", size="sm", style={"width": "100%", "background": COLORS["accent"], "border": "none"},
                                            ),
                                            href="/emails",
                                        ),
                                        dcc.Link(
                                            dbc.Button(
                                                [html.I(className="bi bi-plus-lg", style={"marginRight": "8px"}), "New Task"],
                                                color="info", size="sm", outline=True, style={"width": "100%"},
                                            ),
                                            href="/tasks",
                                        ),
                                        dcc.Link(
                                            dbc.Button(
                                                [html.I(className="bi bi-calendar-event", style={"marginRight": "8px"}), "Log Meeting"],
                                                color="success", size="sm", outline=True, style={"width": "100%"},
                                            ),
                                            href="/meetings",
                                        ),
                                        dcc.Link(
                                            dbc.Button(
                                                [html.I(className="bi bi-chat-dots", style={"marginRight": "8px"}), "Chat with AI"],
                                                color="light", size="sm", outline=True, style={"width": "100%"},
                                            ),
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

        # Email digest section
        html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "24px",
                "borderLeft": f"4px solid {COLORS['info']}",
            },
            children=[
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"},
                    children=[
                        html.H3("Recent Email Digest", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        dcc.Link(
                            dbc.Button("View All Emails", size="sm", outline=True, color="light", style={"fontSize": "0.75rem"}),
                            href="/emails",
                        ),
                    ],
                ),
                html.Div(id="email-digest"),
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

URGENCY_TO_PRIORITY = {
    "critical": "critical",
    "important": "high",
    "routine": "medium",
    "fyi": "low",
}


@callback(
    Output("dashboard-greeting", "children"),
    Input("dashboard-refresh-trigger", "data"),
)
def update_greeting(_):
    user_name = db.get_setting("user_name", "")
    first_name = user_name.split()[0] if user_name else ""
    suffix = f", {first_name}" if first_name else ""
    return f"{_greeting()}{suffix}."


@callback(
    Output("kpi-row", "children"),
    Input("dashboard-refresh-trigger", "data"),
    Input("btn-refresh-priorities", "n_clicks"),
    Input("digest-task-trigger", "data"),
)
def update_kpis(*_):
    all_tasks = db.get_tasks()
    active = [t for t in all_tasks if t["status"] not in ("completed", "cancelled")]
    due_today = db.get_tasks_due_today()
    meetings_today = db.get_todays_meetings()
    emails = db.get_emails(limit=100)

    pending_drafts = db.get_pending_drafts_count()

    return [
        kpi_card("Open Tasks", len(active), f"{len(all_tasks)} total", COLORS["accent"]),
        kpi_card("Due Today", len(due_today), "tasks due", COLORS["warning"]),
        kpi_card("Meetings Today", len(meetings_today), "scheduled", COLORS["info"]),
        kpi_card("Emails Processed", len(emails), "total received", COLORS["success"]),
        kpi_card("Pending Drafts", pending_drafts, "to review", COLORS["danger"] if pending_drafts > 0 else COLORS["text_muted"]),
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


# ── Executive Plan: generate / dismiss / show ──

@callback(
    Output("exec-plan-content", "children"),
    Input("btn-generate-exec-plan", "n_clicks"),
    prevent_initial_call=True,
)
def generate_exec_plan(n_clicks):
    if not n_clicks:
        return no_update

    tasks = db.get_tasks()
    active_tasks = [t for t in tasks if t["status"] not in ("completed", "cancelled")]
    overdue_tasks = db.get_overdue_tasks()
    meetings = db.get_todays_meetings()
    emails = db.get_emails(10)

    if not active_tasks and not meetings and not emails:
        return html.P(
            "No data to build a plan from. Add tasks, log meetings, or scan emails first.",
            style={"color": COLORS["text_muted"], "fontSize": "0.9rem"},
        )

    plan = generate_executive_plan(active_tasks, meetings, emails, overdue_tasks)
    return dcc.Markdown(
        plan,
        style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.7"},
    )


@callback(
    Output("exec-plan-card", "style"),
    Output("exec-plan-show-collapse", "is_open"),
    Input("btn-dismiss-exec-plan", "n_clicks"),
    Input("btn-show-exec-plan", "n_clicks"),
    State("exec-plan-card", "style"),
    prevent_initial_call=True,
)
def toggle_exec_plan(dismiss_clicks, show_clicks, current_style):
    trigger = ctx.triggered_id
    base_style = {
        "background": f"linear-gradient(135deg, {COLORS['card_bg']} 0%, #1a1a3e 100%)",
        "borderRadius": "12px",
        "padding": "24px",
        "marginBottom": "24px",
        "borderLeft": f"4px solid {COLORS['warning']}",
        "position": "relative",
    }
    if trigger == "btn-dismiss-exec-plan":
        return {**base_style, "display": "none"}, True
    if trigger == "btn-show-exec-plan":
        return {**base_style, "display": "block"}, False
    return current_style, False


# ── Priorities: dismiss / show ──

@callback(
    Output("priorities-collapse", "is_open"),
    Output("priorities-show-collapse", "is_open"),
    Input("btn-dismiss-priorities", "n_clicks"),
    Input("btn-show-priorities", "n_clicks"),
    State("priorities-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_priorities(dismiss_clicks, show_clicks, is_open):
    trigger = ctx.triggered_id
    if trigger == "btn-dismiss-priorities":
        return False, True
    if trigger == "btn-show-priorities":
        return True, False
    return is_open, not is_open


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

    briefing = generate_daily_priorities(active_tasks, meetings, emails)
    return dcc.Markdown(
        briefing,
        style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.6"},
    )


# ── Email digest with "Add to Tasks" ──

@callback(
    Output("email-digest", "children"),
    Input("dashboard-refresh-trigger", "data"),
    Input("digest-task-trigger", "data"),
)
def update_digest(*_):
    return _render_email_digest()


@callback(
    Output("digest-task-trigger", "data"),
    Input({"type": "digest-add-task", "index": ALL}, "n_clicks"),
    State("digest-task-trigger", "data"),
    prevent_initial_call=True,
)
def add_email_to_tasks(n_clicks_list, current_trigger):
    if not ctx.triggered_id or not any(n_clicks_list):
        return no_update

    email_id = ctx.triggered_id["index"]
    emails = db.get_emails(50)
    email_data = next((e for e in emails if e["id"] == email_id), None)
    if not email_data:
        return no_update

    urgency = email_data.get("urgency", "routine")
    priority = URGENCY_TO_PRIORITY.get(urgency, "medium")
    summary = email_data.get("processed_summary", "")

    db.create_task(
        title=f"[Email] {email_data['subject'][:80]}",
        description=f"From: {email_data['sender']}\n\n{summary}",
        priority=priority,
    )

    return (current_trigger or 0) + 1


def _render_email_digest():
    emails = db.get_emails(10)
    if not emails:
        return html.P("No emails processed yet. Go to Emails and click Scan Inbox.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem"})

    # Get existing task titles to check for duplicates
    existing_tasks = db.get_tasks()
    existing_titles = {t["title"] for t in existing_tasks}

    items = []
    for e in emails:
        urgency_color = URGENCY_COLORS.get(e.get("urgency", "routine"), COLORS["text_muted"])
        task_title = f"[Email] {e['subject'][:80]}"
        already_added = task_title in existing_titles

        items.append(
            html.Div(
                style={"padding": "10px 0", "borderBottom": f"1px solid {COLORS['border']}"},
                children=[
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "gap": "12px"},
                        children=[
                            # Left: email info
                            html.Div(
                                style={"flex": "1", "minWidth": 0},
                                children=[
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "4px"},
                                        children=[
                                            html.Span(
                                                e.get("urgency", "routine").upper(),
                                                style={"background": urgency_color, "color": "#fff", "padding": "1px 6px", "borderRadius": "3px", "fontSize": "0.65rem", "fontWeight": "600", "flexShrink": "0"},
                                            ),
                                            html.Span(e["subject"], style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "600", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),
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
                            ),
                            # Right: add-to-tasks button
                            html.Div(
                                style={"flexShrink": "0", "paddingTop": "2px"},
                                children=[
                                    html.Span(
                                        [html.I(className="bi bi-check-lg", style={"marginRight": "4px"}), "Added"],
                                        style={"color": COLORS["success"], "fontSize": "0.75rem", "fontWeight": "600"},
                                    ) if already_added else
                                    dbc.Button(
                                        [html.I(className="bi bi-plus-circle", style={"marginRight": "4px"}), "Task"],
                                        id={"type": "digest-add-task", "index": e["id"]},
                                        size="sm",
                                        outline=True,
                                        color="light",
                                        style={"fontSize": "0.7rem", "padding": "2px 8px", "whiteSpace": "nowrap"},
                                        title="Add to tasks",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        )
    return html.Div(items)
