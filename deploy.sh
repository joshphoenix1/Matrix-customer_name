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
#   ANTHROPIC_API_KEY="sk-..." DOMAIN_NAME="acme.matrixai.app" \
#   SSL_CERT_BUCKET="s3://matrix-ai-certs/wildcard" ./deploy.sh
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
SSL_CERT_BUCKET="${SSL_CERT_BUCKET:-}"
SSL_DIR="/etc/ssl/matrix-ai"

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
    sudo apt-get install -y -qq nginx > /dev/null 2>&1
    echo "  OK — python3 $(python3 --version 2>&1 | awk '{print $2}'), nginx"
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
"
echo "  OK — database ready (user configures company/branding via /setup)"

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
# Steps 9-11: HTTPS via Nginx + S3 wildcard cert (if domain set)
# ══════════════════════════════════════════════════════════════
if [ -n "$DOMAIN_NAME" ]; then

    # ── Step 9: Pull wildcard SSL cert from S3 ──
    echo "[9/$TOTAL_STEPS] Pulling SSL certificate from S3..."

    if [ -z "$SSL_CERT_BUCKET" ]; then
        echo ""
        echo "  ERROR: DOMAIN_NAME is set but SSL_CERT_BUCKET is empty."
        echo "  Set SSL_CERT_BUCKET in deploy.conf (e.g., s3://matrix-ai-certs/wildcard)"
        echo "  The bucket must contain: fullchain.pem and privkey.pem"
        echo ""
        echo "  The app is running on HTTP at port ${APP_PORT} without HTTPS."
        exit 1
    fi

    sudo mkdir -p "$SSL_DIR"

    if aws s3 cp "${SSL_CERT_BUCKET}/fullchain.pem" "${SSL_DIR}/fullchain.pem" --quiet 2>/dev/null && \
       aws s3 cp "${SSL_CERT_BUCKET}/privkey.pem" "${SSL_DIR}/privkey.pem" --quiet 2>/dev/null; then
        sudo chmod 600 "${SSL_DIR}/privkey.pem"
        sudo chmod 644 "${SSL_DIR}/fullchain.pem"
        echo "  OK — certificate installed to ${SSL_DIR}/"
    else
        echo ""
        echo "  ERROR: Could not pull cert from ${SSL_CERT_BUCKET}"
        echo "  Check:"
        echo "    - Bucket exists and contains fullchain.pem + privkey.pem"
        echo "    - IAM role has s3:GetObject permission on the bucket"
        echo ""
        echo "  The app is running on HTTP at port ${APP_PORT} without HTTPS."
        exit 1
    fi

    # ── Step 10: Nginx reverse proxy with SSL ──
    echo "[10/$TOTAL_STEPS] Configuring Nginx reverse proxy (HTTPS)..."

    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default

    sudo tee /etc/nginx/sites-available/matrix-ai > /dev/null <<NGXEOF
# Matrix AI Assistant — Nginx reverse proxy with SSL (wildcard cert)

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name ${DOMAIN_NAME};
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${DOMAIN_NAME};

    # Wildcard SSL certificate (pulled from S3)
    ssl_certificate     ${SSL_DIR}/fullchain.pem;
    ssl_certificate_key ${SSL_DIR}/privkey.pem;

    # Modern SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # HSTS (tell browsers to always use HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

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

    # Validate and start
    if ! sudo nginx -t 2>/dev/null; then
        echo "  ERROR: Nginx config is invalid."
        sudo nginx -t
        exit 1
    fi

    sudo systemctl enable nginx > /dev/null 2>&1
    sudo systemctl restart nginx
    echo "  OK — Nginx serving HTTPS for ${DOMAIN_NAME}"

    # ── Step 11: Daily cert sync cron + verify ──
    echo "[11/$TOTAL_STEPS] Setting up daily certificate sync..."

    # Cron job: pull latest cert from S3 daily at 3am and reload Nginx
    CRON_CMD="0 3 * * * aws s3 cp ${SSL_CERT_BUCKET}/fullchain.pem ${SSL_DIR}/fullchain.pem --quiet && aws s3 cp ${SSL_CERT_BUCKET}/privkey.pem ${SSL_DIR}/privkey.pem --quiet && chmod 600 ${SSL_DIR}/privkey.pem && systemctl reload nginx"

    # Install cron (idempotent — removes old entry first)
    (sudo crontab -l 2>/dev/null | grep -v "matrix-ai.*ssl" || true; echo "${CRON_CMD}  # matrix-ai ssl sync") | sudo crontab -
    echo "  OK — daily cert sync at 3:00 AM"

    echo ""
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║          DEPLOYMENT SUCCESSFUL (HTTPS)           ║"
    echo "  ╠══════════════════════════════════════════════════╣"
    echo "  ║                                                  ║"
    echo "  ║  URL:  https://${DOMAIN_NAME}  "
    echo "  ║                                                  ║"
    echo "  ║  Service:  ${SERVICE_NAME}               "
    echo "  ║  Nginx:    sudo systemctl status nginx           ║"
    echo "  ║  SSL cert: ${SSL_DIR}/  "
    echo "  ║  Renewal:  daily sync from S3 (3:00 AM cron)    ║"
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
