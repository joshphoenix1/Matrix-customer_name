"""
Tasks page — Kanban board with columns for To Do, In Progress, Done.
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

COLUMNS = [
    ("pending", "To Do", COLORS["text_muted"]),
    ("in_progress", "In Progress", COLORS["info"]),
    ("completed", "Done", COLORS["success"]),
]

COLUMN_STYLE = {
    "flex": "1",
    "minWidth": "280px",
    "background": COLORS["body_bg"],
    "borderRadius": "12px",
    "padding": "16px",
    "display": "flex",
    "flexDirection": "column",
    "maxHeight": "calc(100vh - 240px)",
    "overflowY": "auto",
}

CARD_STYLE = {
    "background": COLORS["card_bg"],
    "borderRadius": "10px",
    "padding": "14px 16px",
    "marginBottom": "10px",
    "cursor": "default",
    "transition": "box-shadow 0.2s",
}


def _board_card(task):
    """Render a compact Kanban card."""
    priority = task["priority"]
    priority_color = PRIORITY_COLORS.get(priority, COLORS["text_muted"])
    status = task["status"]

    due_text = ""
    overdue = False
    if task.get("due_date"):
        due_text = task["due_date"]
        if task["due_date"] < date.today().isoformat() and status != "completed":
            overdue = True

    # Move buttons
    move_btns = []
    if status == "pending":
        move_btns.append(
            html.Button(
                html.I(className="bi bi-arrow-right"),
                id={"type": "task-move", "index": task["id"], "action": "start"},
                title="Move to In Progress",
                style={
                    "background": "transparent",
                    "border": "none",
                    "color": COLORS["info"],
                    "cursor": "pointer",
                    "fontSize": "0.9rem",
                    "padding": "2px 6px",
                },
            )
        )
        move_btns.append(
            html.Button(
                html.I(className="bi bi-check-lg"),
                id={"type": "task-move", "index": task["id"], "action": "complete"},
                title="Mark Done",
                style={
                    "background": "transparent",
                    "border": "none",
                    "color": COLORS["success"],
                    "cursor": "pointer",
                    "fontSize": "0.9rem",
                    "padding": "2px 6px",
                },
            )
        )
    elif status == "in_progress":
        move_btns.append(
            html.Button(
                html.I(className="bi bi-arrow-left"),
                id={"type": "task-move", "index": task["id"], "action": "reopen"},
                title="Move back to To Do",
                style={
                    "background": "transparent",
                    "border": "none",
                    "color": COLORS["text_muted"],
                    "cursor": "pointer",
                    "fontSize": "0.9rem",
                    "padding": "2px 6px",
                },
            )
        )
        move_btns.append(
            html.Button(
                html.I(className="bi bi-check-lg"),
                id={"type": "task-move", "index": task["id"], "action": "complete"},
                title="Mark Done",
                style={
                    "background": "transparent",
                    "border": "none",
                    "color": COLORS["success"],
                    "cursor": "pointer",
                    "fontSize": "0.9rem",
                    "padding": "2px 6px",
                },
            )
        )
    elif status == "completed":
        move_btns.append(
            html.Button(
                html.I(className="bi bi-arrow-counterclockwise"),
                id={"type": "task-move", "index": task["id"], "action": "reopen"},
                title="Reopen",
                style={
                    "background": "transparent",
                    "border": "none",
                    "color": COLORS["text_muted"],
                    "cursor": "pointer",
                    "fontSize": "0.9rem",
                    "padding": "2px 6px",
                },
            )
        )

    return html.Div(
        style={
            **CARD_STYLE,
            "borderLeft": f"4px solid {priority_color}",
            "opacity": "0.6" if status == "completed" else "1",
        },
        children=[
            # Title row
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "marginBottom": "8px"},
                children=[
                    html.Span(
                        task["title"],
                        style={
                            "color": COLORS["text_primary"],
                            "fontSize": "0.88rem",
                            "fontWeight": "600",
                            "lineHeight": "1.3",
                            "flex": "1",
                            "textDecoration": "line-through" if status == "completed" else "none",
                        },
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "2px", "marginLeft": "8px", "flexShrink": "0"},
                        children=move_btns,
                    ),
                ],
            ),
            # Description
            html.P(
                task.get("description", "")[:120] + ("..." if len(task.get("description", "")) > 120 else ""),
                style={
                    "color": COLORS["text_secondary"],
                    "fontSize": "0.78rem",
                    "margin": "0 0 8px 0",
                    "lineHeight": "1.4",
                },
            ) if task.get("description") else None,
            # Footer: priority badge + due date
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                children=[
                    html.Span(
                        priority.upper(),
                        style={
                            "background": priority_color,
                            "color": "#fff",
                            "padding": "1px 7px",
                            "borderRadius": "3px",
                            "fontSize": "0.6rem",
                            "fontWeight": "700",
                            "letterSpacing": "0.5px",
                        },
                    ),
                    html.Span(
                        due_text,
                        style={
                            "color": COLORS["danger"] if overdue else COLORS["text_muted"],
                            "fontSize": "0.72rem",
                            "fontWeight": "600" if overdue else "400",
                        },
                    ) if due_text else None,
                ],
            ),
        ],
    )


# ── Layout ──

layout = html.Div(
    children=[
        dcc.Store(id="board-refresh", data=0),
        # Header
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"},
            children=[
                html.Div(
                    children=[
                        html.H2("Task Board", style={"color": COLORS["text_primary"], "margin": 0}),
                        html.P("Drag-style Kanban board. Move tasks across columns.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"}),
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
                        "marginBottom": "20px",
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
        # Kanban board
        html.Div(id="kanban-board"),
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
    Output("kanban-board", "children"),
    Input("board-refresh", "data"),
    Input("btn-create-task", "n_clicks"),
    Input({"type": "task-move", "index": ALL, "action": ALL}, "n_clicks"),
)
def render_board(_, create_clicks, move_clicks):
    # Handle move action
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "task-move":
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

    all_tasks = db.get_tasks()

    columns = []
    for status_key, label, color in COLUMNS:
        col_tasks = [t for t in all_tasks if t["status"] == status_key]
        count = len(col_tasks)

        # Sort: critical first, then by due date
        col_tasks.sort(key=lambda t: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(t["priority"], 9),
            t.get("due_date") or "9999-99-99",
        ))

        cards = [_board_card(t) for t in col_tasks]

        if not cards:
            cards = [
                html.Div(
                    style={
                        "textAlign": "center",
                        "padding": "32px 16px",
                        "color": COLORS["text_muted"],
                        "fontSize": "0.8rem",
                    },
                    children="No tasks",
                )
            ]

        columns.append(
            html.Div(
                style=COLUMN_STYLE,
                children=[
                    # Column header
                    html.Div(
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "marginBottom": "14px",
                            "paddingBottom": "10px",
                            "borderBottom": f"2px solid {color}",
                        },
                        children=[
                            html.Span(
                                label,
                                style={
                                    "color": COLORS["text_primary"],
                                    "fontSize": "0.9rem",
                                    "fontWeight": "700",
                                    "letterSpacing": "0.5px",
                                },
                            ),
                            html.Span(
                                str(count),
                                style={
                                    "background": color,
                                    "color": "#fff",
                                    "width": "24px",
                                    "height": "24px",
                                    "borderRadius": "50%",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "fontSize": "0.7rem",
                                    "fontWeight": "700",
                                },
                            ),
                        ],
                    ),
                    # Cards
                    html.Div(cards),
                ],
            )
        )

    return html.Div(
        style={
            "display": "flex",
            "gap": "16px",
            "alignItems": "flex-start",
        },
        children=columns,
    )


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
