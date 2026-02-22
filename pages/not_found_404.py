"""
Custom 404 page.
"""

import dash
from dash import html
from config import COLORS

dash.register_page(__name__, path="/404", name="Not Found")

layout = html.Div(
    style={
        "textAlign": "center",
        "padding": "80px 20px",
    },
    children=[
        html.H1("404", style={"color": COLORS["accent"], "fontSize": "4rem", "fontWeight": "800", "margin": "0 0 16px 0"}),
        html.P("Page not found.", style={"color": COLORS["text_secondary"], "fontSize": "1.2rem", "marginBottom": "24px"}),
        html.A("Go to Dashboard", href="/", style={"color": COLORS["accent"], "fontSize": "1rem"}),
    ],
)
