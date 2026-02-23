"""
Setup page — company info, API key, IMAP email connection, user preferences.
"""

import os
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from config import COLORS, ANTHROPIC_API_KEY
import db

dash.register_page(__name__, path="/setup", name="Setup", order=9)


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


def _mask_key(key):
    """Show first 10 and last 4 chars of an API key, mask the rest."""
    if not key or len(key) < 20:
        return key or ""
    return key[:10] + "*" * (len(key) - 14) + key[-4:]


def layout():
    # Load saved settings
    imap_server = db.get_setting("imap_server", "imap.gmail.com")
    imap_email = db.get_setting("imap_email", "")
    imap_password = db.get_setting("imap_password", "")
    company_name = db.get_setting("company_name", "")
    industry = db.get_setting("industry", "")
    user_name = db.get_setting("user_name", "")
    user_role = db.get_setting("user_role", "")
    # API key: check DB first, then .env
    api_key = db.get_setting("anthropic_api_key") or ANTHROPIC_API_KEY
    has_key = bool(api_key)

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
                                style={"borderRadius": "8px"},
                                className="dash-dropdown-dark",
                            ),
                        ],
                    ),
                ],
            ),
            # Anthropic API Key
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
                            html.I(className="bi bi-key-fill", style={"marginRight": "10px"}),
                            "Anthropic API Key",
                        ],
                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                    ),
                    html.P(
                        [
                            "Your API key powers the AI assistant. Get one from ",
                            html.A(
                                "console.anthropic.com",
                                href="https://console.anthropic.com",
                                target="_blank",
                                style={"color": COLORS["accent"], "textDecoration": "underline"},
                            ),
                            ".",
                        ],
                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "12px"},
                    ),
                    # Status badge
                    html.Div(
                        style={"marginBottom": "12px"},
                        children=[
                            html.Span(
                                [
                                    html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px"}),
                                    f"Key configured: {_mask_key(api_key)}",
                                ],
                                style={"color": COLORS["success"], "fontSize": "0.82rem"},
                            ) if has_key else html.Span(
                                [
                                    html.I(className="bi bi-exclamation-triangle-fill", style={"marginRight": "6px"}),
                                    "No API key configured — AI features are disabled.",
                                ],
                                style={"color": COLORS["warning"], "fontSize": "0.82rem"},
                            ),
                        ],
                    ),
                    _input_field(
                        "API Key" if not has_key else "Update API Key",
                        "setup-api-key",
                        "sk-ant-api03-...",
                        "",
                        input_type="password",
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px", "alignItems": "center"},
                        children=[
                            dbc.Button(
                                [html.I(className="bi bi-shield-check", style={"marginRight": "6px"}), "Test Key"],
                                id="setup-test-api-btn",
                                size="sm",
                                outline=True,
                                color="warning",
                                style={"marginTop": "4px"},
                            ),
                            html.Div(id="setup-api-test-result", style={"marginTop": "8px"}),
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
                    _input_field("Email Address", "setup-imap-email", "you@gmail.com", imap_email),
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
    State("setup-api-key", "value"),
    State("setup-company-name", "value"),
    State("setup-industry", "value"),
    State("setup-imap-server", "value"),
    State("setup-imap-email", "value"),
    State("setup-imap-password", "value"),
    State("setup-user-name", "value"),
    State("setup-user-role", "value"),
    prevent_initial_call=True,
)
def complete_setup(n_clicks, api_key, company_name, industry, imap_server, imap_email, imap_password, user_name, user_role):
    if not n_clicks:
        return no_update

    # Save API key if a new one was entered
    if api_key and api_key.strip().startswith("sk-"):
        key = api_key.strip()
        db.save_setting("anthropic_api_key", key)
        # Also update .env for persistence across restarts
        _update_env_file("ANTHROPIC_API_KEY", key)

    db.save_setting("company_name", company_name or "")
    db.save_setting("industry", industry or "")
    db.save_setting("imap_server", imap_server or "imap.gmail.com")
    db.save_setting("imap_email", imap_email or "")
    db.save_setting("imap_password", imap_password or "")
    db.save_setting("user_name", user_name or "")
    db.save_setting("user_role", user_role or "")

    return html.Span(
        "Settings saved.",
        style={"color": COLORS["success"], "fontSize": "0.9rem"},
    )


def _update_env_file(key, value):
    """Update or add a key=value pair in the .env file."""
    from config import BASE_DIR
    env_path = os.path.join(BASE_DIR, ".env")
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)


@callback(
    Output("setup-api-test-result", "children"),
    Input("setup-test-api-btn", "n_clicks"),
    State("setup-api-key", "value"),
    prevent_initial_call=True,
)
def test_api_key(n_clicks, new_key):
    if not n_clicks:
        return no_update

    # Use the entered key if provided, otherwise the saved one
    key = (new_key.strip() if new_key and new_key.strip() else None) or db.get_setting("anthropic_api_key") or ANTHROPIC_API_KEY
    if not key:
        return html.Span(
            "No API key entered or saved.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        )

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        )
        return html.Span(
            [html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px"}), "API key is valid."],
            style={"color": COLORS["success"], "fontSize": "0.85rem"},
        )
    except Exception as e:
        return html.Span(
            [html.I(className="bi bi-x-circle-fill", style={"marginRight": "6px"}), f"Invalid: {str(e)[:80]}"],
            style={"color": COLORS["danger"], "fontSize": "0.85rem"},
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
