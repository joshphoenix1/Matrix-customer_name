"""
Reusable task display card component.
"""

from dash import html
from config import COLORS

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


def task_card(task, show_actions=True):
    priority_color = PRIORITY_COLORS.get(task["priority"], COLORS["text_muted"])
    status_label, status_color = STATUS_LABELS.get(
        task["status"], ("Unknown", COLORS["text_muted"])
    )

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
                            # Priority badge
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
                            # Status badge
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
            html.Div(
                style={"display": "flex", "gap": "16px", "alignItems": "center"},
                children=[
                    html.Span(
                        due_text,
                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                    ) if due_text else None,
                    html.Span(
                        f"Assigned: {task['assigned_to']}",
                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                    ) if task.get("assigned_to") else None,
                ],
            ) if (due_text or task.get("assigned_to")) else None,
        ],
    )
