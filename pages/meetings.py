"""
Meetings page — monthly calendar grid (top), meeting detail + AI summarize (bottom).
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from datetime import date, datetime
import calendar
from config import COLORS
import db
from services.claude_client import summarize_meeting

dash.register_page(__name__, path="/meetings", name="Meetings", order=4)


def _today_str():
    return date.today().isoformat()


def _build_calendar_grid(year, month, meetings_by_day, selected_date, today):
    """Build a 7-column CSS grid calendar for the given month."""
    cal = calendar.monthcalendar(year, month)

    # Day-of-week header
    header_cells = []
    for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        header_cells.append(
            html.Div(day_name, style={
                "textAlign": "center", "color": COLORS["text_muted"],
                "fontSize": "0.7rem", "fontWeight": "700", "padding": "6px 0",
                "textTransform": "uppercase", "letterSpacing": "1px",
            })
        )

    # Day cells
    day_cells = []
    for week in cal:
        for day in week:
            if day == 0:
                day_cells.append(html.Div(style={"padding": "8px", "minHeight": "48px"}))
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                meeting_count = meetings_by_day.get(day, 0)
                is_today = date_str == today
                is_selected = date_str == selected_date

                # Style
                cell_style = {
                    "textAlign": "center", "padding": "6px 4px", "minHeight": "48px",
                    "borderRadius": "8px", "cursor": "pointer",
                    "display": "flex", "flexDirection": "column",
                    "alignItems": "center", "justifyContent": "center",
                    "transition": "background 0.15s",
                }
                if is_selected:
                    cell_style["background"] = COLORS["accent"]
                    cell_style["color"] = "#fff"
                elif is_today:
                    cell_style["border"] = f"2px solid {COLORS['accent']}"

                children = [
                    html.Span(str(day), style={
                        "fontSize": "0.85rem", "fontWeight": "600",
                        "color": "#fff" if is_selected else COLORS["text_primary"],
                    }),
                ]
                if meeting_count > 0:
                    children.append(
                        html.Div(style={
                            "display": "flex", "alignItems": "center", "gap": "4px", "marginTop": "2px",
                        }, children=[
                            html.Div(style={
                                "width": "6px", "height": "6px", "borderRadius": "50%",
                                "background": COLORS["success"] if not is_selected else "#fff",
                            }),
                            html.Span(str(meeting_count), style={
                                "fontSize": "0.6rem",
                                "color": "#fff" if is_selected else COLORS["success"],
                            }),
                        ])
                    )

                day_cells.append(
                    html.Button(
                        children=children,
                        id={"type": "cal-day", "index": day},
                        n_clicks=0,
                        style={**cell_style, "border": cell_style.get("border", "none"),
                               "background": cell_style.get("background", "transparent")},
                    )
                )

    return html.Div(children=[
        html.Div(header_cells, style={
            "display": "grid", "gridTemplateColumns": "repeat(7, 1fr)", "gap": "2px",
        }),
        html.Div(day_cells, style={
            "display": "grid", "gridTemplateColumns": "repeat(7, 1fr)", "gap": "2px",
        }),
    ])


# ── Layout ──

layout = html.Div(children=[
    dcc.Store(id="cal-year-month", data={"year": date.today().year, "month": date.today().month}),
    dcc.Store(id="cal-selected-date", data=_today_str()),
    dcc.Store(id="meetings-selected-id"),
    dcc.Store(id="meetings-refresh", data=0),

    # ── Top Half: Calendar ──
    html.Div(style={
        "maxHeight": "calc(50vh - 120px)", "overflowY": "auto",
        "marginBottom": "16px",
    }, children=[
        # Header row
        html.Div(style={
            "display": "flex", "justifyContent": "space-between", "alignItems": "center",
            "marginBottom": "16px",
        }, children=[
            html.Div(children=[
                html.H2("Meetings", style={"color": COLORS["text_primary"], "margin": 0}),
                html.P("Calendar view with AI-powered summaries.", style={
                    "color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0",
                }),
            ]),
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                dbc.Button(
                    html.I(className="bi bi-chevron-left"),
                    id="cal-prev-month", size="sm", outline=True, color="light",
                    style={"padding": "4px 10px"},
                ),
                html.Span(id="cal-month-label", style={
                    "color": COLORS["text_primary"], "fontSize": "1rem", "fontWeight": "700",
                    "minWidth": "140px", "textAlign": "center",
                }),
                dbc.Button(
                    html.I(className="bi bi-chevron-right"),
                    id="cal-next-month", size="sm", outline=True, color="light",
                    style={"padding": "4px 10px"},
                ),
                dbc.Button(
                    [html.I(className="bi bi-plus-lg", style={"marginRight": "8px"}), "New Meeting"],
                    id="btn-open-meeting-form", color="primary",
                    style={"background": COLORS["accent"], "border": "none", "marginLeft": "8px"},
                ),
            ]),
        ]),
        # Calendar grid
        html.Div(id="cal-grid", style={
            "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "16px",
        }),
    ]),

    # ── Bottom Half: Detail ──
    html.Div(style={"minHeight": "calc(50vh - 120px)"}, children=[
        # New meeting form (collapsible)
        dbc.Collapse(id="meeting-form-collapse", is_open=False, children=[
            html.Div(style={
                "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
                "marginBottom": "16px", "borderLeft": f"4px solid {COLORS['accent']}",
            }, children=[
                html.H4("New Meeting", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Title", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                        dbc.Input(id="meeting-title", placeholder="Meeting title...", style={
                            "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                            "color": COLORS["text_primary"],
                        }),
                    ], md=8),
                    dbc.Col([
                        dbc.Label("Date", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                        dbc.Input(id="meeting-date", type="date", value=_today_str(), style={
                            "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                            "color": COLORS["text_primary"],
                        }),
                    ], md=4),
                ], className="mb-3"),
                dbc.Label("Meeting Notes", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                dbc.Textarea(
                    id="meeting-notes",
                    placeholder="Paste your meeting notes here...\n\nInclude key discussion points, decisions, and any action items mentioned.",
                    style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"], "minHeight": "150px",
                    },
                    className="mb-3",
                ),
                html.Div(style={"display": "flex", "gap": "8px"}, children=[
                    dbc.Button("Save Meeting", id="btn-save-meeting", color="success", style={
                        "background": COLORS["success"], "border": "none",
                    }),
                    dbc.Button("Cancel", id="btn-cancel-meeting", outline=True, color="secondary"),
                ]),
            ]),
        ]),

        # Day meetings list
        html.Div(id="day-meetings-list"),

        # Meeting detail panel
        html.Div(id="meeting-detail"),
    ]),
])


# ── Callbacks ──

# 1. Navigate month
@callback(
    Output("cal-year-month", "data"),
    Input("cal-prev-month", "n_clicks"),
    Input("cal-next-month", "n_clicks"),
    State("cal-year-month", "data"),
    prevent_initial_call=True,
)
def navigate_month(prev_n, next_n, ym):
    year, month = ym["year"], ym["month"]
    if ctx.triggered_id == "cal-prev-month":
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    else:
        month += 1
        if month > 12:
            month = 1
            year += 1
    return {"year": year, "month": month}


# 2. Render calendar grid + month label
@callback(
    Output("cal-grid", "children"),
    Output("cal-month-label", "children"),
    Input("cal-year-month", "data"),
    Input("cal-selected-date", "data"),
    Input("meetings-refresh", "data"),
)
def render_calendar(ym, selected_date, _):
    year, month = ym["year"], ym["month"]
    meetings = db.get_meetings_for_month(year, month)

    # Count meetings per day
    meetings_by_day = {}
    for m in meetings:
        try:
            day = int(m["date"].split("-")[2])
            meetings_by_day[day] = meetings_by_day.get(day, 0) + 1
        except (IndexError, ValueError):
            pass

    today = _today_str()
    grid = _build_calendar_grid(year, month, meetings_by_day, selected_date, today)
    month_name = calendar.month_name[month]
    label = f"{month_name} {year}"
    return grid, label


# 3. Select day
@callback(
    Output("cal-selected-date", "data"),
    Input({"type": "cal-day", "index": ALL}, "n_clicks"),
    State("cal-year-month", "data"),
    prevent_initial_call=True,
)
def select_day(n_clicks_list, ym):
    if not ctx.triggered_id or not any(n for n in n_clicks_list if n):
        return no_update
    day = ctx.triggered_id["index"]
    year, month = ym["year"], ym["month"]
    return f"{year}-{month:02d}-{day:02d}"


# 4. Render day meetings
@callback(
    Output("day-meetings-list", "children"),
    Input("cal-selected-date", "data"),
    Input("meetings-refresh", "data"),
)
def render_day_meetings(selected_date, _):
    if not selected_date:
        return None

    meetings = db.get_meetings_for_date(selected_date)

    header = html.Div(style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "marginBottom": "12px",
    }, children=[
        html.H4(f"Meetings on {selected_date}", style={
            "color": COLORS["text_primary"], "margin": 0, "fontSize": "1rem",
        }),
        html.Span(f"{len(meetings)} meeting{'s' if len(meetings) != 1 else ''}", style={
            "color": COLORS["text_muted"], "fontSize": "0.85rem",
        }),
    ])

    if not meetings:
        return html.Div(style={
            "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "20px",
            "marginBottom": "16px",
        }, children=[
            header,
            html.P("No meetings on this date.", style={
                "color": COLORS["text_muted"], "fontSize": "0.9rem", "textAlign": "center", "padding": "16px",
            }),
        ])

    items = []
    for m in meetings:
        has_summary = bool(m.get("ai_summary"))
        items.append(
            html.Div(style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "12px 0", "borderBottom": f"1px solid {COLORS['border']}",
            }, children=[
                html.Div(children=[
                    html.Span(m["title"], style={
                        "color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600",
                    }),
                    html.Span(
                        " — AI Summary Available" if has_summary else "",
                        style={"color": COLORS["success"], "fontSize": "0.8rem", "marginLeft": "8px"},
                    ) if has_summary else None,
                ]),
                html.Div(style={"display": "flex", "gap": "8px"}, children=[
                    dbc.Button("View", id={"type": "meeting-view-btn", "index": m["id"]},
                               size="sm", outline=True, color="light", style={"fontSize": "0.75rem"}),
                    dbc.Button("Summarize with AI", id={"type": "meeting-summarize-btn", "index": m["id"]},
                               size="sm", color="primary",
                               style={"fontSize": "0.75rem", "background": COLORS["accent"], "border": "none"},
                    ) if not has_summary and m.get("raw_notes") else None,
                ]),
            ])
        )

    return html.Div(style={
        "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "20px",
        "marginBottom": "16px",
    }, children=[header] + items)


# 5. Toggle meeting form
@callback(
    Output("meeting-form-collapse", "is_open"),
    Output("meeting-date", "value"),
    Input("btn-open-meeting-form", "n_clicks"),
    Input("btn-cancel-meeting", "n_clicks"),
    Input("btn-save-meeting", "n_clicks"),
    State("meeting-form-collapse", "is_open"),
    State("cal-selected-date", "data"),
    prevent_initial_call=True,
)
def toggle_meeting_form(open_n, cancel_n, save_n, is_open, selected_date):
    trigger = ctx.triggered_id
    if trigger == "btn-open-meeting-form":
        return True, selected_date or _today_str()
    return False, no_update


# 6. Save meeting
@callback(
    Output("meeting-title", "value"),
    Output("meeting-notes", "value"),
    Output("meetings-refresh", "data"),
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
        meeting_date=meeting_date or _today_str(),
        raw_notes=(notes or "").strip(),
    )
    return "", "", datetime.now().timestamp()


# 7. Meeting detail actions (view / summarize)
@callback(
    Output("meeting-detail", "children"),
    Output("meetings-selected-id", "data"),
    Input({"type": "meeting-view-btn", "index": ALL}, "n_clicks"),
    Input({"type": "meeting-summarize-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def meeting_detail_actions(view_clicks, summarize_clicks):
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


def _render_meeting_detail(meeting):
    if not meeting:
        return None

    children = [
        html.Div(style={
            "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
            "borderLeft": f"4px solid {COLORS['accent']}",
        }, children=[
            html.H3(meeting["title"], style={"color": COLORS["text_primary"], "marginBottom": "8px"}),
            html.P(f"Date: {meeting['date']}", style={
                "color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px",
            }),
        ] + (
            [
                html.H4("Raw Notes", style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "marginBottom": "8px"}),
                html.Pre(meeting["raw_notes"], style={
                    "color": COLORS["text_secondary"], "background": COLORS["body_bg"],
                    "padding": "16px", "borderRadius": "8px", "whiteSpace": "pre-wrap",
                    "fontSize": "0.85rem", "marginBottom": "20px",
                }),
            ] if meeting.get("raw_notes") else []
        ) + (
            [
                html.Hr(style={"borderColor": COLORS["border"]}),
                html.H4("AI Summary", style={"color": COLORS["success"], "fontSize": "0.9rem", "marginBottom": "8px"}),
                dcc.Markdown(meeting["ai_summary"], style={
                    "color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.6",
                }),
            ] if meeting.get("ai_summary") else []
        )),
    ]

    action_items = db.get_action_items(meeting["id"])
    if action_items:
        children.append(
            html.Div(style={
                "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
                "marginTop": "16px", "borderLeft": f"4px solid {COLORS['warning']}",
            }, children=[
                html.H4("Action Items", style={"color": COLORS["warning"], "marginBottom": "12px"}),
            ] + [
                html.Div(style={
                    "padding": "8px 0", "borderBottom": f"1px solid {COLORS['border']}",
                }, children=[
                    html.Span(ai["description"], style={"color": COLORS["text_primary"], "fontSize": "0.9rem"}),
                    html.Span(f" — {ai['owner']}" if ai.get("owner") else "", style={
                        "color": COLORS["text_muted"], "fontSize": "0.85rem",
                    }),
                    html.Span(f" (due {ai['due_date']})" if ai.get("due_date") else "", style={
                        "color": COLORS["text_muted"], "fontSize": "0.85rem",
                    }),
                    html.Span(" — Task created", style={
                        "color": COLORS["success"], "fontSize": "0.8rem", "marginLeft": "8px",
                    }) if ai.get("task_id") else None,
                ])
                for ai in action_items
            ])
        )

    return html.Div(children)
