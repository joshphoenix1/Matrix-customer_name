"""
Customer-specific configuration for the Matrix AI Assistant.
Change these values per deployment.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Customer Branding ──
COMPANY_NAME = "M8TRX.AI"
AGENT_NAME = "Matrix AI Assistant"
BRAND_COLOR = "#6C5CE7"

# ── Email Placeholder ──
EMAIL_ADDRESS = "assistant@m8trx.ai"

# ── LLM ──
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "m8trx.db")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
UPLOADS_DIR = os.path.join(BASE_DIR, "data", "uploads")

# ── Design System ──
COLORS = {
    "body_bg": "#0D0D1A",
    "sidebar_bg": "#161625",
    "card_bg": "#1E1E2E",
    "text_primary": "#FAFAFA",
    "text_secondary": "#B2BEC3",
    "text_muted": "#636E72",
    "accent": "#6C5CE7",
    "success": "#00B894",
    "warning": "#FDCB6E",
    "danger": "#D63031",
    "info": "#0984E3",
    "border": "#2D3436",
}
