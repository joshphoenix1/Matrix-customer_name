"""
Emails page — IMAP inbox scanning with AI analysis, urgency filtering.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import json
from config import COLORS
import db
from services.email_ingestion import scan_and_process_inbox

dash.register_page(__name__, path="/emails", name="Emails", order=6)

URGENCY_COLORS = {
    "critical": COLORS["danger"],
    "important": "#E17055",
    "routine": COLORS["info"],
    "fyi": COLORS["text_muted"],
}

URGENCY_ORDER = {"critical": 0, "important": 1, "routine": 2, "fyi": 3}

FILTER_OPTIONS = ["All", "Critical", "Important", "Routine", "FYI"]


def _connection_status():
    """Return a small status indicator based on whether IMAP is configured."""
    server = db.get_setting("imap_server")
    email_addr = db.get_setting("imap_email")
    password = db.get_setting("imap_password")

    if server and email_addr and password:
        return html.Span(
            [
                html.I(className="bi bi-circle-fill", style={"fontSize": "0.5rem", "marginRight": "6px", "color": COLORS["success"]}),
                email_addr,
            ],
            style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
        )
    return html.Span(
        [
            html.I(className="bi bi-circle-fill", style={"fontSize": "0.5rem", "marginRight": "6px", "color": COLORS["danger"]}),
            "Not configured",
        ],
        style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
    )


layout = html.Div(
    children=[
        dcc.Store(id="emails-filter", data="All"),
        dcc.Store(id="emails-scan-result", data=None),
        dcc.Store(id="emails-page-load", data=0),
        # Header
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div(
                    children=[
                        html.H2("Emails", style={"color": COLORS["text_primary"], "margin": 0}),
                        html.P(
                            "Scan your inbox and let AI triage incoming emails.",
                            style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                        ),
                    ]
                ),
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "16px"},
                    children=[
                        html.Div(id="emails-connection-status"),
                        dbc.Button(
                            [
                                html.I(className="bi bi-arrow-clockwise", style={"marginRight": "6px"}),
                                "Scan Inbox",
                            ],
                            id="emails-scan-btn",
                            color="primary",
                            style={"background": COLORS["accent"], "border": "none"},
                        ),
                    ],
                ),
            ],
        ),
        # Scan result banner
        html.Div(id="emails-scan-banner"),
        # Filter buttons
        html.Div(
            style={"display": "flex", "gap": "8px", "marginBottom": "20px", "flexWrap": "wrap"},
            children=[
                dbc.Button(
                    f,
                    id={"type": "emails-filter-btn", "index": f},
                    size="sm",
                    outline=True,
                    color="light",
                    style={"fontSize": "0.8rem"},
                )
                for f in FILTER_OPTIONS
            ],
        ),
        # Email list
        html.Div(id="emails-list"),
    ]
)


# ── Callbacks ──

@callback(
    Output("emails-connection-status", "children"),
    Input("emails-scan-result", "data"),
    Input("emails-page-load", "data"),
)
def update_connection_status(*_):
    return _connection_status()


@callback(
    Output("emails-scan-banner", "children"),
    Output("emails-scan-result", "data"),
    Input("emails-scan-btn", "n_clicks"),
    prevent_initial_call=True,
)
def scan_inbox(n_clicks):
    if not n_clicks:
        return no_update, no_update

    # Check config
    server = db.get_setting("imap_server")
    email_addr = db.get_setting("imap_email")
    password = db.get_setting("imap_password")

    if not server or not email_addr or not password:
        return html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "16px 20px",
                "marginBottom": "20px",
                "borderLeft": f"4px solid {COLORS['warning']}",
            },
            children=[
                html.I(className="bi bi-exclamation-triangle", style={"color": COLORS["warning"], "marginRight": "8px"}),
                html.Span(
                    "IMAP not configured. Go to ",
                    style={"color": COLORS["text_secondary"], "fontSize": "0.9rem"},
                ),
                dcc.Link("Setup", href="/setup", style={"color": COLORS["accent"]}),
                html.Span(
                    " to add your email credentials.",
                    style={"color": COLORS["text_secondary"], "fontSize": "0.9rem"},
                ),
            ],
        ), dash.no_update

    summary = scan_and_process_inbox()

    if summary["fetched"] == 0:
        banner = html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "16px 20px",
                "marginBottom": "20px",
                "borderLeft": f"4px solid {COLORS['info']}",
            },
            children=[
                html.I(className="bi bi-inbox", style={"color": COLORS["info"], "marginRight": "8px"}),
                html.Span(
                    "No new emails to process — all inbox emails have already been scanned.",
                    style={"color": COLORS["text_secondary"], "fontSize": "0.9rem"},
                ),
            ],
        )
    else:
        parts = [f"Fetched {summary['fetched']} email{'s' if summary['fetched'] != 1 else ''}"]
        parts.append(f"{summary['processed']} processed by AI")
        if summary.get("tasks_created"):
            parts.append(f"{summary['tasks_created']} task{'s' if summary['tasks_created'] != 1 else ''} auto-created")
        if summary.get("meetings_created"):
            parts.append(f"{summary['meetings_created']} meeting{'s' if summary['meetings_created'] != 1 else ''} added")
        if summary.get("skipped"):
            parts.append(f"{summary['skipped']} automated skipped")
        if summary.get("errors"):
            parts.append(f"{summary['errors']} error{'s' if summary['errors'] != 1 else ''}")

        banner = html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "16px 20px",
                "marginBottom": "20px",
                "borderLeft": f"4px solid {COLORS['success']}",
            },
            children=[
                html.I(className="bi bi-check-circle-fill", style={"color": COLORS["success"], "marginRight": "8px"}),
                html.Span(
                    " — ".join(parts),
                    style={"color": COLORS["text_secondary"], "fontSize": "0.9rem"},
                ),
            ],
        )

    return banner, summary["fetched"]


@callback(
    Output("emails-filter", "data"),
    Input({"type": "emails-filter-btn", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def set_filter(n_clicks_list):
    if not ctx.triggered_id:
        return no_update
    return ctx.triggered_id["index"]


@callback(
    Output("emails-list", "children"),
    Input("emails-filter", "data"),
    Input("emails-scan-result", "data"),
)
def render_emails(active_filter, _scan_result):
    emails = db.get_emails(limit=50)

    if not emails:
        return html.Div(
            style={"textAlign": "center", "padding": "48px", "background": COLORS["card_bg"], "borderRadius": "12px"},
            children=[
                html.I(className="bi bi-envelope", style={"fontSize": "2.5rem", "color": COLORS["text_muted"], "marginBottom": "12px", "display": "block"}),
                html.P("No emails yet.", style={"color": COLORS["text_muted"], "fontSize": "1rem", "marginBottom": "8px"}),
                html.P("Click \"Scan Inbox\" to fetch emails from your connected mailbox.", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
            ],
        )

    # Apply filter
    if active_filter and active_filter != "All":
        filter_key = active_filter.lower()
        emails = [e for e in emails if e.get("urgency", "routine") == filter_key]

    if not emails:
        return html.Div(
            style={"textAlign": "center", "padding": "32px", "background": COLORS["card_bg"], "borderRadius": "12px"},
            children=[
                html.P(f"No {active_filter.lower()} emails.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem"}),
            ],
        )

    # Sort by urgency
    emails.sort(key=lambda e: URGENCY_ORDER.get(e.get("urgency", "routine"), 9))

    items = []
    for em in emails:
        urgency = em.get("urgency", "routine")
        urgency_color = URGENCY_COLORS.get(urgency, COLORS["text_muted"])

        # Parse action items
        action_items = []
        if em.get("action_items"):
            try:
                action_items = json.loads(em["action_items"]) if isinstance(em["action_items"], str) else em["action_items"]
            except (json.JSONDecodeError, TypeError):
                pass

        # Build card content
        card_children = [
            # Top row: urgency badge + subject + sender
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "6px", "flexWrap": "wrap"},
                children=[
                    html.Span(
                        urgency.upper(),
                        style={
                            "background": urgency_color,
                            "color": "#fff",
                            "padding": "2px 8px",
                            "borderRadius": "4px",
                            "fontSize": "0.65rem",
                            "fontWeight": "700",
                            "letterSpacing": "0.5px",
                        },
                    ),
                    html.Span(
                        em["subject"],
                        style={"color": COLORS["text_primary"], "fontSize": "0.95rem", "fontWeight": "600"},
                    ),
                ],
            ),
            # Sender + time
            html.Div(
                style={"display": "flex", "gap": "12px", "marginBottom": "8px"},
                children=[
                    html.Span(
                        em["sender"],
                        style={"color": COLORS["text_secondary"], "fontSize": "0.8rem"},
                    ),
                    html.Span(
                        em.get("received_at", ""),
                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                    ),
                ],
            ),
        ]

        # AI Summary
        if em.get("processed_summary"):
            card_children.append(
                html.P(
                    em["processed_summary"],
                    style={
                        "color": COLORS["text_secondary"],
                        "fontSize": "0.85rem",
                        "lineHeight": "1.5",
                        "margin": "0 0 8px 0",
                        "padding": "8px 12px",
                        "background": COLORS["body_bg"],
                        "borderRadius": "6px",
                    },
                )
            )

        # Action items
        if action_items:
            action_children = [
                html.Span("Action items: ", style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "fontWeight": "600"}),
            ]
            for ai in action_items:
                label = ai if isinstance(ai, str) else ai.get("description", str(ai))
                action_children.append(
                    html.Span(
                        label,
                        style={
                            "background": COLORS["body_bg"],
                            "color": COLORS["text_primary"],
                            "padding": "2px 8px",
                            "borderRadius": "4px",
                            "fontSize": "0.75rem",
                            "marginLeft": "4px",
                            "border": f"1px solid {COLORS['border']}",
                        },
                    )
                )
            card_children.append(
                html.Div(
                    style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
                    children=action_children,
                )
            )

        items.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "16px 20px",
                    "marginBottom": "8px",
                    "borderLeft": f"4px solid {urgency_color}",
                },
                children=card_children,
            )
        )

    return html.Div(items)
