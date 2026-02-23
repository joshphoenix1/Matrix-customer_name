"""
Deploy Guide page — step-by-step deployment instructions for new EC2 instances.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from config import COLORS

dash.register_page(__name__, path="/deploy", name="Deploy", order=8)

# ── Reusable styles ──
CARD = {
    "background": COLORS["card_bg"],
    "borderRadius": "12px",
    "padding": "24px",
    "marginBottom": "20px",
}

CODE_BLOCK = {
    "background": "#0a0a16",
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "8px",
    "padding": "16px",
    "fontFamily": "'Fira Code', 'Cascadia Code', 'Consolas', monospace",
    "fontSize": "0.82rem",
    "color": COLORS["success"],
    "overflowX": "auto",
    "whiteSpace": "pre",
    "lineHeight": "1.7",
    "marginBottom": "12px",
}

STEP_NUM = {
    "width": "32px",
    "height": "32px",
    "borderRadius": "50%",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "fontWeight": "800",
    "fontSize": "0.85rem",
    "color": "#fff",
    "flexShrink": "0",
}

PREREQ_ITEM = {
    "display": "flex",
    "alignItems": "center",
    "gap": "10px",
    "padding": "8px 0",
    "borderBottom": f"1px solid {COLORS['border']}",
}


def _step_card(number, title, description, code, color=COLORS["accent"], note=None):
    """Render a numbered deployment step card."""
    children = [
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "12px"},
            children=[
                html.Div(str(number), style={**STEP_NUM, "background": color}),
                html.H4(title, style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.05rem"}),
            ],
        ),
        html.P(description, style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "12px", "lineHeight": "1.5"}),
    ]
    if code:
        children.append(html.Div(code, style=CODE_BLOCK))
    if note:
        children.append(
            html.Div(
                style={"display": "flex", "alignItems": "flex-start", "gap": "8px", "marginTop": "8px"},
                children=[
                    html.I(className="bi bi-info-circle-fill", style={"color": COLORS["info"], "fontSize": "0.85rem", "marginTop": "2px"}),
                    html.Span(note, style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "lineHeight": "1.4"}),
                ],
            )
        )
    return html.Div(style={**CARD, "borderLeft": f"4px solid {color}"}, children=children)


# ── One-liner commands ──
ONELINER_FULL = (
    'curl -sL https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | \\\n'
    '  ANTHROPIC_API_KEY="sk-ant-..." \\\n'
    '  APP_PORT=5003 \\\n'
    '  IMAP_EMAIL="you@gmail.com" \\\n'
    '  IMAP_PASSWORD="xxxx xxxx xxxx xxxx" \\\n'
    '  COMPANY_NAME="Acme Corp" \\\n'
    '  bash'
)

ONELINER_MANUAL = (
    'curl -sL https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | bash\n'
    'cd ~/matrix-ai\n'
    'nano deploy.conf    # fill in your credentials\n'
    './deploy.sh'
)


def layout():
    return html.Div(
        children=[
            # ── Header ──
            html.Div(
                style={
                    "background": f"linear-gradient(135deg, {COLORS['card_bg']} 0%, #1a2a1a 100%)",
                    "borderRadius": "16px",
                    "padding": "32px 40px",
                    "marginBottom": "28px",
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "8px"},
                        children=[
                            html.I(className="bi bi-rocket-takeoff-fill", style={"color": COLORS["success"], "fontSize": "1.8rem"}),
                            html.H1("Deploy Guide", style={"color": COLORS["text_primary"], "fontSize": "1.8rem", "margin": 0, "fontWeight": "800"}),
                        ],
                    ),
                    html.P(
                        "Deploy Matrix AI Assistant to a fresh EC2 instance in under 2 minutes.",
                        style={"color": COLORS["text_secondary"], "fontSize": "1rem", "margin": 0},
                    ),
                ],
            ),

            # ── Quick Deploy (one-liner) ──
            html.Div(
                style={
                    **CARD,
                    "borderLeft": f"4px solid {COLORS['success']}",
                    "background": f"linear-gradient(135deg, {COLORS['card_bg']} 0%, #0d1f0d 100%)",
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "12px"},
                        children=[
                            html.I(className="bi bi-lightning-charge-fill", style={"color": COLORS["success"], "fontSize": "1.2rem"}),
                            html.H3("Quick Deploy (One Command)", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        ],
                    ),
                    html.P(
                        "SSH into a fresh Ubuntu EC2 and paste this. Replace the values with your credentials.",
                        style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "12px"},
                    ),
                    html.Div(ONELINER_FULL, style={**CODE_BLOCK, "border": f"1px solid {COLORS['success']}"}),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "8px", "marginTop": "4px"},
                        children=[
                            html.I(className="bi bi-check-circle-fill", style={"color": COLORS["success"], "fontSize": "0.85rem"}),
                            html.Span(
                                "That's it. App will be live at http://<EC2_PUBLIC_IP>:5003",
                                style={"color": COLORS["success"], "fontSize": "0.85rem", "fontWeight": "600"},
                            ),
                        ],
                    ),
                ],
            ),

            # ── OR divider ──
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "16px", "margin": "8px 0 28px 0"},
                children=[
                    html.Hr(style={"flex": "1", "border": "none", "borderTop": f"1px solid {COLORS['border']}"}),
                    html.Span("OR STEP BY STEP", style={"color": COLORS["text_muted"], "fontSize": "0.75rem", "letterSpacing": "2px", "fontWeight": "700"}),
                    html.Hr(style={"flex": "1", "border": "none", "borderTop": f"1px solid {COLORS['border']}"}),
                ],
            ),

            # ── Prerequisites ──
            html.Div(
                style={**CARD, "borderLeft": f"4px solid {COLORS['info']}"},
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "16px"},
                        children=[
                            html.I(className="bi bi-clipboard-check-fill", style={"color": COLORS["info"], "fontSize": "1.1rem"}),
                            html.H3("Prerequisites", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        ],
                    ),
                    html.Div([
                        html.Div(style=PREREQ_ITEM, children=[
                            html.I(className="bi bi-cloud-fill", style={"color": COLORS["info"], "fontSize": "1rem"}),
                            html.Div([
                                html.Span("AWS EC2 Instance", style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600"}),
                                html.Span(" — Ubuntu 22.04/24.04 LTS, t3.small or larger, 20GB+ storage", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                            ]),
                        ]),
                        html.Div(style=PREREQ_ITEM, children=[
                            html.I(className="bi bi-shield-lock-fill", style={"color": COLORS["warning"], "fontSize": "1rem"}),
                            html.Div([
                                html.Span("Security Group", style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600"}),
                                html.Span(" — Inbound TCP port 5003 (or your APP_PORT) + SSH port 22", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                            ]),
                        ]),
                        html.Div(style=PREREQ_ITEM, children=[
                            html.I(className="bi bi-key-fill", style={"color": COLORS["accent"], "fontSize": "1rem"}),
                            html.Div([
                                html.Span("Anthropic API Key", style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600"}),
                                html.Span(" — From console.anthropic.com", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                            ]),
                        ]),
                        html.Div(style={**PREREQ_ITEM, "borderBottom": "none"}, children=[
                            html.I(className="bi bi-envelope-at-fill", style={"color": COLORS["success"], "fontSize": "1rem"}),
                            html.Div([
                                html.Span("Gmail App Password", style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600"}),
                                html.Span(" — Optional. For IMAP email scanning. Generate at myaccount.google.com/apppasswords", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                            ]),
                        ]),
                    ]),
                ],
            ),

            # ── Step-by-step ──
            _step_card(
                1,
                "Launch EC2 & SSH In",
                "Launch an Ubuntu instance in AWS Console, then connect via SSH.",
                "ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>",
                COLORS["accent"],
            ),

            _step_card(
                2,
                "Clone the Template",
                "Download the Matrix AI Assistant template from GitHub.",
                "git clone https://github.com/joshphoenix1/Matrix-customer_name.git ~/matrix-ai\ncd ~/matrix-ai",
                COLORS["info"],
                "Git is installed automatically by deploy.sh if missing.",
            ),

            _step_card(
                3,
                "Configure deploy.conf",
                "Open deploy.conf and fill in your API key, email credentials, and company info.",
                'nano deploy.conf\n\n# Required:\n#   ANTHROPIC_API_KEY="sk-ant-..."\n#\n# Optional (can configure in /setup later):\n#   IMAP_EMAIL="you@gmail.com"\n#   IMAP_PASSWORD="xxxx xxxx xxxx xxxx"\n#   COMPANY_NAME="Your Company"\n#   USER_NAME="Jane Doe"\n#   USER_ROLE="CEO"\n#   INDUSTRY="Technology / SaaS"',
                COLORS["warning"],
            ),

            _step_card(
                4,
                "Run the Deploy Script",
                "One command handles everything: system deps, Python venv, pip install, database init, systemd service.",
                "chmod +x deploy.sh\n./deploy.sh",
                COLORS["success"],
            ),

            _step_card(
                5,
                "Access Your Dashboard",
                "Open the URL shown at the end of deployment in your browser.",
                "http://<EC2_PUBLIC_IP>:5003",
                COLORS["accent"],
                "The app runs as a systemd service — it auto-restarts on crash and starts on boot. No babysitting needed.",
            ),

            # ── What the script does ──
            html.Div(
                style={**CARD, "borderLeft": f"4px solid {COLORS['text_muted']}"},
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "16px"},
                        children=[
                            html.I(className="bi bi-gear-wide-connected", style={"color": COLORS["text_muted"], "fontSize": "1.1rem"}),
                            html.H3("What deploy.sh Does Automatically", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        ],
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px"},
                        children=[
                            _auto_item("bi bi-box-seam", "Installs python3, pip, venv, lsof"),
                            _auto_item("bi bi-folder-plus", "Creates Python virtual environment"),
                            _auto_item("bi bi-download", "Installs all pip packages from requirements.txt"),
                            _auto_item("bi bi-file-lock", "Writes .env with your API key"),
                            _auto_item("bi bi-database-fill-gear", "Initializes SQLite database"),
                            _auto_item("bi bi-sliders", "Saves IMAP + branding settings to DB"),
                            _auto_item("bi bi-arrow-repeat", "Creates systemd service (auto-restart)"),
                            _auto_item("bi bi-check-circle", "Verifies deployment and shows URL"),
                        ],
                    ),
                ],
            ),

            # ── Management commands ──
            html.Div(
                style={**CARD, "borderLeft": f"4px solid {COLORS['accent']}"},
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "16px"},
                        children=[
                            html.I(className="bi bi-terminal-fill", style={"color": COLORS["accent"], "fontSize": "1.1rem"}),
                            html.H3("Management Commands", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        ],
                    ),
                    html.Div(
                        "# Check status\n"
                        "sudo systemctl status matrix-ai-5003\n\n"
                        "# View live logs\n"
                        "sudo journalctl -u matrix-ai-5003 -f\n\n"
                        "# Restart\n"
                        "sudo systemctl restart matrix-ai-5003\n\n"
                        "# Stop\n"
                        "sudo systemctl stop matrix-ai-5003\n\n"
                        "# Pull updates & redeploy\n"
                        "cd ~/matrix-ai && git pull && ./deploy.sh",
                        style=CODE_BLOCK,
                    ),
                ],
            ),

            # ── Config Reference ──
            html.Div(
                style={**CARD, "borderLeft": f"4px solid {COLORS['warning']}"},
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "16px"},
                        children=[
                            html.I(className="bi bi-file-earmark-code-fill", style={"color": COLORS["warning"], "fontSize": "1.1rem"}),
                            html.H3("deploy.conf Reference", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        ],
                    ),
                    _config_table(),
                ],
            ),
        ]
    )


def _auto_item(icon, text):
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "10px", "padding": "6px 0"},
        children=[
            html.I(className=icon, style={"color": COLORS["success"], "fontSize": "0.9rem", "width": "20px", "textAlign": "center"}),
            html.Span(text, style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
        ],
    )


def _config_table():
    rows = [
        ("APP_PORT", "5003", "Port the app runs on", True),
        ("ANTHROPIC_API_KEY", "sk-ant-...", "Claude API key", True),
        ("IMAP_SERVER", "imap.gmail.com", "IMAP server hostname", False),
        ("IMAP_EMAIL", "", "Email address for inbox scanning", False),
        ("IMAP_PASSWORD", "", "Gmail App Password (16 chars)", False),
        ("COMPANY_NAME", "", "Your company name", False),
        ("USER_NAME", "", "Your name", False),
        ("USER_ROLE", "", "Your role (CEO, etc.)", False),
        ("INDUSTRY", "", "Your industry vertical", False),
    ]

    header = html.Div(
        style={"display": "grid", "gridTemplateColumns": "2fr 2fr 3fr 1fr", "gap": "8px", "padding": "8px 12px", "background": "#0a0a16", "borderRadius": "8px 8px 0 0", "borderBottom": f"1px solid {COLORS['border']}"},
        children=[
            html.Span("Variable", style={"color": COLORS["accent"], "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.Span("Default", style={"color": COLORS["accent"], "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.Span("Description", style={"color": COLORS["accent"], "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.Span("Required", style={"color": COLORS["accent"], "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase", "letterSpacing": "1px"}),
        ],
    )

    items = [header]
    for var, default, desc, required in rows:
        items.append(
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "2fr 2fr 3fr 1fr", "gap": "8px", "padding": "8px 12px", "borderBottom": f"1px solid {COLORS['border']}"},
                children=[
                    html.Span(var, style={"color": COLORS["success"], "fontSize": "0.82rem", "fontFamily": "monospace", "fontWeight": "600"}),
                    html.Span(default or "—", style={"color": COLORS["text_muted"], "fontSize": "0.82rem", "fontFamily": "monospace"}),
                    html.Span(desc, style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                    html.Span(
                        "Yes" if required else "No",
                        style={"color": COLORS["danger"] if required else COLORS["text_muted"], "fontSize": "0.82rem", "fontWeight": "600" if required else "400"},
                    ),
                ],
            )
        )
    return html.Div(items, style={"border": f"1px solid {COLORS['border']}", "borderRadius": "8px", "overflow": "hidden"})
