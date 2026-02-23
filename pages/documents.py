"""
Documents page — file upload, AI analysis, document management.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import base64
import os
import json
from datetime import datetime
from config import COLORS, UPLOADS_DIR
import db
from services.claude_client import analyze_document, search_documents

dash.register_page(__name__, path="/documents", name="Documents", order=5)

ALLOWED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".pdf"}

os.makedirs(UPLOADS_DIR, exist_ok=True)


def _file_ext(filename):
    return os.path.splitext(filename)[1].lower() if filename else ""


def _format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


# ── Layout ──

layout = html.Div(
    children=[
        dcc.Store(id="doc-selected-id"),
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div(
                    children=[
                        html.H2("Documents", style={"color": COLORS["text_primary"], "margin": 0}),
                        html.P(
                            "Upload documents for AI-powered analysis and insights.",
                            style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                        ),
                    ]
                ),
            ],
        ),
        # Upload area
        html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "24px",
                "marginBottom": "24px",
                "borderLeft": f"4px solid {COLORS['accent']}",
            },
            children=[
                html.H4("Upload Document", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
                dcc.Upload(
                    id="doc-upload",
                    children=html.Div(
                        [
                            html.I(className="bi bi-cloud-arrow-up", style={"fontSize": "2rem", "color": COLORS["accent"], "marginBottom": "8px"}),
                            html.P("Drag & drop a file here, or click to select", style={"color": COLORS["text_secondary"], "margin": "0 0 4px 0"}),
                            html.P(
                                "Supports: .txt, .md, .csv, .json, .pdf",
                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "margin": 0},
                            ),
                        ],
                        style={"textAlign": "center"},
                    ),
                    style={
                        "border": f"2px dashed {COLORS['border']}",
                        "borderRadius": "8px",
                        "padding": "32px",
                        "cursor": "pointer",
                        "background": COLORS["body_bg"],
                    },
                    multiple=False,
                ),
                html.Div(id="doc-upload-status", style={"marginTop": "16px"}),
            ],
        ),
        # AI Document Search
        html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "24px",
                "marginBottom": "24px",
                "borderLeft": f"4px solid {COLORS['info']}",
            },
            children=[
                html.H4(
                    [html.I(className="bi bi-search", style={"marginRight": "10px"}), "AI Document Search"],
                    style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                ),
                html.P(
                    "Search across all uploaded documents using AI. Ask questions about your data.",
                    style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"},
                ),
                html.Div(
                    style={"display": "flex", "gap": "8px"},
                    children=[
                        dbc.Input(
                            id="doc-search-input",
                            placeholder="e.g. What revenue figures are mentioned? / Find all client names / Summarize key terms...",
                            style={
                                "background": COLORS["body_bg"],
                                "border": f"1px solid {COLORS['border']}",
                                "color": COLORS["text_primary"],
                                "borderRadius": "8px",
                                "flex": "1",
                            },
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-stars", style={"marginRight": "6px"}), "Search"],
                            id="doc-search-btn",
                            color="primary",
                            style={"background": COLORS["info"], "border": "none"},
                        ),
                    ],
                ),
                dcc.Loading(
                    id="doc-search-loading",
                    type="dot",
                    color=COLORS["info"],
                    children=[html.Div(id="doc-search-results", style={"marginTop": "16px"})],
                ),
            ],
        ),
        # Document list
        html.Div(id="doc-list"),
        # Document detail / analysis view
        html.Div(id="doc-detail"),
    ]
)


# ── Callbacks ──

@callback(
    Output("doc-upload-status", "children"),
    Output("doc-list", "children", allow_duplicate=True),
    Input("doc-upload", "contents"),
    State("doc-upload", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
    if not contents or not filename:
        return no_update, no_update

    ext = _file_ext(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return html.P(
            f"Unsupported file type: {ext}. Please upload .txt, .md, .csv, .json, or .pdf files.",
            style={"color": COLORS["danger"], "fontSize": "0.9rem"},
        ), no_update

    # Decode base64 content
    try:
        content_type, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
    except Exception:
        return html.P(
            "Error decoding file. Please try again.",
            style={"color": COLORS["danger"], "fontSize": "0.9rem"},
        ), no_update

    # Save file to disk
    safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    filepath = os.path.join(UPLOADS_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(decoded)

    file_size = len(decoded)

    # Save to database
    doc_id = db.save_document(
        filename=filename,
        filepath=filepath,
        file_type=ext,
        file_size=file_size,
    )

    # Read text content for analysis
    text_content = ""
    if ext in (".txt", ".md", ".csv", ".json"):
        try:
            text_content = decoded.decode("utf-8", errors="replace")
        except Exception:
            text_content = "[Could not decode file content]"
    elif ext == ".pdf":
        text_content = f"[PDF file: {filename}, {_format_size(file_size)}. PDF text extraction not available — binary content uploaded.]"

    # Run AI analysis
    if text_content:
        result = analyze_document(filename, text_content)
        analysis_json = json.dumps(result, indent=2)
        db.update_document_analysis(doc_id, analysis_json)

    status = html.Div(
        style={
            "background": COLORS["body_bg"],
            "borderRadius": "8px",
            "padding": "12px 16px",
            "borderLeft": f"4px solid {COLORS['success']}",
        },
        children=[
            html.Span("Uploaded & analyzed: ", style={"color": COLORS["success"], "fontSize": "0.9rem", "fontWeight": "600"}),
            html.Span(filename, style={"color": COLORS["text_primary"], "fontSize": "0.9rem"}),
            html.Span(f" ({_format_size(file_size)})", style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginLeft": "8px"}),
        ],
    )

    return status, _render_doc_list()


@callback(
    Output("doc-list", "children"),
    Input("doc-selected-id", "data"),
)
def refresh_docs(_):
    return _render_doc_list()


@callback(
    Output("doc-detail", "children"),
    Output("doc-selected-id", "data"),
    Input({"type": "doc-view-btn", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def view_document(view_clicks):
    if not ctx.triggered_id:
        return no_update, no_update

    doc_id = ctx.triggered_id["index"]
    doc = db.get_document(doc_id)
    if not doc:
        return html.P("Document not found.", style={"color": COLORS["danger"]}), no_update

    return _render_doc_detail(doc), doc_id


@callback(
    Output("doc-search-results", "children"),
    Input("doc-search-btn", "n_clicks"),
    State("doc-search-input", "value"),
    prevent_initial_call=True,
)
def handle_search(n_clicks, query):
    if not n_clicks or not query or not query.strip():
        return no_update

    docs = db.get_documents()
    if not docs:
        return html.P("No documents uploaded yet. Upload files first, then search.", style={"color": COLORS["warning"], "fontSize": "0.9rem"})

    # Load content for each document
    doc_data = []
    for d in docs:
        content = ""
        if d.get("filepath") and os.path.exists(d["filepath"]):
            ext = d.get("file_type", "")
            if ext in (".txt", ".md", ".csv", ".json"):
                try:
                    with open(d["filepath"], "r", errors="replace") as f:
                        content = f.read(50000)
                except Exception:
                    pass
        doc_data.append({
            "filename": d["filename"],
            "content": content,
            "ai_analysis": d.get("ai_analysis", ""),
        })

    result = search_documents(query.strip(), doc_data)

    return html.Div(
        style={
            "background": COLORS["body_bg"],
            "borderRadius": "8px",
            "padding": "20px",
            "borderLeft": f"3px solid {COLORS['info']}",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "12px"},
                children=[
                    html.I(className="bi bi-stars", style={"color": COLORS["info"]}),
                    html.Span("Search Results", style={"color": COLORS["info"], "fontSize": "0.85rem", "fontWeight": "600"}),
                    html.Span(f"— {len(doc_data)} document{'s' if len(doc_data) != 1 else ''} scanned", style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
                ],
            ),
            dcc.Markdown(
                result,
                style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.6"},
            ),
        ],
    )


def _render_doc_list():
    docs = db.get_documents()
    if not docs:
        return html.Div(
            style={"textAlign": "center", "padding": "48px", "background": COLORS["card_bg"], "borderRadius": "12px"},
            children=[
                html.P("No documents uploaded.", style={"color": COLORS["text_muted"], "fontSize": "1rem", "marginBottom": "8px"}),
                html.P("Upload a file above to get started.", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
            ],
        )

    items = []
    for d in docs:
        has_analysis = bool(d.get("ai_analysis"))
        ext_colors = {
            ".txt": COLORS["info"],
            ".md": COLORS["accent"],
            ".csv": COLORS["success"],
            ".json": COLORS["warning"],
            ".pdf": COLORS["danger"],
        }
        type_color = ext_colors.get(d["file_type"], COLORS["text_muted"])

        items.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "16px 20px",
                    "marginBottom": "8px",
                    "borderLeft": f"4px solid {type_color}",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
                children=[
                    html.Div(
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "4px"},
                                children=[
                                    html.I(className="bi bi-file-earmark-text", style={"color": type_color, "fontSize": "1.1rem"}),
                                    html.Span(d["filename"], style={"color": COLORS["text_primary"], "fontSize": "0.95rem", "fontWeight": "600"}),
                                    html.Span(
                                        d["file_type"].upper(),
                                        style={
                                            "background": type_color,
                                            "color": "#fff",
                                            "padding": "1px 6px",
                                            "borderRadius": "3px",
                                            "fontSize": "0.65rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ],
                            ),
                            html.Div(
                                style={"display": "flex", "gap": "12px"},
                                children=[
                                    html.Span(_format_size(d["file_size"]), style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
                                    html.Span(d["uploaded_at"], style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
                                    html.Span(
                                        "AI Analysis Available" if has_analysis else "",
                                        style={"color": COLORS["success"], "fontSize": "0.8rem"},
                                    ) if has_analysis else None,
                                ],
                            ),
                        ]
                    ),
                    dbc.Button(
                        "View Analysis",
                        id={"type": "doc-view-btn", "index": d["id"]},
                        size="sm",
                        outline=True,
                        color="light",
                        style={"fontSize": "0.75rem"},
                    ),
                ],
            )
        )
    return html.Div(items)


def _render_doc_detail(doc):
    if not doc:
        return None

    children = []

    # Parse AI analysis
    analysis = {}
    if doc.get("ai_analysis"):
        try:
            analysis = json.loads(doc["ai_analysis"])
        except json.JSONDecodeError:
            analysis = {"summary": doc["ai_analysis"]}

    # Header card
    header_children = [
        html.H3(doc["filename"], style={"color": COLORS["text_primary"], "marginBottom": "8px"}),
        html.Div(
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
            children=[
                html.Span(f"Type: {doc['file_type']}", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                html.Span(f"Size: {_format_size(doc['file_size'])}", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                html.Span(f"Uploaded: {doc['uploaded_at']}", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
            ],
        ),
    ]

    # Summary
    if analysis.get("summary"):
        header_children.extend([
            html.H4("Summary", style={"color": COLORS["success"], "fontSize": "0.9rem", "marginBottom": "8px"}),
            html.P(analysis["summary"], style={"color": COLORS["text_secondary"], "fontSize": "0.9rem", "lineHeight": "1.6", "marginBottom": "20px"}),
        ])

    children.append(
        html.Div(
            style={
                "background": COLORS["card_bg"],
                "borderRadius": "12px",
                "padding": "24px",
                "marginTop": "24px",
                "borderLeft": f"4px solid {COLORS['accent']}",
            },
            children=header_children,
        )
    )

    # Key insights
    if analysis.get("key_insights"):
        children.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginTop": "16px",
                    "borderLeft": f"4px solid {COLORS['info']}",
                },
                children=[
                    html.H4("Key Insights", style={"color": COLORS["info"], "marginBottom": "12px"}),
                ] + [
                    html.Div(
                        style={"padding": "8px 0", "borderBottom": f"1px solid {COLORS['border']}"},
                        children=[
                            html.I(className="bi bi-lightbulb", style={"color": COLORS["info"], "marginRight": "8px"}),
                            html.Span(insight, style={"color": COLORS["text_primary"], "fontSize": "0.9rem"}),
                        ],
                    )
                    for insight in analysis["key_insights"]
                ],
            )
        )

    # Entities
    if analysis.get("entities"):
        children.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginTop": "16px",
                    "borderLeft": f"4px solid {COLORS['warning']}",
                },
                children=[
                    html.H4("Entities & References", style={"color": COLORS["warning"], "marginBottom": "12px"}),
                    html.Div(
                        style={"display": "flex", "flexWrap": "wrap", "gap": "8px"},
                        children=[
                            html.Span(
                                entity,
                                style={
                                    "background": COLORS["body_bg"],
                                    "color": COLORS["text_primary"],
                                    "padding": "4px 12px",
                                    "borderRadius": "16px",
                                    "fontSize": "0.85rem",
                                    "border": f"1px solid {COLORS['border']}",
                                },
                            )
                            for entity in analysis["entities"]
                        ],
                    ),
                ],
            )
        )

    # Action items
    if analysis.get("action_items"):
        children.append(
            html.Div(
                style={
                    "background": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "padding": "24px",
                    "marginTop": "16px",
                    "borderLeft": f"4px solid {COLORS['success']}",
                },
                children=[
                    html.H4("Action Items", style={"color": COLORS["success"], "marginBottom": "12px"}),
                ] + [
                    html.Div(
                        style={"padding": "8px 0", "borderBottom": f"1px solid {COLORS['border']}"},
                        children=[
                            html.I(className="bi bi-check-circle", style={"color": COLORS["success"], "marginRight": "8px"}),
                            html.Span(item, style={"color": COLORS["text_primary"], "fontSize": "0.9rem"}),
                        ],
                    )
                    for item in analysis["action_items"]
                ],
            )
        )

    # Raw content preview
    if doc.get("filepath") and os.path.exists(doc["filepath"]):
        ext = doc["file_type"]
        if ext in (".txt", ".md", ".csv", ".json"):
            try:
                with open(doc["filepath"], "r", errors="replace") as f:
                    raw_preview = f.read(5000)
                if len(raw_preview) >= 5000:
                    raw_preview += "\n\n[... truncated ...]"
                children.append(
                    html.Div(
                        style={
                            "background": COLORS["card_bg"],
                            "borderRadius": "12px",
                            "padding": "24px",
                            "marginTop": "16px",
                            "borderLeft": f"4px solid {COLORS['border']}",
                        },
                        children=[
                            html.H4("Raw Content Preview", style={"color": COLORS["text_secondary"], "marginBottom": "12px"}),
                            html.Pre(
                                raw_preview,
                                style={
                                    "color": COLORS["text_secondary"],
                                    "background": COLORS["body_bg"],
                                    "padding": "16px",
                                    "borderRadius": "8px",
                                    "whiteSpace": "pre-wrap",
                                    "fontSize": "0.8rem",
                                    "maxHeight": "400px",
                                    "overflowY": "auto",
                                },
                            ),
                        ],
                    )
                )
            except Exception:
                pass

    return html.Div(children)
