"""
Team Chat page — Slack/Teams-style channel messaging.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from config import COLORS
import db

dash.register_page(__name__, path="/team-chat", name="Team Chat", order=7)


def _initials(name):
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"


def _format_time(ts):
    if not ts:
        return ""
    # ts is like "2026-02-22 14:30:00"
    parts = ts.split(" ")
    if len(parts) >= 2:
        time_part = parts[1][:5]  # HH:MM
        return f"{parts[0]} {time_part}"
    return ts


# ── Layout ──

layout = html.Div(
    style={"padding": "0"},
    children=[
        dcc.Store(id="tc-selected-channel", storage_type="session"),
        dcc.Store(id="tc-refresh", data=0),

        html.Div(
            style={"display": "flex", "height": "calc(100vh - 40px)"},
            children=[
                # Channel sidebar
                html.Div(
                    style={
                        "width": "240px",
                        "minWidth": "240px",
                        "background": COLORS["sidebar_bg"],
                        "borderRight": f"1px solid {COLORS['border']}",
                        "padding": "16px",
                        "overflowY": "auto",
                        "display": "flex",
                        "flexDirection": "column",
                    },
                    children=[
                        html.H3(
                            "Channels",
                            style={"color": COLORS["text_primary"], "fontSize": "1rem", "fontWeight": "700", "margin": "0 0 16px 0", "letterSpacing": "1px"},
                        ),
                        html.Div(id="tc-channel-list"),
                        html.Hr(style={"borderColor": COLORS["border"], "margin": "16px 0"}),
                        # Online team members
                        html.H4(
                            "Team",
                            style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase", "letterSpacing": "1px", "margin": "0 0 10px 0"},
                        ),
                        html.Div(id="tc-online-list"),
                    ],
                ),
                # Message area
                html.Div(
                    style={"flex": "1", "display": "flex", "flexDirection": "column", "padding": "0"},
                    children=[
                        # Channel header
                        html.Div(
                            id="tc-channel-header",
                            style={
                                "padding": "12px 24px",
                                "borderBottom": f"1px solid {COLORS['border']}",
                                "background": COLORS["card_bg"],
                            },
                        ),
                        # Messages feed
                        html.Div(
                            id="tc-message-feed",
                            style={
                                "flex": "1",
                                "overflowY": "auto",
                                "padding": "16px 24px",
                            },
                        ),
                        # Input area
                        html.Div(
                            style={
                                "padding": "12px 24px",
                                "borderTop": f"1px solid {COLORS['border']}",
                                "background": COLORS["card_bg"],
                            },
                            children=[
                                html.Div(
                                    style={"display": "flex", "gap": "8px", "alignItems": "center"},
                                    children=[
                                        dbc.Select(
                                            id="tc-sender-select",
                                            style={
                                                "width": "160px",
                                                "background": COLORS["body_bg"],
                                                "border": f"1px solid {COLORS['border']}",
                                                "color": COLORS["text_primary"],
                                                "fontSize": "0.8rem",
                                            },
                                        ),
                                        dbc.Input(
                                            id="tc-message-input",
                                            placeholder="Type a message...",
                                            type="text",
                                            style={
                                                "flex": "1",
                                                "background": COLORS["body_bg"],
                                                "border": f"1px solid {COLORS['border']}",
                                                "color": COLORS["text_primary"],
                                                "borderRadius": "8px",
                                            },
                                            debounce=False,
                                        ),
                                        dbc.Button(
                                            html.I(className="bi bi-send-fill"),
                                            id="tc-btn-send",
                                            color="primary",
                                            style={"background": COLORS["accent"], "border": "none", "borderRadius": "8px"},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ── Callbacks ──

@callback(
    Output("tc-channel-list", "children"),
    Output("tc-selected-channel", "data"),
    Output("tc-sender-select", "options"),
    Output("tc-sender-select", "value"),
    Output("tc-online-list", "children"),
    Input("tc-refresh", "data"),
    Input({"type": "tc-channel-btn", "index": ALL}, "n_clicks"),
    State("tc-selected-channel", "data"),
)
def render_channels(_, chan_clicks, current_channel):
    channels = db.get_channels()
    employees = db.get_employees()

    # Determine selected channel
    selected = current_channel
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "tc-channel-btn":
        selected = ctx.triggered_id["index"]
    if selected is None and channels:
        selected = channels[0]["id"]

    # Channel list
    chan_items = []
    for ch in channels:
        is_active = ch["id"] == selected
        msg_count = len(db.get_channel_messages(ch["id"]))
        chan_items.append(
            html.Div(
                id={"type": "tc-channel-btn", "index": ch["id"]},
                n_clicks=0,
                style={
                    "padding": "8px 12px",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "background": f"rgba(108, 92, 231, 0.2)" if is_active else "transparent",
                    "marginBottom": "2px",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
                children=[
                    html.Span(
                        f"# {ch['name']}",
                        style={
                            "color": COLORS["text_primary"] if is_active else COLORS["text_secondary"],
                            "fontSize": "0.85rem",
                            "fontWeight": "600" if is_active else "400",
                        },
                    ),
                    html.Span(
                        str(msg_count),
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "0.7rem",
                            "background": COLORS["border"],
                            "padding": "1px 6px",
                            "borderRadius": "8px",
                        },
                    ) if msg_count else None,
                ],
            )
        )

    # Employee sender options
    sender_options = [{"label": e["name"], "value": e["name"]} for e in employees]
    default_sender = employees[0]["name"] if employees else ""

    # Online team list
    status_colors = {"active": COLORS["success"], "away": COLORS["warning"], "offline": COLORS["text_muted"]}
    online_items = []
    for e in employees:
        dot_color = status_colors.get(e["status"], COLORS["text_muted"])
        online_items.append(
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "4px 0"},
                children=[
                    html.Span(
                        style={
                            "width": "8px", "height": "8px", "borderRadius": "50%",
                            "background": dot_color, "flexShrink": "0",
                        },
                    ),
                    html.Span(e["name"], style={"color": COLORS["text_secondary"], "fontSize": "0.8rem"}),
                ],
            )
        )

    return html.Div(chan_items), selected, sender_options, default_sender, html.Div(online_items)


@callback(
    Output("tc-channel-header", "children"),
    Input("tc-selected-channel", "data"),
)
def render_channel_header(channel_id):
    if not channel_id:
        return html.Span("Select a channel", style={"color": COLORS["text_muted"]})
    ch = db.get_channel(channel_id)
    if not ch:
        return html.Span("Channel not found", style={"color": COLORS["danger"]})
    return html.Div(children=[
        html.Span(f"# {ch['name']}", style={"color": COLORS["text_primary"], "fontSize": "1.1rem", "fontWeight": "700", "marginRight": "12px"}),
        html.Span(ch.get("description", ""), style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
    ])


@callback(
    Output("tc-message-feed", "children"),
    Input("tc-selected-channel", "data"),
    Input("tc-refresh", "data"),
)
def render_messages(channel_id, _):
    if not channel_id:
        return html.Div(
            style={"textAlign": "center", "padding": "60px 20px"},
            children=[
                html.I(className="bi bi-chat-square-text", style={"fontSize": "3rem", "color": COLORS["border"], "marginBottom": "16px", "display": "block"}),
                html.P("Select a channel to view messages", style={"color": COLORS["text_muted"]}),
            ],
        )

    messages = db.get_channel_messages(channel_id)
    if not messages:
        return html.Div(
            style={"textAlign": "center", "padding": "60px 20px"},
            children=[
                html.P("No messages yet. Start the conversation!", style={"color": COLORS["text_muted"]}),
            ],
        )

    msg_elements = []
    for msg in messages:
        msg_elements.append(
            html.Div(
                style={
                    "display": "flex",
                    "gap": "12px",
                    "padding": "8px 0",
                    "borderBottom": f"1px solid rgba(45, 52, 54, 0.3)",
                },
                children=[
                    # Avatar
                    html.Div(
                        _initials(msg["sender_name"]),
                        style={
                            "width": "36px", "height": "36px", "borderRadius": "8px",
                            "background": msg.get("sender_avatar_color", COLORS["accent"]),
                            "display": "flex", "alignItems": "center", "justifyContent": "center",
                            "fontSize": "0.75rem", "fontWeight": "700", "color": "#fff",
                            "flexShrink": "0",
                        },
                    ),
                    # Content
                    html.Div(
                        style={"flex": "1", "minWidth": "0"},
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "baseline", "gap": "8px", "marginBottom": "2px"},
                                children=[
                                    html.Span(msg["sender_name"], style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "700"}),
                                    html.Span(_format_time(msg["created_at"]), style={"color": COLORS["text_muted"], "fontSize": "0.7rem"}),
                                ],
                            ),
                            html.P(msg["content"], style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "margin": 0, "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                        ],
                    ),
                ],
            )
        )

    return html.Div(msg_elements)


@callback(
    Output("tc-message-feed", "children", allow_duplicate=True),
    Output("tc-message-input", "value"),
    Output("tc-channel-list", "children", allow_duplicate=True),
    Input("tc-btn-send", "n_clicks"),
    Input("tc-message-input", "n_submit"),
    State("tc-message-input", "value"),
    State("tc-sender-select", "value"),
    State("tc-selected-channel", "data"),
    prevent_initial_call=True,
)
def send_message(n_clicks, n_submit, message, sender, channel_id):
    if not message or not message.strip() or not channel_id or not sender:
        return no_update, no_update, no_update

    # Get avatar color for sender
    employees = db.get_employees()
    avatar_color = COLORS["accent"]
    for e in employees:
        if e["name"] == sender:
            avatar_color = e.get("avatar_color", COLORS["accent"])
            break

    db.send_channel_message(channel_id, sender, message.strip(), avatar_color)

    # Re-render messages and channel list (to update counts)
    messages = db.get_channel_messages(channel_id)
    msg_elements = []
    for msg in messages:
        msg_elements.append(
            html.Div(
                style={
                    "display": "flex",
                    "gap": "12px",
                    "padding": "8px 0",
                    "borderBottom": f"1px solid rgba(45, 52, 54, 0.3)",
                },
                children=[
                    html.Div(
                        _initials(msg["sender_name"]),
                        style={
                            "width": "36px", "height": "36px", "borderRadius": "8px",
                            "background": msg.get("sender_avatar_color", COLORS["accent"]),
                            "display": "flex", "alignItems": "center", "justifyContent": "center",
                            "fontSize": "0.75rem", "fontWeight": "700", "color": "#fff",
                            "flexShrink": "0",
                        },
                    ),
                    html.Div(
                        style={"flex": "1", "minWidth": "0"},
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "baseline", "gap": "8px", "marginBottom": "2px"},
                                children=[
                                    html.Span(msg["sender_name"], style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "700"}),
                                    html.Span(_format_time(msg["created_at"]), style={"color": COLORS["text_muted"], "fontSize": "0.7rem"}),
                                ],
                            ),
                            html.P(msg["content"], style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "margin": 0, "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                        ],
                    ),
                ],
            )
        )

    # Re-render channel list for updated counts
    channels = db.get_channels()
    selected = channel_id
    chan_items = []
    for ch in channels:
        is_active = ch["id"] == selected
        msg_count = len(db.get_channel_messages(ch["id"]))
        chan_items.append(
            html.Div(
                id={"type": "tc-channel-btn", "index": ch["id"]},
                n_clicks=0,
                style={
                    "padding": "8px 12px",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "background": f"rgba(108, 92, 231, 0.2)" if is_active else "transparent",
                    "marginBottom": "2px",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
                children=[
                    html.Span(
                        f"# {ch['name']}",
                        style={
                            "color": COLORS["text_primary"] if is_active else COLORS["text_secondary"],
                            "fontSize": "0.85rem",
                            "fontWeight": "600" if is_active else "400",
                        },
                    ),
                    html.Span(
                        str(msg_count),
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "0.7rem",
                            "background": COLORS["border"],
                            "padding": "1px 6px",
                            "borderRadius": "8px",
                        },
                    ) if msg_count else None,
                ],
            )
        )

    return html.Div(msg_elements), "", html.Div(chan_items)
