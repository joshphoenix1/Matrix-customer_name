"""
Setup page — company info, IMAP email connection, user preferences, dashboard login.
"""

import os
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from config import COLORS
import db

dash.register_page(__name__, path="/setup", name="Setup", order=14)


def _input_field(label, input_id, placeholder="", value="", input_type="text"):
    return html.Div(
        style={"marginBottom": "16px"},
        children=[
            html.Label(
                label,
                style={
                    "color": COLORS["text_secondary"],
                    "fontSize": "0.85rem",
                    "marginBottom": "6px",
                    "display": "block",
                },
            ),
            dbc.Input(
                id=input_id,
                type=input_type,
                placeholder=placeholder,
                value=value,
                style={
                    "background": COLORS["body_bg"],
                    "border": f"1px solid {COLORS['border']}",
                    "color": COLORS["text_primary"],
                    "borderRadius": "8px",
                },
            ),
        ],
    )


INDUSTRY_OPTIONS = [
    "Technology / SaaS",
    "Financial Services",
    "Healthcare / Biotech",
    "Real Estate",
    "E-Commerce / Retail",
    "Manufacturing",
    "Professional Services / Consulting",
    "Media / Entertainment",
    "Education",
    "Energy / Cleantech",
    "Legal",
    "Logistics / Supply Chain",
    "Nonprofit / NGO",
    "Government / Public Sector",
    "Other",
]


def layout():
    # Load saved settings
    imap_server = db.get_setting("imap_server", "imap.gmail.com")
    imap_email = db.get_setting("imap_email", "")
    imap_password = db.get_setting("imap_password", "")
    company_name = db.get_setting("company_name", "")
    industry = db.get_setting("industry", "")
    user_name = db.get_setting("user_name", "")
    user_role = db.get_setting("user_role", "")

    return html.Div(
        children=[
            html.Div(
                style={"marginBottom": "24px"},
                children=[
                    html.H2("Setup", style={"color": COLORS["text_primary"], "margin": 0}),
                    html.P(
                        "Configure your assistant, email connection, and preferences.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                    ),
                ],
            ),
            # Company Info
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginBottom": "20px",
                    "borderLeft": f"4px solid {COLORS['accent']}",
                },
                children=[
                    html.H4("Company Info", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                    _input_field("Company Name", "setup-company-name", "Your company name", company_name),
                    html.Div(
                        style={"marginBottom": "16px"},
                        children=[
                            html.Label(
                                "Industry",
                                style={
                                    "color": COLORS["text_secondary"],
                                    "fontSize": "0.85rem",
                                    "marginBottom": "6px",
                                    "display": "block",
                                },
                            ),
                            dcc.Dropdown(
                                id="setup-industry",
                                options=[{"label": i, "value": i} for i in INDUSTRY_OPTIONS],
                                value=industry or None,
                                placeholder="Select your industry...",
                            ),
                        ],
                    ),
                ],
            ),
            # Claude AI Authentication
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginBottom": "20px",
                    "borderLeft": f"4px solid {COLORS['warning']}",
                },
                children=[
                    html.H4(
                        [
                            html.I(className="bi bi-key", style={"marginRight": "10px"}),
                            "Claude AI Authentication",
                        ],
                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                    ),
                    html.P(
                        "Connect to Claude AI for persona analysis, draft generation, and email triage. "
                        "Two options are supported:",
                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "8px"},
                    ),
                    html.Div(
                        style={
                            "background": COLORS["body_bg"],
                            "borderRadius": "8px",
                            "padding": "12px",
                            "marginBottom": "16px",
                            "fontSize": "0.8rem",
                        },
                        children=[
                            html.P([
                                html.Strong("Option 1 — Claude Code Subscription", style={"color": COLORS["accent"]}),
                                html.Span(" (Pro/Max plan)", style={"color": COLORS["text_muted"]}),
                            ], style={"margin": "0 0 4px 0", "color": COLORS["text_secondary"]}),
                            html.P(
                                "Run 'claude setup-token' in your terminal to get a long-lived token. "
                                "Paste the refresh token (sk-ant-ort01-...) or access token (sk-ant-oat01-...). "
                                "Refresh tokens auto-renew; access tokens expire after 8 hours.",
                                style={"margin": "0 0 12px 0", "color": COLORS["text_muted"]},
                            ),
                            html.P([
                                html.Strong("Option 2 — Anthropic API Key", style={"color": COLORS["info"]}),
                                html.Span(" (pay-per-use)", style={"color": COLORS["text_muted"]}),
                            ], style={"margin": "0 0 4px 0", "color": COLORS["text_secondary"]}),
                            html.P(
                                "Get an API key from console.anthropic.com (sk-ant-api03-...). "
                                "Usage is billed per token.",
                                style={"margin": "0", "color": COLORS["text_muted"]},
                            ),
                        ],
                    ),
                    _input_field("API Key or Token", "setup-api-key", "sk-ant-...", db.get_setting("anthropic_api_key") or db.get_setting("claude_refresh_token") or "", input_type="password"),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "12px", "marginTop": "4px"},
                        children=[
                            dbc.Button(
                                [html.I(className="bi bi-check-circle", style={"marginRight": "6px"}), "Test Connection"],
                                id="setup-test-api-key-btn",
                                size="sm",
                                outline=True,
                                color="warning",
                            ),
                            html.Div(id="setup-api-key-test-result"),
                        ],
                    ),
                ],
            ),
            # Email Inbox Connection
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginBottom": "20px",
                    "borderLeft": f"4px solid {COLORS['info']}",
                },
                children=[
                    html.H4(
                        [
                            html.I(className="bi bi-envelope-open-fill", style={"marginRight": "10px"}),
                            "Email Inbox Connection",
                        ],
                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                    ),
                    html.P(
                        "Connect your email inbox via IMAP to scan and AI-analyse incoming emails. For Gmail, use an App Password.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"},
                    ),
                    _input_field("IMAP Server", "setup-imap-server", "imap.gmail.com", imap_server),
                    _input_field("Email Address", "setup-imap-email", "Enter your email address", imap_email),
                    _input_field("App Password", "setup-imap-password", "Your app password", imap_password, input_type="password"),
                    html.Div(id="setup-imap-test-result", style={"marginTop": "8px"}),
                    dbc.Button(
                        [html.I(className="bi bi-plug", style={"marginRight": "6px"}), "Test Connection"],
                        id="setup-test-imap-btn",
                        size="sm",
                        outline=True,
                        color="info",
                        style={"marginTop": "4px"},
                    ),
                ],
            ),
            # SMTP Outgoing Email
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginBottom": "20px",
                    "borderLeft": f"4px solid {COLORS['accent']}",
                },
                children=[
                    html.H4(
                        [
                            html.I(className="bi bi-send-fill", style={"marginRight": "10px"}),
                            "SMTP Outgoing Email",
                        ],
                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                    ),
                    html.P(
                        "Configure SMTP to send emails (drafts, auto-replies). Defaults to your IMAP credentials if left blank. For Gmail, use smtp.gmail.com port 587.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"},
                    ),
                    _input_field("SMTP Server", "setup-smtp-server", "smtp.gmail.com", db.get_setting("smtp_server", "")),
                    _input_field("SMTP Port", "setup-smtp-port", "587", db.get_setting("smtp_port", "587")),
                    _input_field("SMTP Email", "setup-smtp-email", "Uses IMAP email if blank", db.get_setting("smtp_email", "")),
                    _input_field("SMTP Password", "setup-smtp-password", "Uses IMAP password if blank", db.get_setting("smtp_password", ""), input_type="password"),
                    html.Div(id="setup-smtp-test-result", style={"marginTop": "8px"}),
                    dbc.Button(
                        [html.I(className="bi bi-plug", style={"marginRight": "6px"}), "Test SMTP"],
                        id="setup-test-smtp-btn",
                        size="sm",
                        outline=True,
                        color="primary",
                        style={"marginTop": "4px"},
                    ),
                ],
            ),
            # Your Info
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginBottom": "20px",
                    "borderLeft": f"4px solid {COLORS['success']}",
                },
                children=[
                    html.H4("Your Info", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                    _input_field("Your Name", "setup-user-name", "Jane Doe", user_name),
                    _input_field("Your Role", "setup-user-role", "CEO / Founder", user_role),
                ],
            ),
            # Dashboard Login / Password Change
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginBottom": "20px",
                    "borderLeft": f"4px solid {COLORS['danger']}",
                },
                children=[
                    html.H4(
                        [
                            html.I(className="bi bi-shield-lock-fill", style={"marginRight": "10px"}),
                            "Dashboard Login",
                        ],
                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                    ),
                    html.P(
                        "Change the username and password used to log into this dashboard.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"},
                    ),
                    _input_field("Username", "setup-auth-username", "Enter new username", db.get_setting("auth_username", "")),
                    _input_field("Current Password", "setup-auth-current-pw", "Enter current password", "", input_type="password"),
                    _input_field("New Password", "setup-auth-new-pw", "Enter new password", "", input_type="password"),
                    _input_field("Confirm New Password", "setup-auth-confirm-pw", "Confirm new password", "", input_type="password"),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "12px", "marginTop": "8px"},
                        children=[
                            dbc.Button(
                                [html.I(className="bi bi-key-fill", style={"marginRight": "6px"}), "Update Login"],
                                id="setup-update-login-btn",
                                size="sm",
                                color="danger",
                                outline=True,
                            ),
                            html.Div(id="setup-login-update-status"),
                        ],
                    ),
                ],
            ),
            # Save button + status
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "16px"},
                children=[
                    dbc.Button(
                        [html.I(className="bi bi-check-lg", style={"marginRight": "6px"}), "Save Settings"],
                        id="setup-save-btn",
                        color="primary",
                        style={"background": COLORS["accent"], "border": "none"},
                    ),
                    html.Div(id="setup-save-status"),
                ],
            ),
        ]
    )


# ── Callbacks ──

@callback(
    Output("setup-save-status", "children"),
    Input("setup-save-btn", "n_clicks"),
    State("setup-company-name", "value"),
    State("setup-industry", "value"),
    State("setup-api-key", "value"),
    State("setup-imap-server", "value"),
    State("setup-imap-email", "value"),
    State("setup-imap-password", "value"),
    State("setup-smtp-server", "value"),
    State("setup-smtp-port", "value"),
    State("setup-smtp-email", "value"),
    State("setup-smtp-password", "value"),
    State("setup-user-name", "value"),
    State("setup-user-role", "value"),
    prevent_initial_call=True,
)
def complete_setup(n_clicks, company_name, industry, api_key, imap_server, imap_email, imap_password,
                   smtp_server, smtp_port, smtp_email, smtp_password, user_name, user_role):
    if not n_clicks:
        return no_update

    db.save_setting("company_name", company_name or "")
    db.save_setting("industry", industry or "")
    if api_key is not None:
        key = (api_key or "").strip()
        if key.startswith("sk-ant-ort"):
            db.save_setting("claude_refresh_token", key)
        elif key:
            db.save_setting("anthropic_api_key", key)
    db.save_setting("imap_server", imap_server or "imap.gmail.com")
    db.save_setting("imap_email", imap_email or "")
    db.save_setting("imap_password", imap_password or "")
    db.save_setting("smtp_server", smtp_server or "")
    db.save_setting("smtp_port", smtp_port or "587")
    db.save_setting("smtp_email", smtp_email or "")
    db.save_setting("smtp_password", smtp_password or "")
    db.save_setting("user_name", user_name or "")
    db.save_setting("user_role", user_role or "")

    return html.Span(
        "Settings saved.",
        style={"color": COLORS["success"], "fontSize": "0.9rem"},
    )


@callback(
    Output("setup-imap-test-result", "children"),
    Input("setup-test-imap-btn", "n_clicks"),
    State("setup-imap-server", "value"),
    State("setup-imap-email", "value"),
    State("setup-imap-password", "value"),
    prevent_initial_call=True,
)
def test_imap(n_clicks, server, email, password):
    if not n_clicks:
        return no_update

    if not server or not email or not password:
        return html.Span(
            "Please fill in all IMAP fields first.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    from services.email_ingestion import test_imap_connection
    success, message = test_imap_connection(server, email, password)

    if success:
        return html.Span(
            [html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px"}), message],
            style={"color": COLORS["success"], "fontSize": "0.85rem"},
        )
    else:
        return html.Span(
            [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), message],
            style={"color": COLORS["danger"], "fontSize": "0.85rem"},
        )


@callback(
    Output("setup-api-key-test-result", "children"),
    Input("setup-test-api-key-btn", "n_clicks"),
    State("setup-api-key", "value"),
    prevent_initial_call=True,
)
def test_api_key(n_clicks, api_key):
    if not n_clicks:
        return no_update

    if not api_key or not api_key.strip():
        return html.Span(
            "Please enter a key or token first.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    key = api_key.strip()

    # Detect token type and save appropriately
    if key.startswith("sk-ant-ort"):
        # Refresh token — save as refresh token, will exchange for access token
        db.save_setting("claude_refresh_token", key)
    else:
        db.save_setting("anthropic_api_key", key)

    from services.claude_auth import test_credentials
    success, message, token_type = test_credentials(key)

    type_labels = {
        "api_key": "API Key",
        "oauth": "OAuth Token",
        "oauth_refresh": "Refresh Token (auto-renewing)",
        "refresh_token": "Refresh Token",
    }
    type_label = type_labels.get(token_type, token_type)

    if success:
        return html.Span(
            [
                html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px"}),
                f"Claude connected via {type_label}.",
            ],
            style={"color": COLORS["success"], "fontSize": "0.85rem"},
        )
    else:
        return html.Span(
            [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), message],
            style={"color": COLORS["danger"], "fontSize": "0.85rem"},
        )


@callback(
    Output("setup-smtp-test-result", "children"),
    Input("setup-test-smtp-btn", "n_clicks"),
    State("setup-smtp-server", "value"),
    State("setup-smtp-port", "value"),
    State("setup-smtp-email", "value"),
    State("setup-smtp-password", "value"),
    State("setup-imap-email", "value"),
    State("setup-imap-password", "value"),
    prevent_initial_call=True,
)
def test_smtp(n_clicks, server, port, email, password, imap_email, imap_password):
    if not n_clicks:
        return no_update

    smtp_server = server or "smtp.gmail.com"
    smtp_port = port or "587"
    smtp_email = email or imap_email
    smtp_password = password or imap_password

    if not smtp_email or not smtp_password:
        return html.Span(
            "Please fill in SMTP credentials or configure IMAP first.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    from services.email_sender import test_smtp_connection
    success, message = test_smtp_connection(smtp_server, smtp_port, smtp_email, smtp_password)

    if success:
        return html.Span(
            [html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px"}), message],
            style={"color": COLORS["success"], "fontSize": "0.85rem"},
        )
    else:
        return html.Span(
            [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), message],
            style={"color": COLORS["danger"], "fontSize": "0.85rem"},
        )


@callback(
    Output("setup-login-update-status", "children"),
    Input("setup-update-login-btn", "n_clicks"),
    State("setup-auth-username", "value"),
    State("setup-auth-current-pw", "value"),
    State("setup-auth-new-pw", "value"),
    State("setup-auth-confirm-pw", "value"),
    prevent_initial_call=True,
)
def update_login_credentials(n_clicks, username, current_pw, new_pw, confirm_pw):
    if not n_clicks:
        return no_update

    if not username or not username.strip():
        return html.Span(
            "Username is required.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    if not new_pw:
        return html.Span(
            "New password is required.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    if new_pw != confirm_pw:
        return html.Span(
            [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), "New passwords do not match."],
            style={"color": COLORS["danger"], "fontSize": "0.85rem"},
        )

    if len(new_pw) < 4:
        return html.Span(
            "Password must be at least 4 characters.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    # Verify current password (DB credentials or env-var defaults)
    stored_user = db.get_setting("auth_username")
    if stored_user:
        # DB credentials exist — verify current password against hash
        result = db.verify_auth_credentials(stored_user, current_pw or "")
        if not result:
            return html.Span(
                [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), "Current password is incorrect."],
                style={"color": COLORS["danger"], "fontSize": "0.85rem"},
            )
    else:
        # No DB credentials yet — verify against env-var defaults
        env_user = os.getenv("AUTH_USERNAME", "matrix")
        env_pass = os.getenv("AUTH_PASSWORD", "morpheus")
        if (current_pw or "") != env_pass:
            return html.Span(
                [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), "Current password is incorrect."],
                style={"color": COLORS["danger"], "fontSize": "0.85rem"},
            )

    # Save new credentials
    db.save_auth_credentials(username.strip(), new_pw)

    return html.Span(
        [html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px"}),
         "Login credentials updated. Clear browser cache or open a new private window to use the new credentials."],
        style={"color": COLORS["success"], "fontSize": "0.85rem"},
    )
