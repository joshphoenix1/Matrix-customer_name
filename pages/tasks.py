"""
Tasks page — task board with create, track, and accountability features.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from datetime import date
from config import COLORS
import db

dash.register_page(__name__, path="/tasks", name="Tasks", order=3)

PRIORITY_COLORS = {
    "critical": COLORS["danger"],
    "high": "#E17055",
    "medium": COLORS["warning"],
    "low": COLORS["info"],
}

STATUS_LABELS = {
    "pending": ("Pending", COLORS["text_muted"]),
    "in_progress": ("In Progress", COLORS["info"]),
    "completed": ("Done", COLORS["success"]),
    "cancelled": ("Cancelled", COLORS["danger"]),
}


def _task_card(task):
    """Render a single task card inline."""
    priority_color = PRIORITY_COLORS.get(task["priority"], COLORS["text_muted"])
    status_label, status_color = STATUS_LABELS.get(task["status"], ("Unknown", COLORS["text_muted"]))

    due_text = ""
    if task.get("due_date"):
        due_text = f"Due: {task['due_date']}"

    return html.Div(
        style={
            "background": COLORS["card_bg"],
            "borderRadius": "12px",
            "padding": "16px 20px",
            "marginBottom": "8px",
            "borderLeft": f"4px solid {priority_color}",
        },
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"},
                children=[
                    html.H4(
                        task["title"],
                        style={
                            "color": COLORS["text_primary"],
                            "margin": 0,
                            "fontSize": "0.95rem",
                            "fontWeight": "600",
                            "textDecoration": "line-through" if task["status"] == "completed" else "none",
                        },
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px", "alignItems": "center"},
                        children=[
                            html.Span(
                                task["priority"].upper(),
                                style={
                                    "background": priority_color,
                                    "color": "#fff",
                                    "padding": "2px 8px",
                                    "borderRadius": "4px",
                                    "fontSize": "0.7rem",
                                    "fontWeight": "600",
                                },
                            ),
                            html.Span(
                                status_label,
                                style={
                                    "border": f"1px solid {status_color}",
                                    "color": status_color,
                                    "padding": "2px 8px",
                                    "borderRadius": "4px",
                                    "fontSize": "0.7rem",
                                    "fontWeight": "600",
                                },
                            ),
                        ],
                    ),
                ],
            ),
            html.P(
                task.get("description", ""),
                style={
                    "color": COLORS["text_secondary"],
                    "fontSize": "0.85rem",
                    "margin": "0 0 6px 0",
                    "lineHeight": "1.4",
                },
            ) if task.get("description") else None,
            html.Span(
                due_text,
                style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
            ) if due_text else None,
        ],
    )


# ── Layout ──

layout = html.Div(
    children=[
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div(
                    children=[
                        html.H2("Task Board", style={"color": COLORS["text_primary"], "margin": 0}),
                        html.P("Track priorities and accountability.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"}),
                    ]
                ),
                dbc.Button(
                    [html.I(className="bi bi-plus-lg", style={"marginRight": "8px"}), "Add Task"],
                    id="btn-open-task-form",
                    color="primary",
                    style={"background": COLORS["accent"], "border": "none"},
                ),
            ],
        ),
        # Filter bar
        html.Div(
            style={"display": "flex", "gap": "8px", "marginBottom": "24px", "flexWrap": "wrap"},
            children=[
                dbc.ButtonGroup(
                    [
                        dbc.Button("All", id="filter-all", outline=True, color="light", size="sm", active=True),
                        dbc.Button("Today", id="filter-today", outline=True, color="light", size="sm"),
                        dbc.Button("Overdue", id="filter-overdue", outline=True, color="danger", size="sm"),
                        dbc.Button("Critical", id="filter-critical", outline=True, color="warning", size="sm"),
                        dbc.Button("Completed", id="filter-completed", outline=True, color="success", size="sm"),
                    ]
                ),
            ],
        ),
        dcc.Store(id="task-filter", data="all"),
        # Task create form (collapsible)
        dbc.Collapse(
            id="task-form-collapse",
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
                        html.H4("New Task", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Title", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                        dbc.Input(id="task-title", placeholder="Task title...", style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]}),
                                    ],
                                    md=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Priority", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                        dbc.Select(
                                            id="task-priority",
                                            options=[
                                                {"label": "Critical", "value": "critical"},
                                                {"label": "High", "value": "high"},
                                                {"label": "Medium", "value": "medium"},
                                                {"label": "Low", "value": "low"},
                                            ],
                                            value="medium",
                                            style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]},
                                        ),
                                    ],
                                    md=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Due Date", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                        dbc.Input(id="task-due-date", type="date", style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"]}),
                                    ],
                                    md=3,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Description", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                        dbc.Textarea(id="task-description", placeholder="Task description...", style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "minHeight": "80px"}),
                                    ],
                                    md=12,
                                ),
                            ],
                            className="mb-3",
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "8px"},
                            children=[
                                dbc.Button("Create Task", id="btn-create-task", color="success", style={"background": COLORS["success"], "border": "none"}),
                                dbc.Button("Cancel", id="btn-cancel-task", outline=True, color="secondary"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Task list
        html.Div(id="task-list"),
    ]
)


# ── Callbacks ──

@callback(
    Output("task-form-collapse", "is_open"),
    Input("btn-open-task-form", "n_clicks"),
    Input("btn-cancel-task", "n_clicks"),
    Input("btn-create-task", "n_clicks"),
    State("task-form-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_form(open_clicks, cancel_clicks, create_clicks, is_open):
    trigger = ctx.triggered_id
    if trigger == "btn-open-task-form":
        return True
    return False


@callback(
    Output("task-filter", "data"),
    Input("filter-all", "n_clicks"),
    Input("filter-today", "n_clicks"),
    Input("filter-overdue", "n_clicks"),
    Input("filter-critical", "n_clicks"),
    Input("filter-completed", "n_clicks"),
    prevent_initial_call=True,
)
def set_filter(*_):
    trigger = ctx.triggered_id
    filter_map = {
        "filter-all": "all",
        "filter-today": "today",
        "filter-overdue": "overdue",
        "filter-critical": "critical",
        "filter-completed": "completed",
    }
    return filter_map.get(trigger, "all")


@callback(
    Output("task-list", "children"),
    Input("task-filter", "data"),
    Input("btn-create-task", "n_clicks"),
    Input({"type": "task-status-btn", "index": ALL, "action": ALL}, "n_clicks"),
)
def render_tasks(filter_val, create_clicks, status_clicks):
    # Handle status change
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "task-status-btn":
        task_id = ctx.triggered_id["index"]
        action = ctx.triggered_id["action"]
        status_map = {
            "start": "in_progress",
            "complete": "completed",
            "cancel": "cancelled",
            "reopen": "pending",
        }
        if action in status_map:
            db.update_task(task_id, status=status_map[action])

    # Apply filter
    if filter_val == "today":
        tasks = db.get_tasks_due_today()
    elif filter_val == "overdue":
        tasks = db.get_overdue_tasks()
    elif filter_val == "critical":
        tasks = db.get_tasks(priority="critical")
    elif filter_val == "completed":
        tasks = db.get_tasks(status="completed")
    else:
        tasks = db.get_tasks()

    if not tasks:
        return html.Div(
            style={"textAlign": "center", "padding": "48px", "background": COLORS["card_bg"], "borderRadius": "12px"},
            children=[
                html.P("No tasks found.", style={"color": COLORS["text_muted"], "fontSize": "1rem", "marginBottom": "8px"}),
                html.P("Click 'Add Task' to create your first task.", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
            ],
        )

    items = []
    for t in tasks:
        # Build action buttons based on status
        actions = []
        if t["status"] == "pending":
            actions.append(dbc.Button("Start", id={"type": "task-status-btn", "index": t["id"], "action": "start"}, size="sm", outline=True, color="info", style={"fontSize": "0.75rem"}))
            actions.append(dbc.Button("Done", id={"type": "task-status-btn", "index": t["id"], "action": "complete"}, size="sm", outline=True, color="success", style={"fontSize": "0.75rem"}))
        elif t["status"] == "in_progress":
            actions.append(dbc.Button("Done", id={"type": "task-status-btn", "index": t["id"], "action": "complete"}, size="sm", outline=True, color="success", style={"fontSize": "0.75rem"}))
            actions.append(dbc.Button("Cancel", id={"type": "task-status-btn", "index": t["id"], "action": "cancel"}, size="sm", outline=True, color="danger", style={"fontSize": "0.75rem"}))
        elif t["status"] in ("completed", "cancelled"):
            actions.append(dbc.Button("Reopen", id={"type": "task-status-btn", "index": t["id"], "action": "reopen"}, size="sm", outline=True, color="secondary", style={"fontSize": "0.75rem"}))

        card = _task_card(t)
        items.append(
            html.Div(
                style={"position": "relative"},
                children=[
                    card,
                    html.Div(
                        style={"position": "absolute", "bottom": "12px", "right": "16px", "display": "flex", "gap": "4px"},
                        children=actions,
                    ) if actions else None,
                ],
            )
        )
    return html.Div(items)


@callback(
    Output("task-title", "value"),
    Output("task-description", "value"),
    Output("task-priority", "value"),
    Output("task-due-date", "value"),
    Input("btn-create-task", "n_clicks"),
    State("task-title", "value"),
    State("task-description", "value"),
    State("task-priority", "value"),
    State("task-due-date", "value"),
    prevent_initial_call=True,
)
def create_task(n, title, description, priority, due_date):
    if not n or not title or not title.strip():
        return no_update, no_update, no_update, no_update

    db.create_task(
        title=title.strip(),
        description=(description or "").strip(),
        priority=priority or "medium",
        due_date=due_date or None,
    )
    return "", "", "medium", None
