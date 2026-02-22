"""
Projects page — employee directory and Jira-style project kanban board.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from config import COLORS
import db

dash.register_page(__name__, path="/projects", name="Projects", order=6)

PRIORITY_COLORS = {
    "critical": COLORS["danger"],
    "high": "#E17055",
    "medium": COLORS["warning"],
    "low": COLORS["info"],
}

STATUS_MAP = {
    "pending": "TO DO",
    "in_progress": "IN PROGRESS",
    "completed": "DONE",
    "cancelled": "DONE",
}

STATUS_COLORS = {
    "TO DO": COLORS["text_muted"],
    "IN PROGRESS": COLORS["info"],
    "DONE": COLORS["success"],
}


def _initials(name):
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"


# ── Layout ──

layout = html.Div(
    children=[
        dcc.Store(id="team-selected-project", data=None),
        dcc.Store(id="team-board-refresh", data=0),

        # Page header
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div(children=[
                    html.H2("Team & Projects", style={"color": COLORS["text_primary"], "margin": 0}),
                    html.P("Employee directory and project boards.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"}),
                ]),
            ],
        ),

        # ── Employee Directory ──
        html.Div(
            style={"marginBottom": "32px"},
            children=[
                html.H3(
                    [html.I(className="bi bi-people-fill", style={"marginRight": "10px"}), "Team Directory"],
                    style={"color": COLORS["text_primary"], "fontSize": "1.1rem", "marginBottom": "16px"},
                ),
                html.Div(id="employee-grid"),
            ],
        ),

        # ── Project Board Section ──
        html.Div(children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"},
                children=[
                    html.H3(
                        [html.I(className="bi bi-kanban", style={"marginRight": "10px"}), "Project Board"],
                        style={"color": COLORS["text_primary"], "fontSize": "1.1rem", "margin": 0},
                    ),
                ],
            ),
            # Project tabs
            html.Div(id="project-tabs", style={"marginBottom": "16px"}),
            # Kanban board
            html.Div(id="kanban-board"),
        ]),
    ]
)


# ── Callbacks ──

@callback(
    Output("employee-grid", "children"),
    Input("team-board-refresh", "data"),
)
def render_employees(_):
    employees = db.get_employees()
    if not employees:
        return html.P("No team members yet.", style={"color": COLORS["text_muted"]})

    status_colors = {"active": COLORS["success"], "away": COLORS["warning"], "offline": COLORS["text_muted"]}

    cards = []
    for emp in employees:
        dot_color = status_colors.get(emp["status"], COLORS["text_muted"])
        cards.append(
            dbc.Col(
                html.Div(
                    className="employee-card",
                    children=[
                        html.Div(
                            _initials(emp["name"]),
                            className="employee-avatar",
                            style={"background": emp.get("avatar_color", COLORS["accent"])},
                        ),
                        html.H4(emp["name"], style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600", "margin": "0 0 2px 0"}),
                        html.P(emp["role"], style={"color": COLORS["accent"], "fontSize": "0.8rem", "margin": "0 0 4px 0", "fontWeight": "600"}),
                        html.P(emp["department"], style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "margin": "0 0 8px 0"}),
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "4px"},
                            children=[
                                html.Span(className="employee-status-dot", style={"background": dot_color}),
                                html.Span(emp["status"].capitalize(), style={"color": COLORS["text_muted"], "fontSize": "0.7rem"}),
                            ],
                        ),
                    ],
                ),
                xs=6, sm=4, md=3, lg=3,
                style={"marginBottom": "12px"},
            )
        )
    return dbc.Row(cards)


@callback(
    Output("project-tabs", "children"),
    Output("team-selected-project", "data"),
    Input("team-board-refresh", "data"),
    Input({"type": "project-tab-btn", "index": ALL}, "n_clicks"),
    State("team-selected-project", "data"),
)
def render_project_tabs(_, tab_clicks, current_project):
    projects = db.get_projects(status="active")
    if not projects:
        return html.P("No projects yet.", style={"color": COLORS["text_muted"]}), None

    # Determine selected project
    selected = current_project
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "project-tab-btn":
        selected = ctx.triggered_id["index"]

    if selected is None:
        selected = projects[0]["id"]

    buttons = []
    for p in projects:
        is_active = p["id"] == selected
        task_count = len(db.get_tasks_by_project(p["id"]))
        buttons.append(
            dbc.Button(
                [
                    html.Span(p["key"], style={"fontWeight": "700", "marginRight": "6px"}),
                    html.Span(p["name"], style={"fontWeight": "400"}),
                    html.Span(
                        str(task_count),
                        style={
                            "background": "rgba(255,255,255,0.15)" if is_active else COLORS["border"],
                            "padding": "1px 7px",
                            "borderRadius": "10px",
                            "fontSize": "0.7rem",
                            "marginLeft": "8px",
                        },
                    ),
                ],
                id={"type": "project-tab-btn", "index": p["id"]},
                size="sm",
                style={
                    "background": COLORS["accent"] if is_active else "transparent",
                    "border": f"1px solid {COLORS['accent'] if is_active else COLORS['border']}",
                    "color": "#fff" if is_active else COLORS["text_secondary"],
                    "marginRight": "8px",
                    "fontSize": "0.8rem",
                },
            )
        )

    return html.Div(buttons, style={"display": "flex", "flexWrap": "wrap", "gap": "4px"}), selected


@callback(
    Output("kanban-board", "children"),
    Output("team-board-refresh", "data", allow_duplicate=True),
    Input("team-selected-project", "data"),
    Input({"type": "board-move-btn", "index": ALL, "action": ALL}, "n_clicks"),
    State("team-board-refresh", "data"),
    prevent_initial_call=True,
)
def render_kanban(project_id, move_clicks, refresh_count):
    if not project_id:
        return html.P("Select a project above.", style={"color": COLORS["text_muted"]}), no_update

    # Handle move actions
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "board-move-btn":
        task_id = ctx.triggered_id["index"]
        action = ctx.triggered_id["action"]
        action_map = {
            "to_inprogress": "in_progress",
            "to_done": "completed",
            "to_todo": "pending",
        }
        if action in action_map:
            db.update_task(task_id, status=action_map[action])

    project = db.get_project(project_id)
    if not project:
        return html.P("Project not found.", style={"color": COLORS["danger"]}), no_update

    tasks = db.get_tasks_by_project(project_id)
    project_key = project["key"]

    # Bucket tasks by kanban column
    columns = {"TO DO": [], "IN PROGRESS": [], "DONE": []}
    for t in tasks:
        col = STATUS_MAP.get(t["status"], "TO DO")
        columns[col].append(t)

    # Build the kanban columns
    board_children = []
    for col_name in ["TO DO", "IN PROGRESS", "DONE"]:
        col_tasks = columns[col_name]
        col_color = STATUS_COLORS[col_name]

        cards = []
        for t in col_tasks:
            priority_color = PRIORITY_COLORS.get(t["priority"], COLORS["text_muted"])
            task_key = f"{project_key}-{t['id']}"

            # Move buttons
            move_buttons = []
            if col_name == "TO DO":
                move_buttons.append(
                    html.Button(
                        html.I(className="bi bi-arrow-right"),
                        id={"type": "board-move-btn", "index": t["id"], "action": "to_inprogress"},
                        style={
                            "background": "transparent", "border": "none", "color": COLORS["info"],
                            "cursor": "pointer", "padding": "2px 6px", "fontSize": "0.8rem",
                        },
                        title="Move to In Progress",
                    )
                )
            elif col_name == "IN PROGRESS":
                move_buttons.append(
                    html.Button(
                        html.I(className="bi bi-arrow-left"),
                        id={"type": "board-move-btn", "index": t["id"], "action": "to_todo"},
                        style={
                            "background": "transparent", "border": "none", "color": COLORS["text_muted"],
                            "cursor": "pointer", "padding": "2px 6px", "fontSize": "0.8rem",
                        },
                        title="Move to To Do",
                    )
                )
                move_buttons.append(
                    html.Button(
                        html.I(className="bi bi-arrow-right"),
                        id={"type": "board-move-btn", "index": t["id"], "action": "to_done"},
                        style={
                            "background": "transparent", "border": "none", "color": COLORS["success"],
                            "cursor": "pointer", "padding": "2px 6px", "fontSize": "0.8rem",
                        },
                        title="Move to Done",
                    )
                )
            else:  # DONE
                move_buttons.append(
                    html.Button(
                        html.I(className="bi bi-arrow-counterclockwise"),
                        id={"type": "board-move-btn", "index": t["id"], "action": "to_todo"},
                        style={
                            "background": "transparent", "border": "none", "color": COLORS["text_muted"],
                            "cursor": "pointer", "padding": "2px 6px", "fontSize": "0.8rem",
                        },
                        title="Reopen",
                    )
                )

            # Assignee avatar
            assignee_el = None
            if t.get("assigned_to"):
                assignee_el = html.Div(
                    _initials(t["assigned_to"]),
                    className="kanban-avatar",
                    style={"background": COLORS["accent"]},
                    title=t["assigned_to"],
                )

            cards.append(
                html.Div(
                    className="kanban-card",
                    style={"borderLeftColor": priority_color},
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                            children=[
                                html.Span(task_key, className="kanban-card-key"),
                                html.Span(
                                    t["priority"].upper(),
                                    style={
                                        "background": priority_color, "color": "#fff",
                                        "padding": "1px 6px", "borderRadius": "3px",
                                        "fontSize": "0.6rem", "fontWeight": "700",
                                    },
                                ),
                            ],
                        ),
                        html.Div(
                            t["title"],
                            className="kanban-card-title",
                            style={"textDecoration": "line-through" if t["status"] == "completed" else "none"},
                        ),
                        html.Div(
                            className="kanban-card-footer",
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                    children=[
                                        assignee_el,
                                        html.Span(
                                            t["due_date"],
                                            style={"color": COLORS["text_muted"], "fontSize": "0.7rem"},
                                        ) if t.get("due_date") else None,
                                    ],
                                ),
                                html.Div(move_buttons, style={"display": "flex"}),
                            ],
                        ),
                    ],
                )
            )

        board_children.append(
            html.Div(
                className="kanban-column",
                children=[
                    html.Div(
                        className="kanban-column-header",
                        children=[
                            html.H4(col_name, className="kanban-column-title", style={"color": col_color}),
                            html.Span(str(len(col_tasks)), className="kanban-count"),
                        ],
                    ),
                    html.Div(
                        cards if cards else [
                            html.P("No tasks", style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "textAlign": "center", "padding": "20px 0"})
                        ],
                        style={"flex": "1", "overflowY": "auto"},
                    ),
                ],
            )
        )

    # Project description header
    lead_name = ""
    if project.get("lead_id"):
        lead = db.get_employee(project["lead_id"])
        if lead:
            lead_name = lead["name"]

    project_header = html.Div(
        style={
            "background": COLORS["card_bg"],
            "borderRadius": "12px",
            "padding": "16px 20px",
            "marginBottom": "16px",
            "borderLeft": f"4px solid {COLORS['accent']}",
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
        },
        children=[
            html.Div(children=[
                html.Span(project["key"], style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "0.85rem", "marginRight": "8px"}),
                html.Span(project["name"], style={"color": COLORS["text_primary"], "fontWeight": "600", "fontSize": "0.95rem"}),
                html.Span(f"  —  {project.get('description', '')}", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}) if project.get("description") else None,
            ]),
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                children=[
                    html.Span("Lead:", style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
                    html.Span(lead_name, style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "fontWeight": "600"}),
                ] if lead_name else [],
            ),
        ],
    )

    return html.Div([
        project_header,
        html.Div(board_children, className="kanban-board"),
    ]), (refresh_count or 0)
