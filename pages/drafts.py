"""
Drafts page — review queue for AI-generated email reply drafts.
Approve/edit/reject/send with side-by-side original vs. reply view.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from config import COLORS
import db

dash.register_page(__name__, path="/drafts", name="Drafts", order=9)


FILTER_OPTIONS = ["Pending Review", "Auto-Approved", "Sent", "Rejected", "All"]
STATUS_MAP = {
    "Pending Review": "pending_review",
    "Auto-Approved": "auto_approved",
    "Sent": "sent",
    "Rejected": "rejected",
    "All": None,
}


def _confidence_color(score):
    if score >= 0.8:
        return COLORS["success"]
    elif score >= 0.6:
        return COLORS["warning"]
    return COLORS["danger"]


def _status_color(status):
    return {
        "pending_review": COLORS["warning"],
        "auto_approved": COLORS["info"],
        "approved": COLORS["accent"],
        "sent": COLORS["success"],
        "rejected": COLORS["danger"],
    }.get(status, COLORS["text_muted"])


def layout():
    return html.Div(
        children=[
            dcc.Store(id="drafts-refresh-trigger", data=0),
            # Header
            html.Div(
                style={"marginBottom": "24px"},
                children=[
                    html.H2(
                        [html.I(className="bi bi-pencil-square", style={"marginRight": "12px"}), "Draft Review Queue"],
                        style={"color": COLORS["text_primary"], "margin": 0},
                    ),
                    html.P(
                        "Review, edit, and send AI-generated email replies.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                    ),
                ],
            ),
            # Filter buttons
            html.Div(
                style={"display": "flex", "gap": "8px", "marginBottom": "20px", "flexWrap": "wrap"},
                children=[
                    dbc.Button(
                        opt,
                        id={"type": "draft-filter", "index": opt},
                        size="sm",
                        outline=True,
                        color="light" if opt != "Pending Review" else "warning",
                        style={"fontSize": "0.8rem"},
                    )
                    for opt in FILTER_OPTIONS
                ],
            ),
            # Drafts list
            dcc.Loading(
                type="dot",
                color=COLORS["accent"],
                children=[html.Div(id="drafts-list")],
            ),
        ]
    )


# ── Render drafts list ──

@callback(
    Output("drafts-list", "children"),
    Input({"type": "draft-filter", "index": ALL}, "n_clicks"),
    Input("drafts-refresh-trigger", "data"),
)
def render_drafts(filter_clicks, _refresh):
    # Determine active filter
    active_filter = "Pending Review"
    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered.get("type") == "draft-filter":
        active_filter = triggered["index"]

    status_filter = STATUS_MAP.get(active_filter)
    drafts = db.get_email_drafts(status=status_filter, limit=50)

    if not drafts:
        return html.Div(
            style={"textAlign": "center", "padding": "60px 20px"},
            children=[
                html.I(className="bi bi-inbox", style={"fontSize": "3rem", "color": COLORS["text_muted"]}),
                html.P(
                    f"No {active_filter.lower()} drafts.",
                    style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "marginTop": "12px"},
                ),
            ],
        )

    # Build draft cards
    cards = []
    for draft in drafts:
        # Load original email info
        original_email = None
        if draft.get("email_id"):
            emails = db.get_emails(limit=500)
            original_email = next((e for e in emails if e["id"] == draft["email_id"]), None)

        confidence = draft.get("confidence_score", 0)
        status = draft.get("status", "pending_review")

        cards.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "20px",
                    "marginBottom": "16px",
                    "borderLeft": f"4px solid {_status_color(status)}",
                },
                children=[
                    # Header: subject + badges
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px", "flexWrap": "wrap", "gap": "8px"},
                        children=[
                            html.H5(
                                draft.get("subject", "No Subject"),
                                style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1rem"},
                            ),
                            html.Div(
                                style={"display": "flex", "gap": "6px"},
                                children=[
                                    html.Span(
                                        f"{confidence:.0%}",
                                        style={
                                            "background": _confidence_color(confidence),
                                            "color": "#fff",
                                            "padding": "2px 8px",
                                            "borderRadius": "4px",
                                            "fontSize": "0.75rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Span(
                                        draft.get("category", "general"),
                                        style={
                                            "background": COLORS["body_bg"],
                                            "color": COLORS["text_secondary"],
                                            "padding": "2px 8px",
                                            "borderRadius": "4px",
                                            "fontSize": "0.75rem",
                                        },
                                    ),
                                    html.Span(
                                        status.replace("_", " ").title(),
                                        style={
                                            "background": _status_color(status),
                                            "color": "#fff",
                                            "padding": "2px 8px",
                                            "borderRadius": "4px",
                                            "fontSize": "0.75rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.P(
                        f"To: {draft.get('recipient', '—')}",
                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "margin": "0 0 12px 0"},
                    ),
                    # Side-by-side: Original | Reply
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P("Original Email", style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "1px", "margin": "0 0 8px 0"}),
                                    html.Div(
                                        style={
                                            "background": COLORS["body_bg"],
                                            "borderRadius": "8px",
                                            "padding": "12px",
                                            "maxHeight": "200px",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.P(
                                                original_email.get("body", "")[:1000] if original_email else draft.get("original_body", "")[:1000],
                                                style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "margin": 0, "whiteSpace": "pre-wrap", "lineHeight": "1.5"},
                                            ),
                                        ],
                                    ),
                                ],
                                md=6,
                            ),
                            dbc.Col(
                                [
                                    html.P("Generated Reply", style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "1px", "margin": "0 0 8px 0"}),
                                    dbc.Textarea(
                                        id={"type": "draft-edit-body", "index": draft["id"]},
                                        value=draft.get("body", ""),
                                        style={
                                            "background": COLORS["body_bg"],
                                            "border": f"1px solid {COLORS['border']}",
                                            "color": COLORS["text_primary"],
                                            "borderRadius": "8px",
                                            "minHeight": "200px",
                                            "fontSize": "0.85rem",
                                        },
                                        disabled=status in ("sent", "rejected"),
                                    ),
                                ],
                                md=6,
                            ),
                        ],
                    ),
                    # Reasoning
                    html.Div(
                        style={"marginTop": "10px"},
                        children=[
                            html.Span("AI Reasoning: ", style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "fontWeight": "600"}),
                            html.Span(draft.get("reasoning", "—"), style={"color": COLORS["text_secondary"], "fontSize": "0.75rem"}),
                        ],
                    ) if draft.get("reasoning") else None,
                    # Action buttons
                    html.Div(
                        style={"display": "flex", "gap": "8px", "marginTop": "14px"},
                        children=[
                            dbc.Button(
                                [html.I(className="bi bi-send-fill", style={"marginRight": "6px"}), "Approve & Send"],
                                id={"type": "draft-send", "index": draft["id"]},
                                size="sm",
                                color="success",
                                style={"fontSize": "0.8rem"},
                                disabled=status in ("sent", "rejected"),
                            ),
                            dbc.Button(
                                [html.I(className="bi bi-check-lg", style={"marginRight": "6px"}), "Approve"],
                                id={"type": "draft-approve", "index": draft["id"]},
                                size="sm",
                                color="primary",
                                outline=True,
                                style={"fontSize": "0.8rem"},
                                disabled=status in ("sent", "rejected", "approved"),
                            ),
                            dbc.Button(
                                [html.I(className="bi bi-x-lg", style={"marginRight": "6px"}), "Reject"],
                                id={"type": "draft-reject", "index": draft["id"]},
                                size="sm",
                                color="danger",
                                outline=True,
                                style={"fontSize": "0.8rem"},
                                disabled=status in ("sent", "rejected"),
                            ),
                        ],
                    ) if status not in ("sent", "rejected") else None,
                ],
            )
        )

    return html.Div(cards)


# ── Action callbacks ──

@callback(
    Output("drafts-refresh-trigger", "data"),
    Input({"type": "draft-send", "index": ALL}, "n_clicks"),
    Input({"type": "draft-approve", "index": ALL}, "n_clicks"),
    Input({"type": "draft-reject", "index": ALL}, "n_clicks"),
    State({"type": "draft-edit-body", "index": ALL}, "value"),
    State("drafts-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def handle_draft_actions(send_clicks, approve_clicks, reject_clicks, edit_bodies, current_trigger):
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update

    draft_id = triggered["index"]
    action = triggered["type"]

    # Find the matching textarea value for this draft
    # The ALL pattern returns values in order of the pattern-matching IDs
    # We need to find which index corresponds to our draft_id
    all_edit_ids = ctx.inputs_list[3] if len(ctx.inputs_list) > 3 else []
    edited_body = None
    for item in all_edit_ids:
        if isinstance(item, dict) and item.get("id", {}).get("index") == draft_id:
            edited_body = item.get("value")
            break

    # Save any edited body before action
    if edited_body is not None:
        db.update_email_draft(draft_id, body=edited_body)

    if action == "draft-send":
        # Approve and send via SMTP
        db.update_email_draft(draft_id, status="approved")
        from services.email_sender import send_approved_draft
        success, message = send_approved_draft(draft_id)
        # Status is updated inside send_approved_draft on success

    elif action == "draft-approve":
        db.update_email_draft(draft_id, status="approved")

    elif action == "draft-reject":
        db.update_email_draft(draft_id, status="rejected")

    return (current_trigger or 0) + 1
