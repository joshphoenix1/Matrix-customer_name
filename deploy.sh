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
#   ANTHROPIC_API_KEY="sk-..." APP_PORT=5003 ./deploy.sh
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

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║       Matrix AI Assistant — Deployment           ║"
echo "  ║       Port: $APP_PORT                                ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# ══════════════════════════════════════════════════════════════
# Step 1: System packages
# ══════════════════════════════════════════════════════════════
echo "[1/8] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip lsof curl > /dev/null 2>&1
echo "  OK — python3 $(python3 --version 2>&1 | awk '{print $2}')"

# ══════════════════════════════════════════════════════════════
# Step 2: Python virtual environment
# ══════════════════════════════════════════════════════════════
echo "[2/8] Setting up virtual environment..."
if [ -d venv ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate
echo "  OK — fresh venv created"

# ══════════════════════════════════════════════════════════════
# Step 3: Python packages
# ══════════════════════════════════════════════════════════════
echo "[3/8] Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  OK — $(pip list --format=columns 2>/dev/null | wc -l) packages installed"

# ══════════════════════════════════════════════════════════════
# Step 4: .env file
# ══════════════════════════════════════════════════════════════
echo "[4/8] Writing .env..."
cat > .env <<ENVEOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your-api-key-here}
APP_PORT=${APP_PORT}
ENVEOF
echo "  OK"

# ══════════════════════════════════════════════════════════════
# Step 5: Data directories
# ══════════════════════════════════════════════════════════════
echo "[5/8] Creating data directories..."
mkdir -p data data/uploads cache
echo "  OK"

# ══════════════════════════════════════════════════════════════
# Step 6: Database + settings
# ══════════════════════════════════════════════════════════════
echo "[6/8] Initializing database..."
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
echo "[7/8] Configuring systemd service..."

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
# Step 8: Start
# ══════════════════════════════════════════════════════════════
echo "[8/8] Starting service..."
sudo systemctl start "$SERVICE_NAME"
sleep 3

# Verify
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    PUBLIC_IP=$(curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || hostname -I | awk '{print $1}')
    echo ""
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║          DEPLOYMENT SUCCESSFUL                   ║"
    echo "  ╠══════════════════════════════════════════════════╣"
    echo "  ║                                                  ║"
    echo "  ║  URL:  http://${PUBLIC_IP}:${APP_PORT}  "
    echo "  ║                                                  ║"
    echo "  ║  Service:  ${SERVICE_NAME}               "
    echo "  ║  Status:   sudo systemctl status ${SERVICE_NAME} "
    echo "  ║  Logs:     sudo journalctl -u ${SERVICE_NAME} -f "
    echo "  ║  Restart:  sudo systemctl restart ${SERVICE_NAME}"
    echo "  ║                                                  ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo ""
else
    echo ""
    echo "  ERROR: Service failed to start."
    echo "  Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
    sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi
