#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# Matrix AI Assistant — Bootstrap for Fresh EC2
# ══════════════════════════════════════════════════════════════
#
# ONE-LINER (private repo — pass GITHUB_PAT):
#
#   curl -sL -H "Authorization: token YOUR_PAT" \
#     https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | \
#     GITHUB_PAT="YOUR_PAT" bash
#
# FULLY AUTOMATED:
#
#   curl -sL -H "Authorization: token YOUR_PAT" \
#     https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | \
#     GITHUB_PAT="YOUR_PAT" \
#     ANTHROPIC_API_KEY="sk-ant-..." \
#     APP_PORT=5003 \
#     IMAP_EMAIL="you@gmail.com" \
#     IMAP_PASSWORD="xxxx xxxx xxxx xxxx" \
#     COMPANY_NAME="Acme Corp" \
#     bash
#
# ══════════════════════════════════════════════════════════════
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-$HOME/matrix-ai}"
GITHUB_PAT="${GITHUB_PAT:-}"
GITHUB_ORG="${GITHUB_ORG:-joshphoenix1}"
GITHUB_REPO="${GITHUB_REPO:-Matrix-customer_name}"

# Build repo URL (with PAT for private repos)
if [ -n "$GITHUB_PAT" ]; then
    REPO_URL="https://${GITHUB_PAT}@github.com/${GITHUB_ORG}/${GITHUB_REPO}.git"
else
    REPO_URL="https://github.com/${GITHUB_ORG}/${GITHUB_REPO}.git"
fi

echo ""
echo "  Matrix AI Assistant — Bootstrap"
echo "  ════════════════════════════════"
echo ""

# ── Install git if missing ──
if ! command -v git &>/dev/null; then
    echo "Installing git..."
    sudo apt-get update -qq && sudo apt-get install -y -qq git > /dev/null 2>&1
fi

# ── Clone or pull ──
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing install at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull --ff-only origin master 2>/dev/null || git pull origin master
else
    echo "Cloning template into $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ── Write deploy.conf from env vars if provided ──
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "Writing deploy.conf from environment..."
    cat > deploy.conf <<CONFEOF
# ══════════════════════════════════════════════════════════
# Matrix AI Assistant — Deployment Configuration
# ══════════════════════════════════════════════════════════

# ── App ──
APP_PORT=${APP_PORT:-5003}

# ── Anthropic API ──
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"

# ── IMAP Email ──
IMAP_SERVER="${IMAP_SERVER:-imap.gmail.com}"
IMAP_EMAIL="${IMAP_EMAIL:-}"
IMAP_PASSWORD="${IMAP_PASSWORD:-}"

# ── Customer Branding ──
COMPANY_NAME="${COMPANY_NAME:-}"
USER_NAME="${USER_NAME:-}"
USER_ROLE="${USER_ROLE:-}"
INDUSTRY="${INDUSTRY:-}"
CONFEOF
    echo "  deploy.conf written"
fi

# ── Run deploy ──
chmod +x deploy.sh

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "Running deployment..."
    ./deploy.sh
else
    echo ""
    echo "  ┌────────────────────────────────────────────────┐"
    echo "  │  Repo cloned to: $INSTALL_DIR"
    echo "  │                                                │"
    echo "  │  Next steps:                                   │"
    echo "  │    cd $INSTALL_DIR"
    echo "  │    nano deploy.conf    # add your credentials  │"
    echo "  │    ./deploy.sh         # deploy the app        │"
    echo "  └────────────────────────────────────────────────┘"
    echo ""
fi
