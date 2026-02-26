"""
Channels page — multi-channel ingestion management for persona training.
Connect Gmail Sent Mail, Telegram, WhatsApp, Slack, and Google Calendar.
"""

import base64
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from config import COLORS
import db

dash.register_page(__name__, path="/channels", name="Channels", order=7)


def _status_badge(text, color_key):
    return html.Span(
        text,
        style={"color": COLORS.get(color_key, COLORS["text_secondary"]), "fontSize": "0.85rem"},
    )


def _channel_card(icon_cls, title, description, body_children, border_color=None):
    """Reusable channel card wrapper."""
    return html.Div(
        style={
            "background": COLORS["card_bg"],
            "borderRadius": "12px",
            "padding": "24px",
            "marginBottom": "20px",
            "borderLeft": f"4px solid {border_color or COLORS['accent']}",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "8px"},
                children=[
                    html.I(className=icon_cls, style={"fontSize": "1.3rem", "color": border_color or COLORS["accent"]}),
                    html.H4(title, style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                ],
            ),
            html.P(description, style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"}),
            html.Div(body_children),
        ],
    )


def _field_input(input_id, placeholder, input_type="text", value=""):
    return dbc.Input(
        id=input_id,
        placeholder=placeholder,
        type=input_type,
        value=value,
        style={
            "background": COLORS["body_bg"],
            "border": f"1px solid {COLORS['border']}",
            "color": COLORS["text_primary"],
            "borderRadius": "8px",
            "marginBottom": "10px",
            "fontSize": "0.85rem",
        },
    )


def layout():
    # Load existing settings
    imap_configured = bool(db.get_setting("imap_server") and db.get_setting("imap_email"))
    telegram_api_id = db.get_setting("telegram_api_id", "")
    telegram_api_hash = db.get_setting("telegram_api_hash", "")
    telegram_phone = db.get_setting("telegram_phone", "")
    slack_token = db.get_setting("slack_bot_token", "")

    # Sample counts per source
    counts = db.get_persona_sample_count_by_source()

    return html.Div(
        children=[
            # Auth state stores
            dcc.Store(id="telegram-auth-state", data="idle"),  # idle | code_sent | connected

            # Header
            html.Div(
                style={"marginBottom": "24px"},
                children=[
                    html.H2(
                        [html.I(className="bi bi-diagram-3-fill", style={"marginRight": "12px"}), "Channels"],
                        style={"color": COLORS["text_primary"], "margin": 0},
                    ),
                    html.P(
                        "Connect your communication channels to enrich persona training data. Each connector pulls only your own messages.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                    ),
                ],
            ),

            # Channel grid
            dbc.Row(
                [
                    # Left column
                    dbc.Col(
                        [
                            # ── Gmail Sent Mail ──
                            _channel_card(
                                "bi bi-envelope-fill", "Gmail Sent Mail",
                                "Ingest your sent emails via IMAP. Uses the same IMAP credentials from Setup.",
                                [
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "12px"},
                                        children=[
                                            html.I(
                                                className="bi bi-circle-fill",
                                                style={
                                                    "fontSize": "0.6rem",
                                                    "color": COLORS["success"] if imap_configured else COLORS["text_muted"],
                                                },
                                            ),
                                            html.Span(
                                                "IMAP Connected" if imap_configured else "IMAP not configured — set up on Setup page",
                                                style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "12px"},
                                        children=[
                                            dbc.Button(
                                                [html.I(className="bi bi-cloud-download", style={"marginRight": "6px"}), "Ingest Sent Mail"],
                                                id="btn-gmail-ingest",
                                                size="sm",
                                                color="primary",
                                                disabled=not imap_configured,
                                                style={"background": COLORS["accent"], "border": "none"} if imap_configured else {},
                                            ),
                                            html.Span(
                                                f"{counts.get('gmail_sent', 0)} samples",
                                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot", color=COLORS["accent"],
                                        children=[html.Div(id="gmail-status", style={"marginTop": "8px"})],
                                    ),
                                ],
                                border_color=COLORS["danger"],
                            ),

                            # ── Telegram ──
                            _channel_card(
                                "bi bi-telegram", "Telegram",
                                "Connect via Telegram API to ingest your messages from all chats.",
                                [
                                    _field_input("telegram-api-id", "API ID", value=telegram_api_id),
                                    _field_input("telegram-api-hash", "API Hash", value=telegram_api_hash),
                                    _field_input("telegram-phone", "Phone Number (+1...)", value=telegram_phone),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "10px"},
                                        children=[
                                            dbc.Button(
                                                [html.I(className="bi bi-send", style={"marginRight": "6px"}), "Send Code"],
                                                id="btn-telegram-send-code",
                                                size="sm", color="info", outline=True,
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-shield-check", style={"marginRight": "6px"}), "Test Connection"],
                                                id="btn-telegram-test",
                                                size="sm", color="secondary", outline=True,
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="telegram-code-section",
                                        style={"display": "none"},
                                        children=[
                                            _field_input("telegram-code", "Enter verification code"),
                                            dbc.Button(
                                                [html.I(className="bi bi-check-circle", style={"marginRight": "6px"}), "Verify Code"],
                                                id="btn-telegram-verify",
                                                size="sm", color="success", outline=True,
                                                style={"marginBottom": "10px"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "12px"},
                                        children=[
                                            dbc.Button(
                                                [html.I(className="bi bi-cloud-download", style={"marginRight": "6px"}), "Ingest Messages"],
                                                id="btn-telegram-ingest",
                                                size="sm", color="primary",
                                                style={"background": COLORS["accent"], "border": "none"},
                                            ),
                                            html.Span(
                                                f"{counts.get('telegram', 0)} samples",
                                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot", color=COLORS["info"],
                                        children=[html.Div(id="telegram-status", style={"marginTop": "8px"})],
                                    ),
                                ],
                                border_color=COLORS["info"],
                            ),

                            # ── Slack ──
                            _channel_card(
                                "bi bi-slack", "Slack",
                                "Connect via Slack Bot Token to ingest your messages from all joined channels.",
                                [
                                    _field_input("slack-bot-token", "Bot Token (xoxb-...)", value=slack_token),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "10px"},
                                        children=[
                                            dbc.Button(
                                                [html.I(className="bi bi-plug", style={"marginRight": "6px"}), "Test Connection"],
                                                id="btn-slack-test",
                                                size="sm", color="secondary", outline=True,
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-cloud-download", style={"marginRight": "6px"}), "Ingest Messages"],
                                                id="btn-slack-ingest",
                                                size="sm", color="primary",
                                                style={"background": COLORS["accent"], "border": "none"},
                                            ),
                                            html.Span(
                                                f"{counts.get('slack', 0)} samples",
                                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot", color=COLORS["accent"],
                                        children=[html.Div(id="slack-status", style={"marginTop": "8px"})],
                                    ),
                                ],
                                border_color="#4A154B",
                            ),
                        ],
                        md=6,
                    ),

                    # Right column
                    dbc.Col(
                        [
                            # ── WhatsApp ──
                            _channel_card(
                                "bi bi-whatsapp", "WhatsApp",
                                "Upload a WhatsApp chat export (.txt) to ingest your messages.",
                                [
                                    html.P(
                                        "How to export: Open a chat in WhatsApp → Menu (⋮) → More → Export chat → Without media → save the .txt file.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "marginBottom": "12px",
                                               "background": COLORS["body_bg"], "padding": "10px", "borderRadius": "6px"},
                                    ),
                                    dcc.Upload(
                                        id="whatsapp-upload",
                                        children=html.Div([
                                            html.I(className="bi bi-cloud-arrow-up", style={"fontSize": "1.5rem", "marginRight": "8px"}),
                                            "Drop .txt export here or click to browse",
                                        ]),
                                        style={
                                            "width": "100%",
                                            "borderWidth": "2px",
                                            "borderStyle": "dashed",
                                            "borderColor": COLORS["border"],
                                            "borderRadius": "8px",
                                            "textAlign": "center",
                                            "padding": "20px",
                                            "color": COLORS["text_muted"],
                                            "cursor": "pointer",
                                            "marginBottom": "10px",
                                        },
                                        accept=".txt",
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                        children=[
                                            html.Span(
                                                f"{counts.get('whatsapp', 0)} samples",
                                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot", color=COLORS["success"],
                                        children=[html.Div(id="whatsapp-status", style={"marginTop": "8px"})],
                                    ),
                                ],
                                border_color=COLORS["success"],
                            ),

                            # ── Google Calendar ──
                            _channel_card(
                                "bi bi-calendar-event", "Google Calendar",
                                "Upload a Google Calendar export (.ics) to ingest event titles and descriptions.",
                                [
                                    html.P(
                                        "How to export: Google Calendar → Settings → Import & Export → Export → download .ics file.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "marginBottom": "12px",
                                               "background": COLORS["body_bg"], "padding": "10px", "borderRadius": "6px"},
                                    ),
                                    dcc.Upload(
                                        id="calendar-upload",
                                        children=html.Div([
                                            html.I(className="bi bi-cloud-arrow-up", style={"fontSize": "1.5rem", "marginRight": "8px"}),
                                            "Drop .ics file here or click to browse",
                                        ]),
                                        style={
                                            "width": "100%",
                                            "borderWidth": "2px",
                                            "borderStyle": "dashed",
                                            "borderColor": COLORS["border"],
                                            "borderRadius": "8px",
                                            "textAlign": "center",
                                            "padding": "20px",
                                            "color": COLORS["text_muted"],
                                            "cursor": "pointer",
                                            "marginBottom": "10px",
                                        },
                                        accept=".ics",
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                        children=[
                                            html.Span(
                                                f"{counts.get('calendar', 0)} samples",
                                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot", color=COLORS["warning"],
                                        children=[html.Div(id="calendar-status", style={"marginTop": "8px"})],
                                    ),
                                ],
                                border_color=COLORS["warning"],
                            ),
                        ],
                        md=6,
                    ),
                ],
            ),
        ]
    )


# ── Callbacks ──

# Gmail
@callback(
    Output("gmail-status", "children"),
    Input("btn-gmail-ingest", "n_clicks"),
    prevent_initial_call=True,
)
def handle_gmail(n_clicks):
    if not n_clicks:
        return no_update
    from services.channel_gmail import ingest
    result = ingest()
    if result.get("error"):
        return _status_badge(f"Ingested {result['ingested']} chunks. Error: {result['error']}", "warning")
    return _status_badge(f"Ingested {result['ingested']} sent mail chunks.", "success")


# Telegram — combined callback for auth flow + test + ingest
@callback(
    Output("telegram-status", "children"),
    Output("telegram-code-section", "style"),
    Output("telegram-auth-state", "data"),
    Input("btn-telegram-send-code", "n_clicks"),
    Input("btn-telegram-verify", "n_clicks"),
    Input("btn-telegram-test", "n_clicks"),
    Input("btn-telegram-ingest", "n_clicks"),
    State("telegram-api-id", "value"),
    State("telegram-api-hash", "value"),
    State("telegram-phone", "value"),
    State("telegram-code", "value"),
    State("telegram-auth-state", "data"),
    prevent_initial_call=True,
)
def handle_telegram(send_clicks, verify_clicks, test_clicks, ingest_clicks,
                    api_id, api_hash, phone, code, auth_state):
    triggered = dash.ctx.triggered_id
    hide = {"display": "none"}
    show = {"display": "block", "marginBottom": "10px"}

    if triggered == "btn-telegram-send-code" and send_clicks:
        # Save credentials
        if api_id:
            db.save_setting("telegram_api_id", str(api_id).strip())
        if api_hash:
            db.save_setting("telegram_api_hash", str(api_hash).strip())
        if phone:
            db.save_setting("telegram_phone", str(phone).strip())

        if not api_id or not api_hash or not phone:
            return _status_badge("Fill in API ID, API Hash, and Phone.", "warning"), hide, "idle"

        from services.channel_telegram import start_auth
        ok, msg = start_auth(str(phone).strip())
        if ok:
            return _status_badge(msg, "info"), show, "code_sent"
        return _status_badge(msg, "danger"), hide, "idle"

    if triggered == "btn-telegram-verify" and verify_clicks:
        if not code:
            return _status_badge("Enter the verification code.", "warning"), show, "code_sent"

        from services.channel_telegram import complete_auth
        ok, msg = complete_auth(str(code).strip())
        if ok:
            return _status_badge(msg, "success"), hide, "connected"
        return _status_badge(msg, "danger"), show, "code_sent"

    if triggered == "btn-telegram-test" and test_clicks:
        # Save credentials first
        if api_id:
            db.save_setting("telegram_api_id", str(api_id).strip())
        if api_hash:
            db.save_setting("telegram_api_hash", str(api_hash).strip())
        if phone:
            db.save_setting("telegram_phone", str(phone).strip())

        from services.channel_telegram import test_connection
        ok, msg = test_connection()
        color = "success" if ok else "warning"
        return _status_badge(msg, color), hide, "connected" if ok else auth_state

    if triggered == "btn-telegram-ingest" and ingest_clicks:
        from services.channel_telegram import ingest
        result = ingest()
        if result.get("error"):
            return _status_badge(f"Ingested {result['ingested']}. Error: {result['error']}", "warning"), hide, auth_state
        return _status_badge(f"Ingested {result['ingested']} message chunks.", "success"), hide, auth_state

    return no_update, hide, auth_state


# Slack
@callback(
    Output("slack-status", "children"),
    Input("btn-slack-test", "n_clicks"),
    Input("btn-slack-ingest", "n_clicks"),
    State("slack-bot-token", "value"),
    prevent_initial_call=True,
)
def handle_slack(test_clicks, ingest_clicks, token):
    triggered = dash.ctx.triggered_id

    if triggered == "btn-slack-test" and test_clicks:
        if token:
            db.save_setting("slack_bot_token", str(token).strip())
        from services.channel_slack import test_connection
        ok, msg = test_connection()
        return _status_badge(msg, "success" if ok else "danger")

    if triggered == "btn-slack-ingest" and ingest_clicks:
        if token:
            db.save_setting("slack_bot_token", str(token).strip())
        from services.channel_slack import ingest
        result = ingest()
        if result.get("error"):
            return _status_badge(f"Ingested {result['ingested']}. Error: {result['error']}", "warning")
        return _status_badge(f"Ingested {result['ingested']} message chunks.", "success")

    return no_update


# WhatsApp
@callback(
    Output("whatsapp-status", "children"),
    Input("whatsapp-upload", "contents"),
    State("whatsapp-upload", "filename"),
    prevent_initial_call=True,
)
def handle_whatsapp(contents, filename):
    if not contents:
        return no_update

    # Decode uploaded file
    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string).decode("utf-8", errors="replace")
    except Exception:
        return _status_badge("Failed to read file.", "danger")

    from services.channel_whatsapp import ingest
    result = ingest(decoded)
    if result.get("error"):
        return _status_badge(result["error"], "warning")
    return _status_badge(f"Ingested {result['ingested']} WhatsApp message chunks from {filename}.", "success")


# Calendar
@callback(
    Output("calendar-status", "children"),
    Input("calendar-upload", "contents"),
    State("calendar-upload", "filename"),
    prevent_initial_call=True,
)
def handle_calendar(contents, filename):
    if not contents:
        return no_update

    # Decode uploaded file
    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string).decode("utf-8", errors="replace")
    except Exception:
        return _status_badge("Failed to read file.", "danger")

    from services.channel_calendar import ingest
    result = ingest(decoded)
    if result.get("error"):
        return _status_badge(result["error"], "warning")
    return _status_badge(f"Ingested {result['ingested']} calendar event chunks from {filename}.", "success")
