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
# FULLY AUTOMATED (with HTTPS + Elastic IP):
#
#   curl -sL -H "Authorization: token YOUR_PAT" \
#     https://raw.githubusercontent.com/joshphoenix1/Matrix-customer_name/master/bootstrap.sh | \
#     GITHUB_PAT="YOUR_PAT" \
#     ANTHROPIC_API_KEY="sk-ant-..." \
#     APP_PORT=5003 \
#     DOMAIN_NAME="acme.matrixai.app" \
#     CERT_EMAIL="admin@matrixai.app" \
#     IMAP_EMAIL="you@gmail.com" \
#     IMAP_PASSWORD="xxxx xxxx xxxx xxxx" \
#     COMPANY_NAME="Acme Corp" \
#     bash
#
# NOTE: Elastic IP allocation requires an IAM role on the EC2 with:
#   ec2:AllocateAddress, ec2:AssociateAddress, ec2:DescribeAddresses
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

# ── Install git + AWS CLI if missing ──
if ! command -v git &>/dev/null || ! command -v aws &>/dev/null; then
    echo "Installing system tools..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq git unzip curl > /dev/null 2>&1
    if ! command -v aws &>/dev/null; then
        curl -sL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
        cd /tmp && unzip -qo awscliv2.zip && sudo ./aws/install > /dev/null 2>&1
        cd - > /dev/null
    fi
fi

# ── Allocate Elastic IP (static public IP) ──
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" 2>/dev/null)
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null)
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null)

if [ -n "$INSTANCE_ID" ] && command -v aws &>/dev/null; then
    # Check if an EIP is already associated
    EXISTING_EIP=$(aws ec2 describe-addresses --region "$REGION" \
        --filters "Name=instance-id,Values=$INSTANCE_ID" \
        --query 'Addresses[0].PublicIp' --output text 2>/dev/null || echo "None")

    if [ "$EXISTING_EIP" = "None" ] || [ -z "$EXISTING_EIP" ]; then
        echo "Allocating Elastic IP..."
        ALLOC_ID=$(aws ec2 allocate-address --region "$REGION" --query 'AllocationId' --output text 2>/dev/null)
        if [ -n "$ALLOC_ID" ] && [ "$ALLOC_ID" != "None" ]; then
            aws ec2 associate-address --region "$REGION" --instance-id "$INSTANCE_ID" --allocation-id "$ALLOC_ID" > /dev/null 2>&1
            NEW_EIP=$(aws ec2 describe-addresses --region "$REGION" --allocation-ids "$ALLOC_ID" \
                --query 'Addresses[0].PublicIp' --output text 2>/dev/null)
            echo "  Elastic IP: $NEW_EIP (static — survives stop/start)"
            echo ""
            echo "  *** Point your DNS A record to: $NEW_EIP ***"
            echo ""
        else
            echo "  WARNING: Could not allocate Elastic IP (check IAM permissions)"
            echo "  Required: ec2:AllocateAddress, ec2:AssociateAddress, ec2:DescribeAddresses"
        fi
    else
        echo "  Elastic IP already attached: $EXISTING_EIP"
    fi
else
    echo "  Skipping Elastic IP (not running on EC2 or AWS CLI unavailable)"
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

# ── HTTPS ──
DOMAIN_NAME="${DOMAIN_NAME:-}"
CERT_EMAIL="${CERT_EMAIL:-}"

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
