"""
Rules page — automation controls, read-only mode, confidence threshold,
automation level questionnaire, account exclusions, persona instructions & goals.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL, MATCH
import dash_bootstrap_components as dbc
from config import COLORS
import db

dash.register_page(__name__, path="/rules", name="Rules", order=11)


# ── Constants ──

AUTOMATION_LEVELS = {
    "manual": {
        "label": "Manual",
        "description": "AI drafts replies for you to review. Nothing is auto-approved or sent without your action.",
    },
    "supervised": {
        "label": "Supervised",
        "description": "AI drafts replies and flags high-confidence ones. You still approve and send everything.",
    },
    "semi_auto": {
        "label": "Semi-Automatic",
        "description": "Routine replies (meeting confirms, acknowledgments) are auto-approved above threshold. Complex emails need your review.",
    },
    "full_auto": {
        "label": "Full Automatic",
        "description": "All replies above the confidence threshold are auto-approved. You can still review before sending.",
    },
}

THRESHOLD_MARKS = {
    0.50: "Permissive",
    0.70: "Moderate",
    0.85: "Conservative (recommended)",
    1.00: "Strictest",
}


def _threshold_description(value):
    if value <= 0.55:
        return "Very permissive — most drafts will be auto-approved"
    elif value <= 0.74:
        return "Moderate — routine replies will typically be auto-approved"
    elif value <= 0.89:
        return "Conservative — only highly confident replies auto-approved"
    return "Very strict — almost nothing will be auto-approved"


def _card(children, border_color=None, **style_overrides):
    style = {
        "background": COLORS["card_bg"],
        "borderRadius": "12px",
        "padding": "24px",
        "marginBottom": "20px",
    }
    if border_color:
        style["borderLeft"] = f"4px solid {border_color}"
    style.update(style_overrides)
    return html.Div(style=style, children=children)


def layout():
    # Load current settings
    read_only = db.get_setting("read_only_mode", "false") == "true"
    automation_level = db.get_setting("automation_level", "manual")
    questionnaire_done = db.get_setting("automation_questionnaire_completed", "false") == "true"
    threshold = float(db.get_setting("persona_confidence_threshold", "0.85"))
    exclusions = db.get_exclusions()
    persona_instructions = db.get_setting("persona_instructions", "")
    persona_goals = db.get_setting("persona_goals", "")

    # Parse stored lists
    try:
        instructions_list = json.loads(persona_instructions) if persona_instructions else []
    except Exception:
        instructions_list = []
    try:
        goals_list = json.loads(persona_goals) if persona_goals else []
    except Exception:
        goals_list = []

    return html.Div(
        children=[
            # Hidden stores for state management
            dcc.Store(id="rules-exclusions-refresh", data=0),
            dcc.Store(id="rules-questionnaire-state", data="hidden" if questionnaire_done else "visible"),
            dcc.Store(id="rules-instructions-refresh", data=0),

            # Header
            html.Div(
                style={"marginBottom": "24px"},
                children=[
                    html.H2(
                        [html.I(className="bi bi-shield-check", style={"marginRight": "12px"}), "Rules & Automation"],
                        style={"color": COLORS["text_primary"], "margin": 0},
                    ),
                    html.P(
                        "Control how CloneAI handles your email. Set automation levels, exclusions, and persona instructions.",
                        style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                    ),
                ],
            ),

            # ── Description / Capabilities Section ──
            _card(
                [
                    html.H4(
                        [html.I(className="bi bi-info-circle", style={"marginRight": "8px"}), "How CloneAI Works"],
                        style={"color": COLORS["text_primary"], "marginBottom": "12px"},
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
                        children=[
                            html.Div([
                                html.H6("Persona Training", style={"color": COLORS["accent"], "marginBottom": "6px"}),
                                html.P(
                                    "Ingests your sent emails, chat exports, and documents to learn your writing style, tone, and vocabulary. "
                                    "Uses RAG (Retrieval-Augmented Generation) with ChromaDB embeddings to find similar past communications when drafting replies.",
                                    style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "margin": 0},
                                ),
                            ]),
                            html.Div([
                                html.H6("Draft Generation", style={"color": COLORS["warning"], "marginBottom": "6px"}),
                                html.P(
                                    "Analyzes incoming emails, retrieves your most relevant past responses, and uses Claude AI to draft replies in your voice. "
                                    "Each draft includes a confidence score, category, and AI reasoning for transparency.",
                                    style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "margin": 0},
                                ),
                            ]),
                            html.Div([
                                html.H6("Automation Levels", style={"color": COLORS["success"], "marginBottom": "6px"}),
                                html.P(
                                    "Four levels from fully manual to fully automatic. Semi-auto mode handles routine replies (meeting confirms, acknowledgments) "
                                    "automatically while escalating complex emails for your review.",
                                    style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "margin": 0},
                                ),
                            ]),
                            html.Div([
                                html.H6("Safety Controls", style={"color": COLORS["danger"], "marginBottom": "6px"}),
                                html.P(
                                    "Read-only mode prevents all outbound communication. Account exclusions block specific senders or domains. "
                                    "Confidence thresholds ensure only high-quality drafts are auto-approved.",
                                    style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "margin": 0},
                                ),
                            ]),
                        ],
                    ),
                ],
                border_color=COLORS["info"],
            ),

            # Main layout: two columns
            dbc.Row(
                [
                    # ── Left column: Read-Only + Automation Level + Persona Instructions ──
                    dbc.Col(
                        [
                            # Card 1: Read-Only Mode
                            _card(
                                [
                                    html.Div(
                                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"},
                                        children=[
                                            html.H4(
                                                [html.I(className="bi bi-eye", style={"marginRight": "8px"}), "Read-Only Mode"],
                                                style={"color": COLORS["text_primary"], "margin": 0},
                                            ),
                                            dbc.Switch(
                                                id="rules-read-only-toggle",
                                                value=read_only,
                                                style={"transform": "scale(1.3)"},
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        "When enabled, CloneAI only reads and ingests data for persona training. No emails will be sent or auto-approved.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "margin": "0 0 8px 0"},
                                    ),
                                    html.Div(id="rules-read-only-status"),
                                ],
                                border_color=COLORS["danger"] if read_only else COLORS["text_muted"],
                            ),

                            # Card 2: Automation Level
                            _card(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-sliders", style={"marginRight": "8px"}), "Automation Level"],
                                        style={"color": COLORS["text_primary"], "marginBottom": "16px"},
                                    ),

                                    # Questionnaire section
                                    html.Div(
                                        id="rules-questionnaire-section",
                                        style={"display": "none" if questionnaire_done else "block"},
                                        children=[
                                            html.P(
                                                "Answer these questions so we can recommend an automation level for you.",
                                                style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"},
                                            ),
                                            # Q1
                                            html.Label(
                                                "How comfortable are you with AI drafting emails in your voice?",
                                                style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "fontWeight": "600", "marginBottom": "8px", "display": "block"},
                                            ),
                                            dbc.RadioItems(
                                                id="rules-q1",
                                                options=[
                                                    {"label": "Not comfortable", "value": "0"},
                                                    {"label": "Somewhat comfortable", "value": "1"},
                                                    {"label": "Very comfortable", "value": "2"},
                                                ],
                                                inline=True,
                                                style={"marginBottom": "16px"},
                                            ),
                                            # Q2
                                            html.Label(
                                                "Should routine replies (meeting confirms, acknowledgments) be handled automatically?",
                                                style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "fontWeight": "600", "marginBottom": "8px", "display": "block"},
                                            ),
                                            dbc.RadioItems(
                                                id="rules-q2",
                                                options=[
                                                    {"label": "No, I review everything", "value": "0"},
                                                    {"label": "Yes, with my review", "value": "1"},
                                                    {"label": "Yes, fully automatic", "value": "2"},
                                                ],
                                                inline=True,
                                                style={"marginBottom": "16px"},
                                            ),
                                            # Q3
                                            html.Label(
                                                "Should the AI ever send emails without your explicit approval?",
                                                style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "fontWeight": "600", "marginBottom": "8px", "display": "block"},
                                            ),
                                            dbc.RadioItems(
                                                id="rules-q3",
                                                options=[
                                                    {"label": "Never", "value": "0"},
                                                    {"label": "Only high-confidence routine emails", "value": "1"},
                                                    {"label": "Yes, above confidence threshold", "value": "2"},
                                                ],
                                                inline=True,
                                                style={"marginBottom": "16px"},
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-lightbulb", style={"marginRight": "6px"}), "Get Recommendation"],
                                                id="rules-get-recommendation",
                                                color="primary",
                                                size="sm",
                                                style={"background": COLORS["accent"], "border": "none", "marginBottom": "16px"},
                                            ),
                                            html.Div(id="rules-recommendation-result", style={"marginBottom": "16px"}),
                                            html.Hr(style={"borderColor": COLORS["border"]}),
                                        ],
                                    ),

                                    # Automation level radio buttons (always visible)
                                    html.Label(
                                        "Current Automation Level",
                                        style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "fontWeight": "600", "marginBottom": "8px", "display": "block"},
                                    ),
                                    dbc.RadioItems(
                                        id="rules-automation-level",
                                        options=[
                                            {"label": html.Span([
                                                html.Strong(info["label"], style={"color": COLORS["text_primary"]}),
                                                html.Span(f" — {info['description']}", style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
                                            ]), "value": level_key}
                                            for level_key, info in AUTOMATION_LEVELS.items()
                                        ],
                                        value=automation_level,
                                        style={"marginBottom": "16px"},
                                    ),
                                    html.Div(id="rules-automation-level-status", style={"marginBottom": "16px"}),

                                    # Retake questionnaire button
                                    dbc.Button(
                                        [html.I(className="bi bi-arrow-repeat", style={"marginRight": "6px"}), "Retake Questionnaire"],
                                        id="rules-retake-questionnaire",
                                        size="sm",
                                        color="secondary",
                                        outline=True,
                                        style={"marginBottom": "16px"},
                                    ) if questionnaire_done else None,

                                    html.Hr(style={"borderColor": COLORS["border"]}),

                                    # Confidence Threshold Slider
                                    html.Label(
                                        "Confidence Threshold",
                                        style={"color": COLORS["text_secondary"], "fontSize": "0.85rem", "fontWeight": "600", "marginBottom": "8px", "display": "block"},
                                    ),
                                    dcc.Slider(
                                        id="rules-confidence-threshold",
                                        min=0.50,
                                        max=1.00,
                                        step=0.05,
                                        value=threshold,
                                        marks={k: {"label": v, "style": {"color": COLORS["text_muted"], "fontSize": "0.7rem"}} for k, v in THRESHOLD_MARKS.items()},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(
                                        id="rules-threshold-description",
                                        style={"marginTop": "8px"},
                                        children=[
                                            html.Span(
                                                _threshold_description(threshold),
                                                style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "fontStyle": "italic"},
                                            ),
                                        ],
                                    ),
                                    html.Div(id="rules-threshold-status", style={"marginTop": "8px"}),
                                ],
                                border_color=COLORS["accent"],
                            ),

                            # Card: Persona Instructions
                            _card(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-journal-text", style={"marginRight": "8px"}), "Persona Instructions"],
                                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                                    ),
                                    html.P(
                                        "Add custom instructions to guide how the AI writes in your voice. These are injected into every draft generation prompt.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "12px"},
                                    ),

                                    # Add new instruction
                                    html.Div(
                                        style={"display": "flex", "gap": "8px", "marginBottom": "12px"},
                                        children=[
                                            dbc.Input(
                                                id="rules-new-instruction",
                                                placeholder="e.g., Always sign off with 'Best regards'",
                                                style={
                                                    "background": COLORS["body_bg"],
                                                    "border": f"1px solid {COLORS['border']}",
                                                    "color": COLORS["text_primary"],
                                                    "borderRadius": "8px",
                                                    "flex": "1",
                                                    "fontSize": "0.85rem",
                                                },
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-plus-lg")],
                                                id="rules-add-instruction",
                                                color="primary",
                                                size="sm",
                                                style={"background": COLORS["accent"], "border": "none"},
                                            ),
                                        ],
                                    ),

                                    # Display current instructions
                                    html.Div(id="rules-instructions-display", children=_render_instructions(instructions_list)),

                                    html.Hr(style={"borderColor": COLORS["border"], "margin": "16px 0"}),

                                    # Goals subsection
                                    html.H5(
                                        [html.I(className="bi bi-bullseye", style={"marginRight": "8px"}), "Goals"],
                                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                                    ),
                                    html.P(
                                        "Define goals for your AI persona. Goals guide the overall intent and priorities of generated replies.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "12px"},
                                    ),

                                    # Add new goal
                                    html.Div(
                                        style={"display": "flex", "gap": "8px", "marginBottom": "12px"},
                                        children=[
                                            dbc.Input(
                                                id="rules-new-goal",
                                                placeholder="e.g., Prioritize closing deals in all sales-related replies",
                                                style={
                                                    "background": COLORS["body_bg"],
                                                    "border": f"1px solid {COLORS['border']}",
                                                    "color": COLORS["text_primary"],
                                                    "borderRadius": "8px",
                                                    "flex": "1",
                                                    "fontSize": "0.85rem",
                                                },
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-plus-lg")],
                                                id="rules-add-goal",
                                                color="warning",
                                                size="sm",
                                                outline=True,
                                            ),
                                        ],
                                    ),

                                    # Display current goals
                                    html.Div(id="rules-goals-display", children=_render_goals(goals_list)),
                                ],
                                border_color=COLORS["info"],
                            ),
                        ],
                        md=7,
                    ),

                    # ── Right column: Exclusions ──
                    dbc.Col(
                        [
                            # Card 3: Account Exclusions
                            _card(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-person-x", style={"marginRight": "8px"}), "Account Exclusions"],
                                        style={"color": COLORS["text_primary"], "marginBottom": "8px"},
                                    ),
                                    html.P(
                                        "Enter an email address (user@example.com) or domain (@example.com). "
                                        "Emails matching these will never receive auto-replies.",
                                        style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "marginBottom": "16px"},
                                    ),
                                    # Add exclusion form
                                    dbc.Input(
                                        id="rules-exclusion-pattern",
                                        placeholder="Email or @domain",
                                        style={
                                            "background": COLORS["body_bg"],
                                            "border": f"1px solid {COLORS['border']}",
                                            "color": COLORS["text_primary"],
                                            "borderRadius": "8px",
                                            "marginBottom": "8px",
                                            "fontSize": "0.85rem",
                                        },
                                    ),
                                    dbc.Input(
                                        id="rules-exclusion-reason",
                                        placeholder="Reason (optional)",
                                        style={
                                            "background": COLORS["body_bg"],
                                            "border": f"1px solid {COLORS['border']}",
                                            "color": COLORS["text_primary"],
                                            "borderRadius": "8px",
                                            "marginBottom": "10px",
                                            "fontSize": "0.85rem",
                                        },
                                    ),
                                    dbc.Button(
                                        [html.I(className="bi bi-plus-lg", style={"marginRight": "6px"}), "Add Exclusion"],
                                        id="rules-add-exclusion",
                                        size="sm",
                                        color="danger",
                                        outline=True,
                                        style={"marginBottom": "16px"},
                                    ),
                                    html.Div(id="rules-exclusion-status", style={"marginBottom": "12px"}),
                                    # Exclusions list
                                    html.Div(
                                        id="rules-exclusions-list",
                                        children=_render_exclusions(exclusions),
                                    ),
                                ],
                                border_color=COLORS["warning"],
                            ),

                            # Active Rules Summary
                            _card(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-list-check", style={"marginRight": "8px"}), "Active Rules Summary"],
                                        style={"color": COLORS["text_primary"], "marginBottom": "12px"},
                                    ),
                                    html.Div(id="rules-summary-display", children=_render_rules_summary(
                                        read_only, automation_level, threshold, len(exclusions),
                                        len(instructions_list), len(goals_list),
                                    )),
                                ],
                                border_color=COLORS["success"],
                            ),
                        ],
                        md=5,
                    ),
                ],
            ),
        ]
    )


# ── Render helpers ──

def _render_exclusions(exclusions):
    if not exclusions:
        return html.P(
            "No exclusions configured.",
            style={"color": COLORS["text_muted"], "fontSize": "0.85rem"},
        )

    items = []
    for exc in exclusions:
        items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "background": COLORS["body_bg"],
                    "borderRadius": "8px",
                    "padding": "10px 14px",
                    "marginBottom": "8px",
                },
                children=[
                    html.Div([
                        html.Span(
                            exc["pattern"],
                            style={"color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "600"},
                        ),
                        html.Span(
                            f" — {exc['reason']}" if exc.get("reason") else "",
                            style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
                        ),
                    ]),
                    dbc.Button(
                        html.I(className="bi bi-x-lg"),
                        id={"type": "rules-delete-exclusion", "index": exc["id"]},
                        size="sm",
                        color="danger",
                        outline=True,
                        style={"padding": "2px 8px", "fontSize": "0.75rem"},
                    ),
                ],
            )
        )
    return html.Div(items)


def _render_instructions(instructions_list):
    if not instructions_list:
        return html.P(
            "No custom instructions yet.",
            style={"color": COLORS["text_muted"], "fontSize": "0.85rem"},
        )
    items = []
    for i, instruction in enumerate(instructions_list):
        items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "background": COLORS["body_bg"],
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "marginBottom": "6px",
                },
                children=[
                    html.Span(
                        instruction,
                        style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "flex": "1"},
                    ),
                    dbc.Button(
                        html.I(className="bi bi-x-lg"),
                        id={"type": "rules-delete-instruction", "index": i},
                        size="sm",
                        color="secondary",
                        outline=True,
                        style={"padding": "2px 6px", "fontSize": "0.7rem"},
                    ),
                ],
            )
        )
    return html.Div(items)


def _render_goals(goals_list):
    if not goals_list:
        return html.P(
            "No goals defined yet.",
            style={"color": COLORS["text_muted"], "fontSize": "0.85rem"},
        )
    items = []
    for i, goal in enumerate(goals_list):
        items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "background": COLORS["body_bg"],
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "marginBottom": "6px",
                    "borderLeft": f"3px solid {COLORS['warning']}",
                },
                children=[
                    html.Span(
                        goal,
                        style={"color": COLORS["text_secondary"], "fontSize": "0.8rem", "flex": "1"},
                    ),
                    dbc.Button(
                        html.I(className="bi bi-x-lg"),
                        id={"type": "rules-delete-goal", "index": i},
                        size="sm",
                        color="secondary",
                        outline=True,
                        style={"padding": "2px 6px", "fontSize": "0.7rem"},
                    ),
                ],
            )
        )
    return html.Div(items)


def _render_rules_summary(read_only, automation_level, threshold, exclusion_count,
                          instruction_count, goal_count):
    level_info = AUTOMATION_LEVELS.get(automation_level, AUTOMATION_LEVELS["manual"])
    items = []

    # Read-only status
    if read_only:
        items.append(_summary_row("bi bi-eye-fill", "Read-Only Mode", "ACTIVE — no outbound emails", COLORS["danger"]))
    else:
        items.append(_summary_row("bi bi-eye", "Read-Only Mode", "Disabled", COLORS["text_muted"]))

    # Automation level
    items.append(_summary_row("bi bi-sliders", "Automation", level_info["label"], COLORS["accent"]))

    # Threshold
    items.append(_summary_row("bi bi-speedometer2", "Threshold", f"{threshold:.0%} — {_threshold_description(threshold).split('—')[0].strip()}", COLORS["info"]))

    # Exclusions
    items.append(_summary_row("bi bi-person-x", "Exclusions", f"{exclusion_count} rule{'s' if exclusion_count != 1 else ''}", COLORS["warning"]))

    # Instructions
    items.append(_summary_row("bi bi-journal-text", "Instructions", f"{instruction_count} custom instruction{'s' if instruction_count != 1 else ''}", COLORS["info"]))

    # Goals
    items.append(_summary_row("bi bi-bullseye", "Goals", f"{goal_count} goal{'s' if goal_count != 1 else ''}", COLORS["warning"]))

    return html.Div(items)


def _summary_row(icon_cls, label, value, color):
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "10px"},
        children=[
            html.I(className=icon_cls, style={"color": color, "fontSize": "1rem", "width": "20px"}),
            html.Span(label + ":", style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "fontWeight": "600", "minWidth": "90px"}),
            html.Span(value, style={"color": COLORS["text_secondary"], "fontSize": "0.8rem"}),
        ],
    )


# ══════════════════════════════════════════════
# Callbacks
# ══════════════════════════════════════════════

# 1. Save read-only toggle
@callback(
    Output("rules-read-only-status", "children"),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input("rules-read-only-toggle", "value"),
    prevent_initial_call=True,
)
def save_read_only(enabled):
    db.save_setting("read_only_mode", "true" if enabled else "false")
    status_text = "Read-only mode enabled." if enabled else "Read-only mode disabled."
    color = COLORS["danger"] if enabled else COLORS["success"]

    badge = html.Span(status_text, style={"color": color, "fontSize": "0.8rem"})
    if enabled:
        badge = html.Div([
            html.Span(
                [html.I(className="bi bi-exclamation-triangle-fill", style={"marginRight": "6px"}), status_text],
                style={"color": color, "fontSize": "0.8rem", "fontWeight": "600"},
            ),
        ])

    return badge, _get_updated_summary()


# 2. Process questionnaire
@callback(
    Output("rules-recommendation-result", "children"),
    Output("rules-automation-level", "value", allow_duplicate=True),
    Input("rules-get-recommendation", "n_clicks"),
    State("rules-q1", "value"),
    State("rules-q2", "value"),
    State("rules-q3", "value"),
    prevent_initial_call=True,
)
def process_questionnaire(n_clicks, q1, q2, q3):
    if not n_clicks:
        return no_update, no_update

    if q1 is None or q2 is None or q3 is None:
        return html.Span(
            "Please answer all three questions.",
            style={"color": COLORS["warning"], "fontSize": "0.85rem"},
        ), no_update

    total = int(q1) + int(q2) + int(q3)

    if total <= 1:
        level = "manual"
    elif total <= 3:
        level = "supervised"
    elif total <= 5:
        level = "semi_auto"
    else:
        level = "full_auto"

    db.save_setting("automation_level", level)
    db.save_setting("automation_questionnaire_completed", "true")

    level_info = AUTOMATION_LEVELS[level]
    return html.Span(
        [
            html.I(className="bi bi-check-circle-fill", style={"marginRight": "6px", "color": COLORS["success"]}),
            f"Recommended: {level_info['label']}",
        ],
        style={"color": COLORS["success"], "fontSize": "0.85rem"},
    ), level


# 3. Save automation level (manual override)
@callback(
    Output("rules-automation-level-status", "children"),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input("rules-automation-level", "value"),
    prevent_initial_call=True,
)
def save_automation_level(level):
    if not level:
        return no_update, no_update
    db.save_setting("automation_level", level)
    level_info = AUTOMATION_LEVELS.get(level, AUTOMATION_LEVELS["manual"])
    return html.Span(
        f"Automation set to: {level_info['label']}",
        style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
    ), _get_updated_summary()


# 4. Save threshold + update description
@callback(
    Output("rules-threshold-description", "children"),
    Output("rules-threshold-status", "children"),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input("rules-confidence-threshold", "value"),
    prevent_initial_call=True,
)
def save_threshold(value):
    if value is None:
        return no_update, no_update, no_update
    db.save_setting("persona_confidence_threshold", str(value))
    desc = _threshold_description(value)
    return (
        html.Span(desc, style={"color": COLORS["text_muted"], "fontSize": "0.8rem", "fontStyle": "italic"}),
        html.Span(f"Threshold saved: {value:.2f}", style={"color": COLORS["text_muted"], "fontSize": "0.8rem"}),
        _get_updated_summary(),
    )


# 5. Add exclusion
@callback(
    Output("rules-exclusions-list", "children"),
    Output("rules-exclusion-status", "children"),
    Output("rules-exclusion-pattern", "value"),
    Output("rules-exclusion-reason", "value"),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input("rules-add-exclusion", "n_clicks"),
    State("rules-exclusion-pattern", "value"),
    State("rules-exclusion-reason", "value"),
    prevent_initial_call=True,
)
def add_exclusion(n_clicks, pattern, reason):
    if not n_clicks or not pattern or not pattern.strip():
        return no_update, no_update, no_update, no_update, no_update

    pattern = pattern.strip()
    db.add_exclusion(pattern, reason or "")
    exclusions = db.get_exclusions()

    return (
        _render_exclusions(exclusions),
        html.Span(f"Added: {pattern}", style={"color": COLORS["success"], "fontSize": "0.8rem"}),
        "",
        "",
        _get_updated_summary(),
    )


# 6. Delete exclusion (pattern-matching callback)
@callback(
    Output("rules-exclusions-list", "children", allow_duplicate=True),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input({"type": "rules-delete-exclusion", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def delete_exclusion(n_clicks_list):
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update

    if not any(n for n in n_clicks_list if n):
        return no_update, no_update

    exclusion_id = triggered["index"]
    db.remove_exclusion(exclusion_id)
    exclusions = db.get_exclusions()
    return _render_exclusions(exclusions), _get_updated_summary()


# 7. Retake questionnaire
@callback(
    Output("rules-questionnaire-section", "style"),
    Input("rules-retake-questionnaire", "n_clicks"),
    prevent_initial_call=True,
)
def retake_questionnaire(n_clicks):
    if not n_clicks:
        return no_update
    db.save_setting("automation_questionnaire_completed", "false")
    return {"display": "block"}


# 8. Add persona instruction
@callback(
    Output("rules-instructions-display", "children"),
    Output("rules-new-instruction", "value"),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input("rules-add-instruction", "n_clicks"),
    Input({"type": "rules-delete-instruction", "index": ALL}, "n_clicks"),
    State("rules-new-instruction", "value"),
    prevent_initial_call=True,
)
def manage_instructions(add_clicks, delete_clicks, new_instruction):
    triggered = ctx.triggered_id
    raw = db.get_setting("persona_instructions", "")
    try:
        instructions = json.loads(raw) if raw else []
    except Exception:
        instructions = []

    if triggered == "rules-add-instruction" and add_clicks:
        if new_instruction and new_instruction.strip():
            instructions.append(new_instruction.strip())
            db.save_setting("persona_instructions", json.dumps(instructions))
            return _render_instructions(instructions), "", _get_updated_summary()
        return no_update, no_update, no_update

    if isinstance(triggered, dict) and triggered.get("type") == "rules-delete-instruction":
        if any(n for n in delete_clicks if n):
            idx = triggered["index"]
            if 0 <= idx < len(instructions):
                instructions.pop(idx)
                db.save_setting("persona_instructions", json.dumps(instructions))
                return _render_instructions(instructions), no_update, _get_updated_summary()

    return no_update, no_update, no_update


# 9. Add/delete persona goal
@callback(
    Output("rules-goals-display", "children"),
    Output("rules-new-goal", "value"),
    Output("rules-summary-display", "children", allow_duplicate=True),
    Input("rules-add-goal", "n_clicks"),
    Input({"type": "rules-delete-goal", "index": ALL}, "n_clicks"),
    State("rules-new-goal", "value"),
    prevent_initial_call=True,
)
def manage_goals(add_clicks, delete_clicks, new_goal):
    triggered = ctx.triggered_id
    raw = db.get_setting("persona_goals", "")
    try:
        goals = json.loads(raw) if raw else []
    except Exception:
        goals = []

    if triggered == "rules-add-goal" and add_clicks:
        if new_goal and new_goal.strip():
            goals.append(new_goal.strip())
            db.save_setting("persona_goals", json.dumps(goals))
            return _render_goals(goals), "", _get_updated_summary()
        return no_update, no_update, no_update

    if isinstance(triggered, dict) and triggered.get("type") == "rules-delete-goal":
        if any(n for n in delete_clicks if n):
            idx = triggered["index"]
            if 0 <= idx < len(goals):
                goals.pop(idx)
                db.save_setting("persona_goals", json.dumps(goals))
                return _render_goals(goals), no_update, _get_updated_summary()

    return no_update, no_update, no_update


# ── Summary helper ──

def _get_updated_summary():
    read_only = db.get_setting("read_only_mode", "false") == "true"
    automation_level = db.get_setting("automation_level", "manual")
    threshold = float(db.get_setting("persona_confidence_threshold", "0.85"))
    exclusion_count = len(db.get_exclusions())

    raw_instructions = db.get_setting("persona_instructions", "")
    try:
        instruction_count = len(json.loads(raw_instructions)) if raw_instructions else 0
    except Exception:
        instruction_count = 0

    raw_goals = db.get_setting("persona_goals", "")
    try:
        goal_count = len(json.loads(raw_goals)) if raw_goals else 0
    except Exception:
        goal_count = 0

    return _render_rules_summary(
        read_only, automation_level, threshold, exclusion_count,
        instruction_count, goal_count,
    )
