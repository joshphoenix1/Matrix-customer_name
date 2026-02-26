"""
Persona page — persona clone management, profile display, ingestion controls,
chat export ingestion. Auto-reply settings are on the Rules page.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from config import COLORS
import db
from components.kpi_card import kpi_card

dash.register_page(__name__, path="/persona", name="Persona", order=12)


def layout():
    # Load current state
    sample_count = db.get_persona_sample_count()
    pending_drafts = db.get_pending_drafts_count()
    profile_json = db.get_setting("persona_profile")
    profile = json.loads(profile_json) if profile_json else None

    try:
        from services.vector_store import get_count
        vector_count = get_count()
    except Exception:
        vector_count = 0

    profile_status = "Active" if profile else "Not Built"

    # Per-source breakdown
    source_counts = db.get_persona_sample_count_by_source()

    return html.Div(
        children=[
            # Header
            html.Div(
                style={"marginBottom": "24px"},
                children=[
                    html.H2(
                        [html.I(className="bi bi-person-bounding-box", style={"marginRight": "12px"}), "Persona Clone"],
                        style={"color": COLORS["text_primary"], "margin": 0},
                    ),
                    html.P(
                        "Train your AI to write emails in your voice. Ingest your communications, build a style profile, then auto-draft replies.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                    ),
                    html.P(
                        "Built with ChromaDB vector embeddings, Sentence Transformers (all-MiniLM-L6-v2), "
                        "and Claude for RAG-powered style fingerprinting and reply generation.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "margin": "4px 0 0 0", "fontStyle": "italic"},
                    ),
                ],
            ),

            # KPI row
            html.Div(
                id="persona-kpi-row",
                style={"display": "flex", "gap": "16px", "marginBottom": "12px", "flexWrap": "wrap"},
                children=[
                    kpi_card("Training Samples", sample_count, "text chunks", COLORS["accent"]),
                    kpi_card("Vector Store", vector_count, "embeddings", COLORS["info"]),
                    kpi_card("Pending Drafts", pending_drafts, "to review", COLORS["warning"]),
                    kpi_card("Profile Status", profile_status, "", COLORS["success"] if profile else COLORS["text_muted"]),
                ],
            ),

            # Per-channel sample breakdown
            html.Div(
                style={"marginBottom": "24px", "display": "flex", "gap": "8px", "flexWrap": "wrap"},
                children=[
                    html.Span(
                        f"{src.replace('_', ' ').title()}: {cnt}",
                        style={
                            "background": COLORS["card_bg"],
                            "color": COLORS["text_secondary"],
                            "padding": "4px 12px",
                            "borderRadius": "6px",
                            "fontSize": "0.8rem",
                            "border": f"1px solid {COLORS['border']}",
                        },
                    )
                    for src, cnt in sorted(source_counts.items())
                ] if source_counts else [
                    html.Span(
                        "No samples yet",
                        style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                    )
                ],
            ),

            # Main grid
            dbc.Row(
                [
                    # Left column: Profile + Ingestion
                    dbc.Col(
                        [
                            # Persona Profile card
                            html.Div(
                                style={
                                    "background": COLORS["card_bg"],
                                    "borderRadius": "12px",
                                    "padding": "24px",
                                    "marginBottom": "20px",
                                    "borderLeft": f"4px solid {COLORS['accent']}",
                                },
                                children=[
                                    html.Div(
                                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"},
                                        children=[
                                            html.H4("Writing Style Profile", style={"color": COLORS["text_primary"], "margin": 0}),
                                            dbc.Button(
                                                [html.I(className="bi bi-arrow-clockwise", style={"marginRight": "6px"}), "Rebuild Profile"],
                                                id="btn-rebuild-profile",
                                                size="sm",
                                                color="primary",
                                                style={"background": COLORS["accent"], "border": "none"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot",
                                        color=COLORS["accent"],
                                        children=[html.Div(id="persona-profile-display")],
                                    ),
                                ],
                            ),

                            # Chat Export ingestion
                            html.Div(
                                style={
                                    "background": COLORS["card_bg"],
                                    "borderRadius": "12px",
                                    "padding": "24px",
                                    "marginBottom": "20px",
                                    "borderLeft": f"4px solid {COLORS['info']}",
                                },
                                children=[
                                    html.H4("Ingest Chat / Text Export", style={"color": COLORS["text_primary"], "marginBottom": "8px"}),
                                    html.P(
                                        "Paste exported chat messages or other text samples to add to your persona training data.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "12px"},
                                    ),
                                    dbc.Textarea(
                                        id="persona-chat-export",
                                        placeholder="Paste your chat export or text samples here...",
                                        style={
                                            "background": COLORS["body_bg"],
                                            "border": f"1px solid {COLORS['border']}",
                                            "color": COLORS["text_primary"],
                                            "borderRadius": "8px",
                                            "minHeight": "120px",
                                            "marginBottom": "12px",
                                        },
                                    ),
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "12px"},
                                        children=[
                                            dbc.Button(
                                                [html.I(className="bi bi-chat-text", style={"marginRight": "6px"}), "Ingest Text"],
                                                id="btn-ingest-chat",
                                                size="sm",
                                                color="info",
                                                outline=True,
                                            ),
                                            html.Div(id="persona-chat-status"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                        md=7,
                    ),

                    # Right column: Actions
                    dbc.Col(
                        [
                            # Ingestion Actions
                            html.Div(
                                style={
                                    "background": COLORS["card_bg"],
                                    "borderRadius": "12px",
                                    "padding": "24px",
                                    "marginBottom": "20px",
                                    "borderLeft": f"4px solid {COLORS['success']}",
                                },
                                children=[
                                    html.H4("Training Actions", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "10px"},
                                        children=[
                                            dbc.Button(
                                                [html.I(className="bi bi-envelope-arrow-down", style={"marginRight": "8px"}), "Ingest Emails"],
                                                id="btn-ingest-emails",
                                                color="success",
                                                outline=True,
                                                style={"width": "100%"},
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-file-earmark-arrow-down", style={"marginRight": "8px"}), "Ingest Documents"],
                                                id="btn-ingest-docs",
                                                color="success",
                                                outline=True,
                                                style={"width": "100%"},
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-database-fill-gear", style={"marginRight": "8px"}), "Embed Samples"],
                                                id="btn-embed-samples",
                                                color="primary",
                                                outline=True,
                                                style={"width": "100%"},
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-pencil-square", style={"marginRight": "8px"}), "Generate Drafts"],
                                                id="btn-generate-drafts",
                                                color="warning",
                                                outline=True,
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="dot",
                                        color=COLORS["success"],
                                        children=[html.Div(id="persona-action-status", style={"marginTop": "12px"})],
                                    ),
                                ],
                            ),
                        ],
                        md=5,
                    ),
                ],
            ),
        ]
    )


# ── Callbacks ──

@callback(
    Output("persona-profile-display", "children"),
    Input("btn-rebuild-profile", "n_clicks"),
    Input("persona-kpi-row", "children"),
    prevent_initial_call=False,
)
def display_or_rebuild_profile(rebuild_clicks, _):
    triggered = dash.ctx.triggered_id

    if triggered == "btn-rebuild-profile" and rebuild_clicks:
        from services.persona_engine import rebuild_persona
        result = rebuild_persona()
        if result.get("profile", {}).get("error"):
            return html.P(
                f"Error: {result['profile']['error']}",
                style={"color": COLORS["danger"], "fontSize": "0.9rem"},
            )

    # Display current profile
    profile_json = db.get_setting("persona_profile")
    if not profile_json:
        return html.P(
            "No persona profile yet. Click 'Rebuild Profile' or ingest emails first.",
            style={"color": COLORS["text_muted"], "fontSize": "0.9rem"},
        )

    try:
        profile = json.loads(profile_json)
    except Exception:
        return html.P("Invalid profile data.", style={"color": COLORS["danger"], "fontSize": "0.9rem"})

    items = []
    field_labels = {
        "tone": ("Tone", "bi bi-chat-heart"),
        "formality_level": ("Formality Level", "bi bi-sliders"),
        "response_length_tendency": ("Response Length", "bi bi-text-left"),
        "sentence_structure": ("Sentence Style", "bi bi-list-columns"),
    }
    for key, (label, icon) in field_labels.items():
        val = profile.get(key, "—")
        items.append(
            html.Div(
                style={"marginBottom": "10px"},
                children=[
                    html.Span(
                        [html.I(className=icon, style={"marginRight": "6px"}), label + ": "],
                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "fontWeight": "600"},
                    ),
                    html.Span(str(val), style={"color": COLORS["text_primary"], "fontSize": "0.85rem"}),
                ],
            )
        )

    list_fields = {
        "greeting_patterns": "Greetings",
        "sign_off_patterns": "Sign-offs",
        "common_phrases": "Common Phrases",
        "vocabulary_patterns": "Vocabulary",
        "email_categories": "Email Categories",
        "avoids": "Avoids",
    }
    for key, label in list_fields.items():
        vals = profile.get(key, [])
        if isinstance(vals, list) and vals:
            badges = [
                html.Span(
                    v,
                    style={
                        "background": COLORS["body_bg"],
                        "color": COLORS["text_secondary"],
                        "padding": "2px 8px",
                        "borderRadius": "4px",
                        "fontSize": "0.8rem",
                        "marginRight": "4px",
                        "marginBottom": "4px",
                        "display": "inline-block",
                    },
                )
                for v in vals[:8]
            ]
            items.append(
                html.Div(
                    style={"marginBottom": "10px"},
                    children=[
                        html.P(label, style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "margin": "0 0 4px 0", "fontWeight": "600"}),
                        html.Div(badges),
                    ],
                )
            )

    return html.Div(items)


@callback(
    Output("persona-action-status", "children"),
    Input("btn-ingest-emails", "n_clicks"),
    Input("btn-ingest-docs", "n_clicks"),
    Input("btn-embed-samples", "n_clicks"),
    Input("btn-generate-drafts", "n_clicks"),
    prevent_initial_call=True,
)
def handle_persona_actions(ingest_emails_clicks, ingest_docs_clicks, embed_clicks, drafts_clicks):
    triggered = dash.ctx.triggered_id
    from services import persona_engine

    if triggered == "btn-ingest-emails" and ingest_emails_clicks:
        result = persona_engine.ingest_emails()
        if result.get("error"):
            return _status_badge(result["error"], "danger")
        return _status_badge(f"Ingested {result['ingested']} email chunks.", "success")

    if triggered == "btn-ingest-docs" and ingest_docs_clicks:
        result = persona_engine.ingest_documents()
        return _status_badge(f"Ingested {result['ingested']} document chunks.", "success")

    if triggered == "btn-embed-samples" and embed_clicks:
        result = persona_engine.embed_pending_samples()
        return _status_badge(f"Embedded {result['embedded']} samples into vector store.", "success")

    if triggered == "btn-generate-drafts" and drafts_clicks:
        result = persona_engine.process_new_emails_for_drafts()
        if result.get("error"):
            return _status_badge(result["error"], "warning")
        return _status_badge(f"Generated {result['processed']} new drafts.", "success")

    return no_update


@callback(
    Output("persona-chat-status", "children"),
    Input("btn-ingest-chat", "n_clicks"),
    State("persona-chat-export", "value"),
    prevent_initial_call=True,
)
def ingest_chat_export(n_clicks, text):
    if not n_clicks or not text:
        return no_update
    from services.persona_engine import ingest_chat_export as do_ingest
    result = do_ingest(text)
    return _status_badge(f"Ingested {result['ingested']} text chunks.", "success")


def _status_badge(text, color_key):
    return html.Span(
        text,
        style={"color": COLORS.get(color_key, COLORS["text_secondary"]), "fontSize": "0.85rem"},
    )
