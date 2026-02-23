#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# Matrix AI Assistant — One-Touch Deployment
# Run: chmod +x deploy.sh && ./deploy.sh
# ══════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Load deploy.conf ──
if [ ! -f deploy.conf ]; then
    echo "ERROR: deploy.conf not found. Copy deploy.conf.example and fill in your values."
    exit 1
fi
source deploy.conf

APP_PORT="${APP_PORT:-5003}"

echo "═══════════════════════════════════════════════"
echo "  Matrix AI Assistant — Deploying on port $APP_PORT"
echo "═══════════════════════════════════════════════"

# ── 1. System dependencies ──
echo ""
echo "[1/7] Checking system dependencies..."
if ! command -v python3 &>/dev/null; then
    echo "  Installing python3..."
    sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-venv python3-pip
else
    echo "  python3 found: $(python3 --version)"
fi

# ── 2. Virtual environment ──
echo ""
echo "[2/7] Setting up virtual environment..."
if [ ! -d venv ]; then
    python3 -m venv venv
    echo "  Created fresh venv"
else
    echo "  venv already exists"
fi
source venv/bin/activate

# ── 3. Install dependencies ──
echo ""
echo "[3/7] Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# ── 4. Write .env ──
echo ""
echo "[4/7] Writing .env..."
cat > .env <<ENVEOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
APP_PORT=${APP_PORT}
ENVEOF
echo "  .env written"

# ── 5. Create data directories ──
echo ""
echo "[5/7] Initializing directories..."
mkdir -p data data/uploads cache

# ── 6. Initialize DB and save settings ──
echo ""
echo "[6/7] Initializing database and settings..."
python3 -c "
import db
db.init_db()
print('  Database initialized')

# Save IMAP settings if provided
imap_server = '''${IMAP_SERVER:-}'''
imap_email  = '''${IMAP_EMAIL:-}'''
imap_password = '''${IMAP_PASSWORD:-}'''

if imap_email:
    db.save_setting('imap_server', imap_server or 'imap.gmail.com')
    db.save_setting('imap_email', imap_email)
    db.save_setting('imap_password', imap_password)
    print(f'  IMAP configured: {imap_email}')
else:
    print('  IMAP not configured — set up later in /setup')

# Save branding if provided
company = '''${COMPANY_NAME:-}'''
user_name = '''${USER_NAME:-}'''
user_role = '''${USER_ROLE:-}'''

if company:
    db.save_setting('company_name', company)
    print(f'  Company: {company}')
if user_name:
    db.save_setting('user_name', user_name)
if user_role:
    db.save_setting('user_role', user_role)
"

# ── 7. Kill any existing instance and start ──
echo ""
echo "[7/7] Starting Matrix AI Assistant..."

# Kill existing process on this port if any
EXISTING_PID=$(lsof -ti :$APP_PORT 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
    echo "  Stopping existing process on port $APP_PORT (PID $EXISTING_PID)..."
    kill $EXISTING_PID 2>/dev/null || true
    sleep 2
fi

# Start in background
nohup python3 app.py > matrix.log 2>&1 &
NEW_PID=$!
sleep 3

# Verify it's running
if kill -0 $NEW_PID 2>/dev/null; then
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  DEPLOYED SUCCESSFULLY"
    echo "  URL: http://$(hostname -I | awk '{print $1}'):$APP_PORT"
    echo "  PID: $NEW_PID"
    echo "  Log: $SCRIPT_DIR/matrix.log"
    echo "═══════════════════════════════════════════════"
else
    echo ""
    echo "ERROR: App failed to start. Check matrix.log:"
    tail -20 matrix.log
    exit 1
fi
