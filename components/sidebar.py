"""
Reusable navigation sidebar — reads from dash.page_registry.
"""

import dash
from dash import html, dcc
from config import COMPANY_NAME, COLORS
import db

PAGE_ICONS = {
    "Dashboard": "bi bi-grid-1x2-fill",
    "Chat": "bi bi-chat-dots-fill",
    "Tasks": "bi bi-check2-square",
    "Meetings": "bi bi-calendar-event-fill",
    "Documents": "bi bi-file-earmark-text-fill",
    "Emails": "bi bi-envelope-open-fill",
    "Deploy": "bi bi-rocket-takeoff-fill",
    "Setup": "bi bi-gear-fill",
}


def create_sidebar():
    nav_links = []
    for page in dash.page_registry.values():
        if page.get("name") == "Not Found":
            continue
        icon_cls = PAGE_ICONS.get(page["name"], "bi bi-circle")
        nav_links.append(
            dcc.Link(
                html.Div(
                    [
                        html.I(className=icon_cls, style={"marginRight": "10px", "fontSize": "1rem"}),
                        html.Span(page["name"]),
                    ],
                    className="sidebar-nav-link",
                ),
                href=page["relative_path"],
                style={"textDecoration": "none"},
            )
        )

    # Get configured email for footer display
    imap_email = db.get_setting("imap_email", "")
    footer_text = imap_email if imap_email else "Not configured"

    return html.Div(
        id="sidebar",
        style={
            "width": "260px",
            "minWidth": "260px",
            "background": COLORS["sidebar_bg"],
            "height": "100vh",
            "position": "fixed",
            "top": 0,
            "left": 0,
            "padding": "24px 16px",
            "overflowY": "auto",
            "borderRight": f"1px solid {COLORS['border']}",
            "zIndex": 100,
            "display": "flex",
            "flexDirection": "column",
        },
        children=[
            # Brand
            html.Div(
                style={"marginBottom": "32px", "textAlign": "center"},
                children=[
                    html.H1(
                        COMPANY_NAME,
                        style={
                            "color": COLORS["text_primary"],
                            "fontSize": "1.4rem",
                            "margin": 0,
                            "letterSpacing": "3px",
                            "fontWeight": "800",
                        },
                    ),
                    html.P(
                        "Matrix AI Assistant",
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "0.8rem",
                            "margin": "4px 0 0 0",
                            "letterSpacing": "2px",
                        },
                    ),
                ],
            ),
            # Navigation
            html.Div(nav_links, style={"flex": "1"}),
            # Footer — email
            html.Div(
                style={
                    "borderTop": f"1px solid {COLORS['border']}",
                    "paddingTop": "16px",
                    "marginTop": "16px",
                },
                children=[
                    html.P(
                        "Connected Inbox:",
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "0.7rem",
                            "margin": "0 0 4px 0",
                            "textTransform": "uppercase",
                            "letterSpacing": "1px",
                        },
                    ),
                    html.P(
                        footer_text,
                        style={
                            "color": COLORS["accent"],
                            "fontSize": "0.8rem",
                            "margin": 0,
                            "wordBreak": "break-all",
                        },
                    ),
                ],
            ),
        ],
    )
