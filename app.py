"""
Matrix AI Assistant — Multi-page Dash application entry point.
"""

import os
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from config import COLORS, COMPANY_NAME, CACHE_DIR

# ── Diskcache for background callbacks ──
os.makedirs(CACHE_DIR, exist_ok=True)

# ── App init ──
app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title=f"{COMPANY_NAME} | Matrix AI Assistant",
    update_title=None,
    external_stylesheets=[
        dbc.themes.DARKLY,
        dbc.icons.BOOTSTRAP,
    ],
)

# ── Initialize database on import ──
import db
db.init_db()

# ── Import sidebar (must be after page registration) ──
from components.sidebar import create_sidebar

# ── Layout ──
app.layout = html.Div(
    style={
        "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "margin": 0,
        "padding": 0,
        "background": COLORS["body_bg"],
        "minHeight": "100vh",
    },
    children=[
        dcc.Location(id="url", refresh=False),
        create_sidebar(),
        html.Div(
            id="page-content",
            style={
                "marginLeft": "260px",
                "padding": "40px 48px",
                "background": COLORS["body_bg"],
                "minHeight": "100vh",
            },
            children=[
                html.Div(
                    style={"maxWidth": "1200px", "margin": "0 auto"},
                    children=[dash.page_container],
                ),
            ],
        ),
    ],
)

# ── Custom index string for fonts and meta ──
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
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

# ── Run ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
