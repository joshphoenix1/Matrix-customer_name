"""
Reusable KPI / metric card component.
"""

from dash import html
from config import COLORS


def kpi_card(title, value, subtitle="", color=None):
    accent = color or COLORS["accent"]
    return html.Div(
        style={
            "background": COLORS["card_bg"],
            "borderRadius": "12px",
            "padding": "24px",
            "borderLeft": f"4px solid {accent}",
            "flex": "1",
            "minWidth": "180px",
        },
        children=[
            html.P(
                title,
                style={
                    "color": COLORS["text_muted"],
                    "fontSize": "0.8rem",
                    "margin": "0 0 8px 0",
                    "textTransform": "uppercase",
                    "letterSpacing": "1px",
                },
            ),
            html.H2(
                str(value),
                style={
                    "color": accent,
                    "fontSize": "2rem",
                    "fontWeight": "800",
                    "margin": "0 0 4px 0",
                },
            ),
            html.P(
                subtitle,
                style={
                    "color": COLORS["text_secondary"],
                    "fontSize": "0.85rem",
                    "margin": 0,
                },
            ) if subtitle else None,
        ],
    )
