#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# Matrix AI Assistant — Automated Deployment
# ══════════════════════════════════════════════════════════════
#
# Usage:
#   1. Edit deploy.conf with your credentials
#   2. ./deploy.sh
#
# Or pass values inline (overrides deploy.conf):
#   ANTHROPIC_API_KEY="sk-..." APP_PORT=5003 DOMAIN_NAME="acme.matrixai.app" ./deploy.sh
#
# ══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Load deploy.conf (env vars take precedence) ──
if [ -f deploy.conf ]; then
    set -a
    source deploy.conf
    set +a
fi

APP_PORT="${APP_PORT:-5003}"
APP_DIR="$SCRIPT_DIR"
APP_USER="${SUDO_USER:-$(whoami)}"
SERVICE_NAME="matrix-ai-${APP_PORT}"
DOMAIN_NAME="${DOMAIN_NAME:-}"
CERT_EMAIL="${CERT_EMAIL:-}"

# Determine total steps based on whether HTTPS is configured
if [ -n "$DOMAIN_NAME" ]; then
    TOTAL_STEPS=11
else
    TOTAL_STEPS=8
fi

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║       Matrix AI Assistant — Deployment           ║"
echo "  ║       Port: $APP_PORT                                ║"
if [ -n "$DOMAIN_NAME" ]; then
echo "  ║       HTTPS: $DOMAIN_NAME"
fi
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# ══════════════════════════════════════════════════════════════
# Step 1: System packages
# ══════════════════════════════════════════════════════════════
echo "[1/$TOTAL_STEPS] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip lsof curl > /dev/null 2>&1
if [ -n "$DOMAIN_NAME" ]; then
    sudo apt-get install -y -qq nginx certbot python3-certbot-nginx > /dev/null 2>&1
    echo "  OK — python3 $(python3 --version 2>&1 | awk '{print $2}'), nginx, certbot"
else
    echo "  OK — python3 $(python3 --version 2>&1 | awk '{print $2}')"
fi

# ══════════════════════════════════════════════════════════════
# Step 2: Python virtual environment
# ══════════════════════════════════════════════════════════════
echo "[2/$TOTAL_STEPS] Setting up virtual environment..."
if [ -d venv ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate
echo "  OK — fresh venv created"

# ══════════════════════════════════════════════════════════════
# Step 3: Python packages
# ══════════════════════════════════════════════════════════════
echo "[3/$TOTAL_STEPS] Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  OK — $(pip list --format=columns 2>/dev/null | wc -l) packages installed"

# ══════════════════════════════════════════════════════════════
# Step 4: .env file
# ══════════════════════════════════════════════════════════════
echo "[4/$TOTAL_STEPS] Writing .env..."
cat > .env <<ENVEOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your-api-key-here}
APP_PORT=${APP_PORT}
ENVEOF
echo "  OK"

# ══════════════════════════════════════════════════════════════
# Step 5: Data directories
# ══════════════════════════════════════════════════════════════
echo "[5/$TOTAL_STEPS] Creating data directories..."
mkdir -p data data/uploads cache
echo "  OK"

# ══════════════════════════════════════════════════════════════
# Step 6: Database + settings
# ══════════════════════════════════════════════════════════════
echo "[6/$TOTAL_STEPS] Initializing database..."
python3 -c "
import db
db.init_db()

# IMAP settings
imap_server   = '''${IMAP_SERVER:-}'''
imap_email    = '''${IMAP_EMAIL:-}'''
imap_password = '''${IMAP_PASSWORD:-}'''
if imap_email:
    db.save_setting('imap_server', imap_server or 'imap.gmail.com')
    db.save_setting('imap_email', imap_email)
    db.save_setting('imap_password', imap_password)
    print(f'  IMAP: {imap_email}')
else:
    print('  IMAP: skipped (configure in /setup)')

# Branding
company   = '''${COMPANY_NAME:-}'''
user_name = '''${USER_NAME:-}'''
user_role = '''${USER_ROLE:-}'''
industry  = '''${INDUSTRY:-}'''
if company:
    db.save_setting('company_name', company)
    print(f'  Company: {company}')
if user_name:
    db.save_setting('user_name', user_name)
if user_role:
    db.save_setting('user_role', user_role)
if industry:
    db.save_setting('industry', industry)
"
echo "  OK — database ready"

# ══════════════════════════════════════════════════════════════
# Step 7: systemd service (survives reboots)
# ══════════════════════════════════════════════════════════════
echo "[7/$TOTAL_STEPS] Configuring systemd service..."

# Stop existing service or nohup process
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
EXISTING_PID=$(lsof -ti :$APP_PORT 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
    kill $EXISTING_PID 2>/dev/null || true
    sleep 2
fi

VENV_PYTHON="$APP_DIR/venv/bin/python3"

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<SVCEOF
[Unit]
Description=Matrix AI Assistant (port ${APP_PORT})
After=network.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_PYTHON} app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
echo "  OK — ${SERVICE_NAME}.service installed"

# ══════════════════════════════════════════════════════════════
# Step 8: Start app service
# ══════════════════════════════════════════════════════════════
echo "[8/$TOTAL_STEPS] Starting service..."
sudo systemctl start "$SERVICE_NAME"
sleep 3

if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "  ERROR: Service failed to start."
    echo "  Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
    sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi
echo "  OK — ${SERVICE_NAME} running"

# ══════════════════════════════════════════════════════════════
# Steps 9-11: HTTPS via Nginx + Let's Encrypt (if domain set)
# ══════════════════════════════════════════════════════════════
if [ -n "$DOMAIN_NAME" ]; then

    # ── Step 9: Nginx reverse proxy config ──
    echo "[9/$TOTAL_STEPS] Configuring Nginx reverse proxy..."

    # Remove default site if it exists
    sudo rm -f /etc/nginx/sites-enabled/default

    sudo tee /etc/nginx/sites-available/matrix-ai > /dev/null <<NGXEOF
# Matrix AI Assistant — Nginx reverse proxy
# Certbot will modify this file to add SSL directives.

server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support (Dash callbacks)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long AI operations
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
NGXEOF

    sudo ln -sf /etc/nginx/sites-available/matrix-ai /etc/nginx/sites-enabled/matrix-ai

    # Validate config
    if ! sudo nginx -t 2>/dev/null; then
        echo "  ERROR: Nginx config is invalid."
        sudo nginx -t
        exit 1
    fi

    sudo systemctl enable nginx > /dev/null 2>&1
    sudo systemctl restart nginx
    echo "  OK — Nginx configured for ${DOMAIN_NAME}"

    # ── Step 10: SSL certificate via Let's Encrypt ──
    echo "[10/$TOTAL_STEPS] Obtaining SSL certificate..."

    CERTBOT_ARGS="--nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos"
    if [ -n "$CERT_EMAIL" ]; then
        CERTBOT_ARGS="$CERTBOT_ARGS -m ${CERT_EMAIL}"
    else
        CERTBOT_ARGS="$CERTBOT_ARGS --register-unsafely-without-email"
    fi

    # Redirect all HTTP to HTTPS
    CERTBOT_ARGS="$CERTBOT_ARGS --redirect"

    if sudo certbot $CERTBOT_ARGS; then
        echo "  OK — SSL certificate installed"
    else
        echo ""
        echo "  WARNING: Certbot failed. Common causes:"
        echo "    - DNS for ${DOMAIN_NAME} does not point to this server"
        echo "    - Port 80 is blocked by security group / firewall"
        echo "    - Rate limit reached (try again later)"
        echo ""
        echo "  The app is still accessible via HTTP."
        echo "  Fix the issue and run:  sudo certbot --nginx -d ${DOMAIN_NAME}"
        echo ""
    fi

    # ── Step 11: Verify HTTPS ──
    echo "[11/$TOTAL_STEPS] Verifying deployment..."

    # Ensure certbot auto-renewal timer is active
    sudo systemctl enable certbot.timer > /dev/null 2>&1 || true
    sudo systemctl start certbot.timer > /dev/null 2>&1 || true

    echo ""
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║          DEPLOYMENT SUCCESSFUL (HTTPS)           ║"
    echo "  ╠══════════════════════════════════════════════════╣"
    echo "  ║                                                  ║"
    echo "  ║  URL:  https://${DOMAIN_NAME}  "
    echo "  ║                                                  ║"
    echo "  ║  Service:  ${SERVICE_NAME}               "
    echo "  ║  Nginx:    sudo systemctl status nginx           ║"
    echo "  ║  SSL:      sudo certbot certificates             ║"
    echo "  ║  Renewal:  automatic (certbot.timer)             ║"
    echo "  ║  Logs:     sudo journalctl -u ${SERVICE_NAME} -f "
    echo "  ║  Restart:  sudo systemctl restart ${SERVICE_NAME}"
    echo "  ║                                                  ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo ""

else
    # ── No domain — HTTP-only deployment ──
    PUBLIC_IP=$(curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || hostname -I | awk '{print $1}')
    echo ""
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║          DEPLOYMENT SUCCESSFUL                   ║"
    echo "  ╠══════════════════════════════════════════════════╣"
    echo "  ║                                                  ║"
    echo "  ║  URL:  http://${PUBLIC_IP}:${APP_PORT}  "
    echo "  ║                                                  ║"
    echo "  ║  WARNING: No HTTPS — credentials sent in        ║"
    echo "  ║  cleartext. Set DOMAIN_NAME in deploy.conf      ║"
    echo "  ║  and re-run to enable HTTPS.                    ║"
    echo "  ║                                                  ║"
    echo "  ║  Service:  ${SERVICE_NAME}               "
    echo "  ║  Status:   sudo systemctl status ${SERVICE_NAME} "
    echo "  ║  Logs:     sudo journalctl -u ${SERVICE_NAME} -f "
    echo "  ║  Restart:  sudo systemctl restart ${SERVICE_NAME}"
    echo "  ║                                                  ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo ""
fi
