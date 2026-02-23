"""
Setup page — company info, IMAP email connection, user preferences.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from config import COLORS
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
                                style={"borderRadius": "8px"},
                                className="dash-dropdown-dark",
                            ),
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
    State("setup-company-name", "value"),
    State("setup-industry", "value"),
    State("setup-imap-server", "value"),
    State("setup-imap-email", "value"),
    State("setup-imap-password", "value"),
    State("setup-user-name", "value"),
    State("setup-user-role", "value"),
    prevent_initial_call=True,
)
def complete_setup(n_clicks, company_name, industry, imap_server, imap_email, imap_password, user_name, user_role):
    if not n_clicks:
        return no_update

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
