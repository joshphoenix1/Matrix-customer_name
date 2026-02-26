"""
Matrix AI Assistant — Deployment Guide
Standalone Dash app on port 5005.
Run: python deployment_guide.py
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    title="Matrix AI — Deployment Guide",
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
)

COLORS = {
    "body_bg": "#0D0D1A",
    "card_bg": "#1E1E2E",
    "sidebar_bg": "#161625",
    "text_primary": "#FAFAFA",
    "text_secondary": "#B2BEC3",
    "text_muted": "#636E72",
    "accent": "#6C5CE7",
    "success": "#00B894",
    "warning": "#FDCB6E",
    "danger": "#D63031",
    "info": "#0984E3",
    "border": "#2D3436",
    "code_bg": "#141422",
}


def _section(title, icon, color, children, section_id=""):
    return html.Div(
        id=section_id,
        style={
            "background": COLORS["card_bg"],
            "borderRadius": "12px",
            "padding": "28px",
            "marginBottom": "24px",
            "borderLeft": f"4px solid {color}",
        },
        children=[
            html.H3(
                [html.I(className=f"bi {icon}", style={"marginRight": "12px"}), title],
                style={"color": COLORS["text_primary"], "marginBottom": "16px"},
            ),
            *children,
        ],
    )


def _text(content):
    return html.P(
        content,
        style={"color": COLORS["text_secondary"], "fontSize": "0.92rem", "lineHeight": "1.7", "marginBottom": "12px"},
    )


def _code(content, language="bash"):
    return html.Pre(
        html.Code(content),
        style={
            "background": COLORS["code_bg"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "8px",
            "padding": "16px",
            "color": COLORS["success"],
            "fontSize": "0.82rem",
            "overflowX": "auto",
            "marginBottom": "16px",
            "lineHeight": "1.6",
        },
    )


def _step(number, title, description, details=None, code=None, warning=None, result=None):
    children = [
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "12px"},
            children=[
                html.Span(
                    str(number),
                    style={
                        "background": COLORS["accent"],
                        "color": "#fff",
                        "borderRadius": "50%",
                        "width": "32px",
                        "height": "32px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "800",
                        "fontSize": "0.85rem",
                        "flexShrink": "0",
                    },
                ),
                html.H5(title, style={"color": COLORS["text_primary"], "margin": 0}),
            ],
        ),
        _text(description),
    ]
    if details:
        children.append(html.Ul(
            [html.Li(d, style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}) for d in details],
            style={"marginBottom": "12px"},
        ))
    if code:
        children.append(_code(code))
    if warning:
        children.append(html.Div(
            [html.I(className="bi bi-exclamation-triangle-fill", style={"marginRight": "8px"}), warning],
            style={
                "background": "rgba(253,203,110,0.1)",
                "border": f"1px solid {COLORS['warning']}",
                "borderRadius": "8px",
                "padding": "12px",
                "color": COLORS["warning"],
                "fontSize": "0.85rem",
                "marginBottom": "12px",
            },
        ))
    if result:
        children.append(html.Div(
            [html.I(className="bi bi-check-circle-fill", style={"marginRight": "8px"}), result],
            style={
                "color": COLORS["success"],
                "fontSize": "0.85rem",
                "marginTop": "8px",
            },
        ))
    return html.Div(
        style={
            "background": "rgba(108,92,231,0.03)",
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "10px",
            "padding": "20px",
            "marginBottom": "16px",
        },
        children=children,
    )


def _nav_link(label, href):
    return html.A(
        label,
        href=href,
        style={
            "color": COLORS["text_secondary"],
            "textDecoration": "none",
            "display": "block",
            "padding": "6px 0",
            "fontSize": "0.85rem",
            "borderLeft": f"2px solid transparent",
            "paddingLeft": "12px",
        },
    )


app.layout = html.Div(
    style={
        "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "background": COLORS["body_bg"],
        "minHeight": "100vh",
        "display": "flex",
    },
    children=[
        # ── Sidebar nav ──
        html.Div(
            style={
                "width": "240px",
                "background": COLORS["sidebar_bg"],
                "padding": "32px 20px",
                "position": "fixed",
                "top": 0,
                "left": 0,
                "bottom": 0,
                "overflowY": "auto",
                "borderRight": f"1px solid {COLORS['border']}",
            },
            children=[
                html.Div(
                    style={"marginBottom": "28px"},
                    children=[
                        html.H4("Deployment Guide", style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.1rem"}),
                        html.P("Matrix AI Assistant", style={"color": COLORS["text_muted"], "fontSize": "0.78rem", "margin": "4px 0 0 0"}),
                    ],
                ),
                html.Hr(style={"borderColor": COLORS["border"], "margin": "0 0 16px 0"}),
                html.P("Sections", style={"color": COLORS["text_muted"], "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "1px", "marginBottom": "8px"}),
                _nav_link("Overview", "#overview"),
                _nav_link("Prerequisites", "#prereqs"),
                _nav_link("Option A: One-Liner", "#option-a"),
                _nav_link("Option B: Manual", "#option-b"),
                _nav_link("What Happens (11 Steps)", "#steps"),
                _nav_link("Architecture Diagram", "#architecture"),
                _nav_link("After Deployment", "#after"),
                _nav_link("Multi-Tenant at Scale", "#scaling"),
                _nav_link("Troubleshooting", "#troubleshooting"),
                _nav_link("Rollback", "#rollback"),
            ],
        ),
        # ── Main content ──
        html.Div(
            style={
                "marginLeft": "240px",
                "padding": "40px 48px",
                "maxWidth": "920px",
                "width": "100%",
            },
            children=[
                # ── Header ──
                html.Div(
                    style={"marginBottom": "32px"},
                    children=[
                        html.H1(
                            [html.I(className="bi bi-rocket-takeoff-fill", style={"marginRight": "16px"}), "Deployment Guide"],
                            style={"color": COLORS["text_primary"], "fontWeight": "800"},
                        ),
                        html.P(
                            "Complete guide to deploying Matrix AI Assistant for a new customer — from a blank EC2 to a live, HTTPS-secured dashboard.",
                            style={"color": COLORS["text_muted"], "fontSize": "1rem", "maxWidth": "700px"},
                        ),
                    ],
                ),

                # ══════════════════════════════════════════════════
                # OVERVIEW
                # ══════════════════════════════════════════════════
                _section("Overview", "bi-info-circle-fill", COLORS["info"], [
                    _text("Each customer gets their own EC2 instance running a dedicated Matrix AI Assistant. The deployment is fully automated — a single command clones the template repo, installs all dependencies, configures HTTPS, and starts the app."),
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "1fr 1fr",
                            "gap": "12px",
                            "marginTop": "12px",
                        },
                        children=[
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px", "textAlign": "center"}, children=[
                                html.Div("10–15 min", style={"color": COLORS["accent"], "fontWeight": "800", "fontSize": "1.3rem"}),
                                html.Div("Deploy time", style={"color": COLORS["text_muted"], "fontSize": "0.78rem"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px", "textAlign": "center"}, children=[
                                html.Div("HTTPS", style={"color": COLORS["warning"], "fontWeight": "800", "fontSize": "1.3rem"}),
                                html.Div("Auto-renewing SSL", style={"color": COLORS["text_muted"], "fontSize": "0.78rem"}),
                            ]),
                        ],
                    ),
                ], section_id="overview"),

                # ══════════════════════════════════════════════════
                # PREREQUISITES
                # ══════════════════════════════════════════════════
                _section("Prerequisites", "bi-clipboard-check-fill", COLORS["warning"], [
                    html.H5("Before you start, you need:", style={"color": COLORS["text_primary"], "marginBottom": "12px"}),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
                        children=[
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div([html.I(className="bi bi-cloud", style={"marginRight": "8px", "color": COLORS["info"]}), "Fresh EC2 Instance"], style={"color": COLORS["text_primary"], "fontWeight": "600", "marginBottom": "8px"}),
                                html.Ul([
                                    html.Li("Ubuntu 22.04 or 24.04", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("t3.small or larger (2 GB RAM min)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("20 GB storage minimum", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                ], style={"marginBottom": 0, "paddingLeft": "20px"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div([html.I(className="bi bi-shield-lock", style={"marginRight": "8px", "color": COLORS["warning"]}), "Security Group"], style={"color": COLORS["text_primary"], "fontWeight": "600", "marginBottom": "8px"}),
                                html.Ul([
                                    html.Li("Port 22 (SSH)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("Port 80 (HTTP — redirects to HTTPS)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("Port 443 (HTTPS)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                ], style={"marginBottom": 0, "paddingLeft": "20px"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div([html.I(className="bi bi-globe", style={"marginRight": "8px", "color": COLORS["success"]}), "DNS Record"], style={"color": COLORS["text_primary"], "fontWeight": "600", "marginBottom": "8px"}),
                                html.Ul([
                                    html.Li("A record: clientname.yourdomain.com", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("Points to the EC2 public IP", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("Must be live BEFORE deploying", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                ], style={"marginBottom": 0, "paddingLeft": "20px"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div([html.I(className="bi bi-key", style={"marginRight": "8px", "color": COLORS["danger"]}), "Credentials & S3"], style={"color": COLORS["text_primary"], "fontWeight": "600", "marginBottom": "8px"}),
                                html.Ul([
                                    html.Li("GitHub PAT (for private repo)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("Anthropic API key (sk-ant-...)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("S3 bucket with wildcard cert (fullchain.pem + privkey.pem)", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                    html.Li("IAM role: s3:GetObject, ec2:AllocateAddress, ec2:AssociateAddress, ec2:DescribeAddresses", style={"color": COLORS["text_secondary"], "fontSize": "0.82rem"}),
                                ], style={"marginBottom": 0, "paddingLeft": "20px"}),
                            ]),
                        ],
                    ),
                ], section_id="prereqs"),

                # ══════════════════════════════════════════════════
                # OPTION A: ONE-LINER
                # ══════════════════════════════════════════════════
                _section("Option A: One-Liner Bootstrap (Recommended)", "bi-lightning-fill", COLORS["accent"], [
                    _text("SSH into the fresh EC2 and paste this single command. It clones the repo, writes the config, and runs the full deployment automatically."),
                    _code('''curl -sL -H "Authorization: token YOUR_GITHUB_PAT" \\
  https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | \\
  GITHUB_PAT="YOUR_GITHUB_PAT" \\
  ANTHROPIC_API_KEY="sk-ant-api03-..." \\
  APP_PORT=5003 \\
  DOMAIN_NAME="acme.matrixai.app" \\
  SSL_CERT_BUCKET="s3://matrix-ai-certs/wildcard" \\
  bash'''),
                    html.H5("What this does:", style={"color": COLORS["text_primary"], "marginTop": "16px", "marginBottom": "8px"}),
                    html.Ol([
                        html.Li("Installs git + AWS CLI if missing", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Allocates an Elastic IP (static public IP that survives stop/start)", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Clones the template repo into ~/matrix-ai", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Writes deploy.conf from the env vars you passed", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Runs deploy.sh (which does the 11 steps below)", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                    ]),
                    html.Div(
                        [html.I(className="bi bi-info-circle-fill", style={"marginRight": "8px"}),
                         "All parameters except GITHUB_PAT and ANTHROPIC_API_KEY are optional. The customer configures company info, email, and login from the /setup page after deployment."],
                        style={
                            "background": "rgba(9,132,227,0.1)",
                            "border": f"1px solid {COLORS['info']}",
                            "borderRadius": "8px",
                            "padding": "12px",
                            "color": COLORS["info"],
                            "fontSize": "0.85rem",
                        },
                    ),
                ], section_id="option-a"),

                # ══════════════════════════════════════════════════
                # OPTION B: MANUAL
                # ══════════════════════════════════════════════════
                _section("Option B: Manual Deployment", "bi-terminal-fill", COLORS["text_muted"], [
                    _text("If you prefer manual control, clone the repo, edit the config file, and run the deploy script separately."),
                    _code('''# 1. Clone the repo
git clone https://YOUR_PAT@github.com/joshphoenix1/Matrix-customer_name.git ~/matrix-ai
cd ~/matrix-ai

# 2. Edit the config
nano deploy.conf
# Fill in: ANTHROPIC_API_KEY, DOMAIN_NAME, SSL_CERT_BUCKET

# 3. Deploy
./deploy.sh'''),
                ], section_id="option-b"),

                # ══════════════════════════════════════════════════
                # WHAT HAPPENS — 11 STEPS
                # ══════════════════════════════════════════════════
                _section("What Happens: The 11 Deployment Steps", "bi-list-ol", COLORS["accent"], [
                    _text("When deploy.sh runs with a DOMAIN_NAME set, it executes 11 steps. Without a domain, it runs 8 steps (HTTP only). Here is exactly what each step does:"),

                    _step(1, "Install System Dependencies",
                        "Updates apt and installs the base packages needed to run the application.",
                        details=[
                            "python3, python3-venv, python3-pip — Python runtime and package management",
                            "lsof, curl — port checking and HTTP utilities",
                            "nginx — reverse proxy (only if DOMAIN_NAME is set)",
                        ],
                        code="sudo apt-get install -y python3 python3-venv python3-pip lsof curl nginx",
                        result="System packages installed",
                    ),

                    _step(2, "Create Python Virtual Environment",
                        "Creates an isolated Python environment so the app's packages don't conflict with the system Python.",
                        details=[
                            "Deletes any existing venv/ directory for a clean slate",
                            "Creates a fresh venv using python3 -m venv",
                            "Activates it for the remainder of the deploy",
                        ],
                        result="Fresh venv created at ./venv/",
                    ),

                    _step(3, "Install Python Packages",
                        "Installs all Python dependencies from requirements.txt into the virtual environment.",
                        details=[
                            "dash, dash-bootstrap-components — web UI framework",
                            "flask — HTTP server (Dash is built on Flask)",
                            "anthropic — Claude API client",
                            "python-dotenv — environment variable loading",
                            "PyMuPDF — PDF text extraction",
                            "~30 packages total including dependencies",
                        ],
                        code="pip install -r requirements.txt",
                        result="All Python packages installed",
                    ),

                    _step(4, "Write .env File",
                        "Creates the .env file with the Anthropic API key and port. This file is read by the app at startup.",
                        code="# Generated .env:\nANTHROPIC_API_KEY=sk-ant-api03-...\nAPP_PORT=5003",
                        result=".env file written",
                    ),

                    _step(5, "Create Data Directories",
                        "Creates the directories the app uses for its SQLite database, file uploads, and cache.",
                        code="mkdir -p data data/uploads cache",
                        details=[
                            "data/ — SQLite database (m8trx.db)",
                            "data/uploads/ — uploaded documents for AI analysis",
                            "cache/ — Dash background callback cache",
                        ],
                        result="Directories created",
                    ),

                    _step(6, "Initialize Database",
                        "Creates all 11 SQLite tables. The database starts clean — no user data is seeded during deployment.",
                        details=[
                            "Runs db.init_db() which creates: conversations, messages, tasks, meetings, meeting_action_items, emails, documents, clients, deals, settings, invoices, revenue_entries",
                            "No user data, branding, or email settings are pre-populated",
                            "The customer configures everything from the /setup page after first login",
                        ],
                        result="Database initialized with 11 tables (empty settings)",
                    ),

                    _step(7, "Configure systemd Service",
                        "Creates a systemd unit file so the app starts automatically on boot and restarts if it crashes.",
                        details=[
                            "Stops any existing service on the same port",
                            "Kills any rogue process occupying the port",
                            "Writes matrix-ai-{PORT}.service to /etc/systemd/system/",
                            "Enables the service (auto-start on boot)",
                        ],
                        code="# Generated systemd unit:\n[Service]\nType=simple\nUser=ubuntu\nWorkingDirectory=/home/ubuntu/matrix-ai\nExecStart=/home/ubuntu/matrix-ai/venv/bin/python3 app.py\nRestart=always\nRestartSec=5",
                        result="systemd service installed and enabled",
                    ),

                    _step(8, "Start the App Service",
                        "Starts the Flask/Dash app via systemd and verifies it's running.",
                        details=[
                            "Runs: systemctl start matrix-ai-5003",
                            "Waits 3 seconds for startup",
                            "Verifies the service is active — if not, prints error logs and exits",
                            "At this point the app is live on localhost:5003",
                        ],
                        result="App service running on port 5003",
                    ),

                    _step(9, "Pull Wildcard SSL Certificate from S3",
                        "Downloads the shared wildcard certificate (*.yourdomain.com) from a private S3 bucket. One cert covers all customer subdomains — no per-instance certbot, no rate limits.",
                        details=[
                            "Creates /etc/ssl/matrix-ai/ directory",
                            "Pulls fullchain.pem and privkey.pem from the S3 bucket specified in SSL_CERT_BUCKET",
                            "Sets secure permissions: privkey.pem is 600 (root-only), fullchain.pem is 644",
                            "If S3 pull fails, prints diagnostic info (bucket path, IAM permissions) and exits",
                        ],
                        code="aws s3 cp s3://matrix-ai-certs/wildcard/fullchain.pem /etc/ssl/matrix-ai/fullchain.pem\naws s3 cp s3://matrix-ai-certs/wildcard/privkey.pem /etc/ssl/matrix-ai/privkey.pem",
                        warning="The EC2 instance must have an IAM role with s3:GetObject permission on the cert bucket.",
                        result="Wildcard certificate installed to /etc/ssl/matrix-ai/",
                    ),

                    _step(10, "Configure Nginx Reverse Proxy (HTTPS)",
                        "Writes an Nginx config with full SSL termination that proxies to the app on localhost:5003.",
                        details=[
                            "Removes the default Nginx site",
                            "Writes /etc/nginx/sites-available/matrix-ai with two server blocks:",
                            "  — Port 80: 301 redirect all HTTP to HTTPS",
                            "  — Port 443: SSL termination with the wildcard cert, proxy_pass to localhost:5003",
                            "SSL settings: TLSv1.2/1.3 only, modern cipher suite, HSTS header",
                            "Security headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy",
                            "WebSocket upgrade headers (required for Dash callbacks)",
                            "120s proxy timeouts for long AI operations",
                        ],
                        warning="The app detects the Nginx config file and auto-binds to 127.0.0.1 instead of 0.0.0.0, so it's no longer directly accessible from the internet on port 5003.",
                        result="Nginx serving HTTPS with HTTP redirect",
                    ),

                    _step(11, "Daily Certificate Sync Cron",
                        "Installs a cron job that pulls the latest certificate from S3 every day at 3:00 AM and reloads Nginx. When you renew the wildcard cert centrally and push it to S3, all instances pick it up automatically.",
                        details=[
                            "Cron runs daily at 3:00 AM: pulls both cert files from S3, reloads Nginx",
                            "No manual intervention needed on any instance",
                            "Renewal workflow: renew the wildcard cert on your management machine, upload to S3, all instances sync within 24 hours",
                            "Prints the final deployment summary with the HTTPS URL",
                        ],
                        code="# Cron installed automatically:\n0 3 * * * aws s3 cp s3://..../fullchain.pem /etc/ssl/matrix-ai/ && \\\n          aws s3 cp s3://..../privkey.pem /etc/ssl/matrix-ai/ && \\\n          systemctl reload nginx",
                        result="Certificate auto-syncs daily from S3",
                    ),
                ], section_id="steps"),

                # ══════════════════════════════════════════════════
                # ARCHITECTURE
                # ══════════════════════════════════════════════════
                _section("Architecture Diagram", "bi-diagram-3-fill", COLORS["info"], [
                    _text("After deployment, traffic flows like this:"),
                    html.Pre(
                        """
    Internet                         EC2 Instance
    ────────                         ────────────────────────────────────────

    Browser ──[ HTTPS :443 ]──> Nginx (TLS termination)
                                  │
                                  │  proxy_pass (plain HTTP, localhost only)
                                  │
                                  └──> Flask/Dash app (127.0.0.1:5003)
                                         │
                                         ├── HTTP Basic Auth (checks DB hash)
                                         ├── SQLite database (data/m8trx.db)
                                         └── Anthropic API (Claude AI)


    S3 Bucket (wildcard cert) ──[ daily cron ]──> /etc/ssl/matrix-ai/

    Port 80   ──[ HTTP ]──> Nginx ──> 301 redirect to HTTPS
    Port 5003 ──[ blocked from internet — localhost only ]
    Port 443  ──[ HTTPS ]──> Nginx ──> App (the only public path)
""",
                        style={
                            "background": COLORS["code_bg"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "8px",
                            "padding": "20px",
                            "color": COLORS["text_secondary"],
                            "fontSize": "0.80rem",
                            "overflowX": "auto",
                            "lineHeight": "1.6",
                        },
                    ),
                    _text("Key points:"),
                    html.Ul([
                        html.Li("Nginx handles all encryption — the Python app never touches SSL", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("The app binds to 127.0.0.1 so it's unreachable from the internet directly", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("HTTP Basic Auth credentials are transmitted safely inside the HTTPS tunnel", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("The master login (matrix/morpheus) always works as a fallback. Customer-set credentials are stored with scrypt hashing in SQLite.", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                    ]),
                ], section_id="architecture"),

                # ══════════════════════════════════════════════════
                # AFTER DEPLOYMENT
                # ══════════════════════════════════════════════════
                _section("After Deployment", "bi-check2-all", COLORS["success"], [
                    html.H5("Useful commands on the server:", style={"color": COLORS["text_primary"], "marginBottom": "12px"}),
                    _code('''# Check app status
sudo systemctl status matrix-ai-5003

# View live logs
sudo journalctl -u matrix-ai-5003 -f

# Restart the app
sudo systemctl restart matrix-ai-5003

# Check Nginx status
sudo systemctl status nginx

# View installed SSL cert details
openssl x509 -in /etc/ssl/matrix-ai/fullchain.pem -noout -dates -subject

# Force cert sync from S3 now (usually not needed — cron runs daily)
sudo aws s3 cp s3://matrix-ai-certs/wildcard/fullchain.pem /etc/ssl/matrix-ai/fullchain.pem
sudo aws s3 cp s3://matrix-ai-certs/wildcard/privkey.pem /etc/ssl/matrix-ai/privkey.pem
sudo systemctl reload nginx

# Check Nginx error logs
sudo tail -50 /var/log/nginx/error.log'''),

                    html.H5("Default login credentials:", style={"color": COLORS["text_primary"], "marginTop": "20px", "marginBottom": "12px"}),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
                        children=[
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("Master Login", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "8px", "fontSize": "0.85rem"}),
                                html.Div("Username: matrix", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                html.Div("Password: morpheus", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                html.Div("(Always works, not shown in UI)", style={"color": COLORS["text_muted"], "fontSize": "0.78rem", "marginTop": "4px"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("Customer Login", style={"color": COLORS["success"], "fontWeight": "600", "marginBottom": "8px", "fontSize": "0.85rem"}),
                                html.Div("Set from the /setup page", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                html.Div("Stored with scrypt hash in DB", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                html.Div("(Changeable by the customer)", style={"color": COLORS["text_muted"], "fontSize": "0.78rem", "marginTop": "4px"}),
                            ]),
                        ],
                    ),

                    html.H5("First things the customer should do:", style={"color": COLORS["text_primary"], "marginTop": "20px", "marginBottom": "12px"}),
                    html.Ol([
                        html.Li("Log in with the default credentials (matrix / morpheus)", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Go to /setup and set their own username + password in the Dashboard Login section", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Set company name, their name, and role for AI personalization", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Configure IMAP email connection for email scanning", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                    ]),
                ], section_id="after"),

                # ══════════════════════════════════════════════════
                # MULTI-TENANT SCALING
                # ══════════════════════════════════════════════════
                _section("Multi-Tenant at Scale", "bi-buildings-fill", COLORS["warning"], [
                    _text("Each customer gets their own EC2 + subdomain. A single wildcard SSL certificate (*.yourdomain.com) is shared across all instances via S3 — no per-instance cert generation, no rate limits, unlimited deployments."),

                    html.H5("One-Time Setup (do this once)", style={"color": COLORS["text_primary"], "marginTop": "12px", "marginBottom": "8px"}),
                    _code('''# 1. Register a domain (~$12/year) and use Cloudflare (free) for DNS

# 2. Issue a wildcard cert via certbot + DNS-01 challenge
#    (run this from any machine — your laptop, a management server, etc.)
certbot certonly --dns-cloudflare \\
  --dns-cloudflare-credentials ~/.cloudflare.ini \\
  -d "*.matrixai.app" -d "matrixai.app"

# 3. Upload cert to a private S3 bucket
aws s3 cp /etc/letsencrypt/live/matrixai.app/fullchain.pem s3://matrix-ai-certs/wildcard/
aws s3 cp /etc/letsencrypt/live/matrixai.app/privkey.pem s3://matrix-ai-certs/wildcard/

# 4. Create an IAM role for EC2 instances with:
#    - s3:GetObject on arn:aws:s3:::matrix-ai-certs/*
#    - ec2:AllocateAddress, ec2:AssociateAddress, ec2:DescribeAddresses

# 5. Set up a cron on your management machine to renew + push to S3 every 60 days
#    certbot renew && aws s3 cp ... (all instances sync within 24h)'''),

                    html.H5("Per-Customer Deploy (10–15 min)", style={"color": COLORS["text_primary"], "marginTop": "16px", "marginBottom": "8px"}),
                    _code('''# 1. Launch EC2 (Ubuntu 22.04/24.04, t3.small, 20GB)
#    Attach the IAM role. Security group: ports 22, 80, 443

# 2. SSH in and run bootstrap (auto-allocates Elastic IP)
ssh ubuntu@<instance-ip>

curl -sL -H "Authorization: token $PAT" \\
  https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | \\
  GITHUB_PAT="$PAT" \\
  ANTHROPIC_API_KEY="sk-ant-..." \\
  DOMAIN_NAME="acme.matrixai.app" \\
  SSL_CERT_BUCKET="s3://matrix-ai-certs/wildcard" \\
  bash

# 3. Note the Elastic IP printed by bootstrap
# 4. Create DNS A record: acme.matrixai.app → <elastic-ip>
# 5. Verify: open https://acme.matrixai.app'''),

                    html.H5("Why this scales", style={"color": COLORS["text_primary"], "marginTop": "16px", "marginBottom": "8px"}),
                    html.Ul([
                        html.Li("No rate limits — one wildcard cert covers unlimited subdomains", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("No certbot on instances — cert pulled from S3, no port 80 challenge needed", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Auto-renewal — update S3 once, all instances sync via daily cron", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Elastic IP — static IP survives instance stop/start, DNS never goes stale", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                        html.Li("Total cert cost: $0 (Let's Encrypt) + ~$12/year for the domain", style={"color": COLORS["text_secondary"], "fontSize": "0.88rem", "marginBottom": "4px"}),
                    ]),
                ], section_id="scaling"),

                # ══════════════════════════════════════════════════
                # TROUBLESHOOTING
                # ══════════════════════════════════════════════════
                _section("Troubleshooting", "bi-wrench-adjustable", COLORS["danger"], [
                    html.Div(
                        style={"display": "grid", "gap": "12px"},
                        children=[
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("S3 cert pull fails: \"Access Denied\"", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "6px"}),
                                html.Div("The EC2 instance needs an IAM role with s3:GetObject on the cert bucket. Check:", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                _code("aws s3 ls s3://matrix-ai-certs/wildcard/\n# Should list fullchain.pem and privkey.pem"),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("Elastic IP fails: \"UnauthorizedOperation\"", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "6px"}),
                                html.Div("IAM role needs ec2:AllocateAddress, ec2:AssociateAddress, ec2:DescribeAddresses. Add these to the IAM policy attached to the instance role.", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("App shows 502 Bad Gateway", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "6px"}),
                                html.Div("Nginx is running but the app isn't. Restart it:", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                _code("sudo systemctl restart matrix-ai-5003\nsudo journalctl -u matrix-ai-5003 -n 30"),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("Browser says \"Not Secure\" or shows HTTP", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "6px"}),
                                html.Div("Cert may not have pulled correctly. Re-pull from S3:", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                _code("sudo aws s3 cp s3://matrix-ai-certs/wildcard/fullchain.pem /etc/ssl/matrix-ai/\nsudo aws s3 cp s3://matrix-ai-certs/wildcard/privkey.pem /etc/ssl/matrix-ai/\nsudo systemctl reload nginx"),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("Can't log in after password change", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "6px"}),
                                html.Div("HTTP Basic Auth caches credentials in the browser. Close all tabs and reopen, or use a private/incognito window. The master login (matrix/morpheus) always works.", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                            ]),
                            html.Div(style={"background": COLORS["code_bg"], "borderRadius": "8px", "padding": "16px"}, children=[
                                html.Div("Certificate expiry warning", style={"color": COLORS["danger"], "fontWeight": "600", "marginBottom": "6px"}),
                                html.Div("Renew the wildcard cert on your management machine, push to S3, then force-sync on the instance:", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                                _code("# On management machine:\ncertbot renew\naws s3 cp /etc/letsencrypt/live/matrixai.app/fullchain.pem s3://matrix-ai-certs/wildcard/\naws s3 cp /etc/letsencrypt/live/matrixai.app/privkey.pem s3://matrix-ai-certs/wildcard/\n\n# On the instance (or wait for 3am cron):\nsudo aws s3 cp s3://matrix-ai-certs/wildcard/fullchain.pem /etc/ssl/matrix-ai/\nsudo aws s3 cp s3://matrix-ai-certs/wildcard/privkey.pem /etc/ssl/matrix-ai/\nsudo systemctl reload nginx"),
                            ]),
                        ],
                    ),
                ], section_id="troubleshooting"),

                # ══════════════════════════════════════════════════
                # ROLLBACK
                # ══════════════════════════════════════════════════
                _section("Rollback", "bi-arrow-counterclockwise", COLORS["text_muted"], [
                    _text("To roll back the HTTPS changes and revert to the pre-HTTPS codebase:"),
                    _code('''# In the git repo:
git checkout d0bce23 -- app.py deploy.sh deploy.conf bootstrap.sh

# On a live server, also clean up Nginx:
sudo rm -f /etc/nginx/sites-enabled/matrix-ai /etc/nginx/sites-available/matrix-ai
sudo systemctl stop nginx
sudo systemctl restart matrix-ai-5003'''),
                    _text("This restores the original HTTP-only deployment with the password change feature intact."),
                ], section_id="rollback"),

                # ── Footer ──
                html.Div(
                    style={"textAlign": "center", "padding": "32px 0", "borderTop": f"1px solid {COLORS['border']}", "marginTop": "20px"},
                    children=[
                        html.P("Matrix AI Assistant — Deployment Guide", style={"color": COLORS["text_muted"], "fontSize": "0.82rem", "margin": 0}),
                    ],
                ),
            ],
        ),
    ],
)

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            a:hover { color: #6C5CE7 !important; border-left-color: #6C5CE7 !important; }
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: #0D0D1A; }
            ::-webkit-scrollbar-thumb { background: #2D3436; border-radius: 4px; }
            html { scroll-behavior: smooth; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
