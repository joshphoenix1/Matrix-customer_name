"""
Meetings page — meeting notes, AI summarization, action item extraction.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from datetime import date
from config import COLORS
import db
from services.claude_client import summarize_meeting

dash.register_page(__name__, path="/meetings", name="Meetings", order=4)

# ── Layout ──

layout = html.Div(
    children=[
        dcc.Store(id="meetings-selected-id"),
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div(
                    children=[
                        html.H2("Meeting Notes", style={"color": COLORS["text_primary"], "margin": 0}),
                        html.P("Log meetings, get AI summaries, and extract action items.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"}),
                    ]
                ),
                dbc.Button(
                    [html.I(className="bi bi-plus-lg", style={"marginRight": "8px"}), "New Meeting"],
                    id="btn-open-meeting-form",
                    color="primary",
                    style={"background": COLORS["accent"], "border": "none"},
                ),
            ],
        ),
        # New meeting form
        dbc.Collapse(
            id="meeting-form-collapse",
            is_open=False,
            children=[
                html.Div(
                    style={
                        "background": COLORS["card_bg"],
                        "borderRadius": "12px",
                        "padding": "24px",
                        "marginBottom": "24px",
                        "borderLeft": f"4px solid {COLORS['accent']}",
                    },
                    children=[
                        html.H4("New Meeting", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Title", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                        dbc.Input(id="meeting-title", placeholder="Meeting title...", style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]}),
                                    ],
                                    md=8,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Date", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                        dbc.Input(id="meeting-date", type="date", value=date.today().isoformat(), style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]}),
                                    ],
                                    md=4,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Label("Meeting Notes", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                        dbc.Textarea(
                            id="meeting-notes",
                            placeholder="Paste your meeting notes here...\n\nInclude key discussion points, decisions, and any action items mentioned.",
                            style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "minHeight": "200px"},
                            className="mb-3",
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "8px"},
                            children=[
                                dbc.Button("Save Meeting", id="btn-save-meeting", color="success", style={"background": COLORS["success"], "border": "none"}),
                                dbc.Button("Cancel", id="btn-cancel-meeting", outline=True, color="secondary"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Meeting list
        html.Div(id="meeting-list"),
        # Meeting detail / summary view
        html.Div(id="meeting-detail"),
    ]
)


# ── Callbacks ──

@callback(
    Output("meeting-form-collapse", "is_open"),
    Input("btn-open-meeting-form", "n_clicks"),
    Input("btn-cancel-meeting", "n_clicks"),
    Input("btn-save-meeting", "n_clicks"),
    State("meeting-form-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_meeting_form(open_clicks, cancel_clicks, save_clicks, is_open):
    trigger = ctx.triggered_id
    if trigger == "btn-open-meeting-form":
        return True
    return False


@callback(
    Output("meeting-title", "value"),
    Output("meeting-notes", "value"),
    Output("meeting-list", "children", allow_duplicate=True),
    Input("btn-save-meeting", "n_clicks"),
    State("meeting-title", "value"),
    State("meeting-date", "value"),
    State("meeting-notes", "value"),
    prevent_initial_call=True,
)
def save_meeting(n, title, meeting_date, notes):
    if not n or not title or not title.strip():
        return no_update, no_update, no_update
    db.save_meeting(
        title=title.strip(),
        meeting_date=meeting_date or date.today().isoformat(),
        raw_notes=(notes or "").strip(),
    )
    return "", "", _render_meeting_list()


@callback(
    Output("meeting-list", "children"),
    Input("meetings-selected-id", "data"),
)
def refresh_meetings(_):
    return _render_meeting_list()


@callback(
    Output("meeting-detail", "children"),
    Output("meetings-selected-id", "data"),
    Input({"type": "meeting-view-btn", "index": dash.ALL}, "n_clicks"),
    Input({"type": "meeting-summarize-btn", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def meeting_actions(view_clicks, summarize_clicks):
    if not ctx.triggered_id:
        return no_update, no_update

    meeting_id = ctx.triggered_id["index"]
    action_type = ctx.triggered_id["type"]

    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return html.P("Meeting not found.", style={"color": COLORS["danger"]}), no_update

    # Handle summarize
    if action_type == "meeting-summarize-btn":
        if meeting["raw_notes"]:
            result = summarize_meeting(meeting["raw_notes"])
            summary_text = result.get("summary", "No summary generated.")
            decisions = result.get("key_decisions", [])
            action_items = result.get("action_items", [])

            # Build full summary for storage
            full_summary = f"**Summary:** {summary_text}\n\n"
            if decisions:
                full_summary += "**Key Decisions:**\n"
                for d in decisions:
                    full_summary += f"- {d}\n"
                full_summary += "\n"
            if action_items:
                full_summary += "**Action Items:**\n"
                for ai in action_items:
                    owner = f" ({ai.get('owner', '')})" if ai.get("owner") else ""
                    due = f" — due {ai['due_date']}" if ai.get("due_date") else ""
                    full_summary += f"- {ai['description']}{owner}{due}\n"

            db.update_meeting_summary(meeting_id, full_summary)

            # Create tasks from action items
            for ai in action_items:
                task_id = db.create_task(
                    title=ai["description"][:100],
                    description=f"From meeting: {meeting['title']}\n{ai['description']}",
                    priority="high",
                    due_date=ai.get("due_date"),
                )
                db.save_action_item(
                    meeting_id=meeting_id,
                    description=ai["description"],
                    owner=ai.get("owner", ""),
                    due_date=ai.get("due_date"),
                    task_id=task_id,
                )

            meeting = db.get_meeting(meeting_id)

    return _render_meeting_detail(meeting), meeting_id


def _render_meeting_list():
    meetings = db.get_meetings()
    if not meetings:
        return html.Div(
            style={"textAlign": "center", "padding": "48px", "background": COLORS["card_bg"], "borderRadius": "12px"},
            children=[
                html.P("No meetings recorded.", style={"color": COLORS["text_muted"], "fontSize": "1rem", "marginBottom": "8px"}),
                html.P("Click 'New Meeting' to log your first meeting.", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
            ],
        )

    items = []
    for m in meetings:
        has_summary = bool(m.get("ai_summary"))
        items.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "16px 20px",
                    "marginBottom": "8px",
                    "borderLeft": f"4px solid {COLORS['success'] if has_summary else COLORS['border']}",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
                children=[
                    html.Div(
                        children=[
                            html.H4(m["title"], style={"color": COLORS["text_primary"], "margin": "0 0 4px 0", "fontSize": "0.95rem"}),
                            html.Span(m["date"], style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
                            html.Span(
                                " — AI Summary Available" if has_summary else "",
                                style={"color": COLORS["success"], "fontSize": "0.8rem", "marginLeft": "8px"},
                            ) if has_summary else None,
                        ]
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px"},
                        children=[
                            dbc.Button(
                                "View",
                                id={"type": "meeting-view-btn", "index": m["id"]},
                                size="sm",
                                outline=True,
                                color="light",
                                style={"fontSize": "0.75rem"},
                            ),
                            dbc.Button(
                                "Summarize with AI",
                                id={"type": "meeting-summarize-btn", "index": m["id"]},
                                size="sm",
                                color="primary",
                                style={"fontSize": "0.75rem", "background": COLORS["accent"], "border": "none"},
                            ) if not has_summary and m.get("raw_notes") else None,
                        ],
                    ),
                ],
            )
        )
    return html.Div(items)


def _render_meeting_detail(meeting):
    if not meeting:
        return None

    children = [
        html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "24px",
                "marginTop": "24px",
                "borderLeft": f"4px solid {COLORS['accent']}",
            },
            children=[
                html.H3(meeting["title"], style={"color": COLORS["text_primary"], "marginBottom": "8px"}),
                html.P(f"Date: {meeting['date']}", style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"}),
            ] + (
                [
                    html.H4("Raw Notes", style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "marginBottom": "8px"}),
                    html.Pre(
                        meeting["raw_notes"],
                        style={
                            "color": COLORS["text_secondary"],
                            "background": COLORS["body_bg"],
                            "padding": "16px",
                            "borderRadius": "8px",
                            "whiteSpace": "pre-wrap",
                            "fontSize": "0.85rem",
                            "marginBottom": "20px",
                        },
                    ),
                ] if meeting.get("raw_notes") else []
            ) + (
                [
                    html.Hr(style={"borderColor": COLORS["border"]}),
                    html.H4("AI Summary", style={"color": COLORS["success"], "fontSize": "0.9rem", "marginBottom": "8px"}),
                    dcc.Markdown(
                        meeting["ai_summary"],
                        style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.6"},
                    ),
                ] if meeting.get("ai_summary") else []
            ),
        ),
    ]

    action_items = db.get_action_items(meeting["id"])
    if action_items:
        children.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginTop": "16px",
                    "borderLeft": f"4px solid {COLORS['warning']}",
                },
                children=[
                    html.H4("Action Items", style={"color": COLORS["warning"], "marginBottom": "12px"}),
                ] + [
                    html.Div(
                        style={"padding": "8px 0", "borderBottom": f"1px solid {COLORS['border']}"},
                        children=[
                            html.Span(ai["description"], style={"color": COLORS["text_primary"], "fontSize": "0.9rem"}),
                            html.Span(
                                f" — {ai['owner']}" if ai.get("owner") else "",
                                style={"color": COLORS["text_muted"], "fontSize": "0.85rem"},
                            ),
                            html.Span(
                                f" (due {ai['due_date']})" if ai.get("due_date") else "",
                                style={"color": COLORS["text_muted"], "fontSize": "0.85rem"},
                            ),
                            html.Span(
                                " — Task created",
                                style={"color": COLORS["success"], "fontSize": "0.8rem", "marginLeft": "8px"},
                            ) if ai.get("task_id") else None,
                        ],
                    )
                    for ai in action_items
                ],
            )
        )

    return html.Div(children)
