"""
CRM page — client relationships, deal pipeline, and tracking.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from datetime import datetime
from config import COLORS
import db

dash.register_page(__name__, path="/crm", name="CRM", order=7)

STAGE_COLORS = {
    "prospect": COLORS["text_muted"],
    "proposal": COLORS["info"],
    "negotiation": COLORS["warning"],
    "won": COLORS["success"],
    "lost": COLORS["danger"],
}

STATUS_COLORS = {
    "active": COLORS["success"],
    "prospect": COLORS["info"],
    "inactive": COLORS["text_muted"],
}

STAGE_ORDER = ["prospect", "proposal", "negotiation", "won", "lost"]


def _kpi(label, value, subtitle=None, color=COLORS["text_primary"]):
    children = [
        html.P(label, style={
            "color": COLORS["text_muted"], "fontSize": "0.7rem", "margin": "0 0 4px 0",
            "textTransform": "uppercase", "letterSpacing": "1px",
        }),
        html.P(value, style={
            "color": color, "fontSize": "1.5rem", "margin": 0, "fontWeight": "800",
        }),
    ]
    if subtitle:
        children.append(html.P(subtitle, style={
            "color": COLORS["text_muted"], "fontSize": "0.7rem", "margin": "2px 0 0 0",
        }))
    return html.Div(style={
        "textAlign": "center", "padding": "16px", "background": COLORS["card_bg"],
        "borderRadius": "12px", "flex": "1", "minWidth": "140px",
    }, children=children)


# ── Layout ──

layout = html.Div(children=[
    dcc.Store(id="crm-refresh", data=0),
    dcc.Store(id="crm-client-filter", data="all"),

    # Header
    html.Div(
        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
        children=[
            html.Div(children=[
                html.H2("Client Relationships", style={"color": COLORS["text_primary"], "margin": 0}),
                html.P("Manage clients and track your deal pipeline.", style={
                    "color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0",
                }),
            ]),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                dbc.Button(
                    [html.I(className="bi bi-person-plus", style={"marginRight": "8px"}), "Add Client"],
                    id="btn-toggle-client-form", color="primary",
                    style={"background": COLORS["accent"], "border": "none"},
                ),
                dbc.Button(
                    [html.I(className="bi bi-plus-lg", style={"marginRight": "8px"}), "Add Deal"],
                    id="btn-toggle-deal-form", color="success",
                    style={"background": COLORS["success"], "border": "none"},
                ),
            ]),
        ],
    ),

    # KPI row
    html.Div(id="crm-kpi-row", style={
        "display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap",
    }),

    # Add Client Form
    dbc.Collapse(id="client-form-collapse", is_open=False, children=[
        html.Div(style={
            "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
            "marginBottom": "24px", "borderLeft": f"4px solid {COLORS['accent']}",
        }, children=[
            html.H4("New Client", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Name *", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-client-name", placeholder="Client name...", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
                dbc.Col([
                    dbc.Label("Email", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-client-email", placeholder="email@example.com", type="email", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
                dbc.Col([
                    dbc.Label("Phone", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-client-phone", placeholder="Phone number...", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Company", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-client-company", placeholder="Company name...", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
                dbc.Col([
                    dbc.Label("Status", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dcc.Dropdown(
                        id="crm-client-status",
                        options=[
                            {"label": "Active", "value": "active"},
                            {"label": "Prospect", "value": "prospect"},
                            {"label": "Inactive", "value": "inactive"},
                        ],
                        value="active",
                        style={"fontSize": "0.9rem"},
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Notes", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-client-notes", placeholder="Optional notes...", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
            ], className="mb-3"),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                dbc.Button("Save Client", id="btn-save-client", color="success", style={
                    "background": COLORS["success"], "border": "none",
                }),
                dbc.Button("Cancel", id="btn-cancel-client", outline=True, color="secondary"),
            ]),
            html.Div(id="client-form-status", style={"marginTop": "8px"}),
        ]),
    ]),

    # Add Deal Form
    dbc.Collapse(id="deal-form-collapse", is_open=False, children=[
        html.Div(style={
            "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
            "marginBottom": "24px", "borderLeft": f"4px solid {COLORS['success']}",
        }, children=[
            html.H4("New Deal", style={"color": COLORS["text_primary"], "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Client *", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dcc.Dropdown(id="crm-deal-client", placeholder="Select client...", style={"fontSize": "0.9rem"}),
                ], md=4),
                dbc.Col([
                    dbc.Label("Deal Title *", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-deal-title", placeholder="Deal title...", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
                dbc.Col([
                    dbc.Label("Value ($)", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-deal-value", type="number", placeholder="0", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Stage", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dcc.Dropdown(
                        id="crm-deal-stage",
                        options=[{"label": s.title(), "value": s} for s in STAGE_ORDER],
                        value="prospect",
                        style={"fontSize": "0.9rem"},
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Expected Close", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-deal-close", type="date", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
                dbc.Col([
                    dbc.Label("Notes", style={"color": COLORS["text_secondary"], "fontSize": "0.85rem"}),
                    dbc.Input(id="crm-deal-notes", placeholder="Optional notes...", style={
                        "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_primary"],
                    }),
                ], md=4),
            ], className="mb-3"),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                dbc.Button("Save Deal", id="btn-save-deal", color="success", style={
                    "background": COLORS["success"], "border": "none",
                }),
                dbc.Button("Cancel", id="btn-cancel-deal", outline=True, color="secondary"),
            ]),
            html.Div(id="deal-form-status", style={"marginTop": "8px"}),
        ]),
    ]),

    # Two-column layout
    dbc.Row([
        # Left: Client list
        dbc.Col([
            html.Div(style={
                "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
                "borderLeft": f"4px solid {COLORS['accent']}",
            }, children=[
                html.Div(style={
                    "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                    "marginBottom": "16px",
                }, children=[
                    html.H4([html.I(className="bi bi-people", style={"marginRight": "10px"}), "Clients"],
                             style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1rem"}),
                    html.Div(style={"display": "flex", "gap": "6px"}, children=[
                        dbc.Button("All", id="crm-filter-all", size="sm", outline=True, color="light", style={"fontSize": "0.75rem"}),
                        dbc.Button("Active", id="crm-filter-active", size="sm", outline=True, color="success", style={"fontSize": "0.75rem"}),
                        dbc.Button("Prospect", id="crm-filter-prospect", size="sm", outline=True, color="info", style={"fontSize": "0.75rem"}),
                        dbc.Button("Inactive", id="crm-filter-inactive", size="sm", outline=True, color="secondary", style={"fontSize": "0.75rem"}),
                    ]),
                ]),
                html.Div(id="crm-client-list"),
            ]),
        ], md=7),
        # Right: Deal pipeline
        dbc.Col([
            html.Div(style={
                "background": COLORS["card_bg"], "borderRadius": "12px", "padding": "24px",
                "borderLeft": f"4px solid {COLORS['success']}",
            }, children=[
                html.H4([html.I(className="bi bi-funnel", style={"marginRight": "10px"}), "Deal Pipeline"],
                         style={"color": COLORS["text_primary"], "margin": "0 0 16px 0", "fontSize": "1rem"}),
                html.Div(id="crm-deal-pipeline"),
            ]),
        ], md=5),
    ]),
])


# ── Callbacks ──

# Toggle client form
@callback(
    Output("client-form-collapse", "is_open"),
    Input("btn-toggle-client-form", "n_clicks"),
    Input("btn-cancel-client", "n_clicks"),
    Input("btn-save-client", "n_clicks"),
    State("client-form-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_client_form(open_n, cancel_n, save_n, is_open):
    trigger = ctx.triggered_id
    if trigger == "btn-toggle-client-form":
        return not is_open
    return False


# Toggle deal form
@callback(
    Output("deal-form-collapse", "is_open"),
    Output("crm-deal-client", "options"),
    Input("btn-toggle-deal-form", "n_clicks"),
    Input("btn-cancel-deal", "n_clicks"),
    Input("btn-save-deal", "n_clicks"),
    State("deal-form-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_deal_form(open_n, cancel_n, save_n, is_open):
    trigger = ctx.triggered_id
    clients = db.get_clients()
    options = [{"label": c["name"], "value": c["id"]} for c in clients]
    if trigger == "btn-toggle-deal-form":
        return not is_open, options
    return False, options


# Save client
@callback(
    Output("client-form-status", "children"),
    Output("crm-refresh", "data", allow_duplicate=True),
    Output("crm-client-name", "value"),
    Output("crm-client-email", "value"),
    Output("crm-client-phone", "value"),
    Output("crm-client-company", "value"),
    Output("crm-client-notes", "value"),
    Input("btn-save-client", "n_clicks"),
    State("crm-client-name", "value"),
    State("crm-client-email", "value"),
    State("crm-client-phone", "value"),
    State("crm-client-company", "value"),
    State("crm-client-status", "value"),
    State("crm-client-notes", "value"),
    prevent_initial_call=True,
)
def create_client(n, name, email, phone, company, status, notes):
    if not n:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    if not name or not name.strip():
        return (
            html.Span("Client name is required.", style={"color": COLORS["warning"], "fontSize": "0.85rem"}),
            no_update, no_update, no_update, no_update, no_update, no_update,
        )
    db.create_client(
        name=name.strip(),
        email=(email or "").strip(),
        phone=(phone or "").strip(),
        company=(company or "").strip(),
        status=status or "active",
        notes=(notes or "").strip(),
    )
    return (
        html.Span(f"Client '{name.strip()}' created.", style={"color": COLORS["success"], "fontSize": "0.85rem"}),
        datetime.now().timestamp(), "", "", "", "", "",
    )


# Save deal
@callback(
    Output("deal-form-status", "children"),
    Output("crm-refresh", "data", allow_duplicate=True),
    Output("crm-deal-title", "value"),
    Output("crm-deal-value", "value"),
    Output("crm-deal-notes", "value"),
    Input("btn-save-deal", "n_clicks"),
    State("crm-deal-client", "value"),
    State("crm-deal-title", "value"),
    State("crm-deal-value", "value"),
    State("crm-deal-stage", "value"),
    State("crm-deal-close", "value"),
    State("crm-deal-notes", "value"),
    prevent_initial_call=True,
)
def create_deal(n, client_id, title, value, stage, expected_close, notes):
    if not n:
        return no_update, no_update, no_update, no_update, no_update
    if not client_id or not title or not title.strip():
        return (
            html.Span("Client and deal title are required.", style={"color": COLORS["warning"], "fontSize": "0.85rem"}),
            no_update, no_update, no_update, no_update,
        )
    try:
        value = float(value or 0)
    except (ValueError, TypeError):
        return (
            html.Span("Invalid value.", style={"color": COLORS["danger"], "fontSize": "0.85rem"}),
            no_update, no_update, no_update, no_update,
        )
    db.create_deal(
        client_id=client_id,
        title=title.strip(),
        value=value,
        stage=stage or "prospect",
        expected_close=expected_close or None,
        notes=(notes or "").strip(),
    )
    return (
        html.Span(f"Deal '{title.strip()}' created.", style={"color": COLORS["success"], "fontSize": "0.85rem"}),
        datetime.now().timestamp(), "", None, "",
    )


# KPIs
@callback(
    Output("crm-kpi-row", "children"),
    Input("crm-refresh", "data"),
)
def render_kpis(_):
    s = db.get_crm_summary()
    return [
        _kpi("Total Clients", str(s["total_clients"]), color=COLORS["text_primary"]),
        _kpi("Active Deals", str(s["active_deals"]), "in pipeline", COLORS["info"]),
        _kpi("Pipeline Value", f"${s['pipeline_value']:,.0f}", "open deals", COLORS["warning"]),
        _kpi("Won Revenue", f"${s['won_value']:,.0f}", "closed won", COLORS["success"]),
    ]


# Client filter
@callback(
    Output("crm-client-filter", "data"),
    Input("crm-filter-all", "n_clicks"),
    Input("crm-filter-active", "n_clicks"),
    Input("crm-filter-prospect", "n_clicks"),
    Input("crm-filter-inactive", "n_clicks"),
    prevent_initial_call=True,
)
def set_client_filter(*_):
    tid = ctx.triggered_id
    if tid == "crm-filter-active":
        return "active"
    elif tid == "crm-filter-prospect":
        return "prospect"
    elif tid == "crm-filter-inactive":
        return "inactive"
    return "all"


# Render client list
@callback(
    Output("crm-client-list", "children"),
    Input("crm-refresh", "data"),
    Input("crm-client-filter", "data"),
)
def render_clients(_, active_filter):
    status_filter = None if active_filter == "all" else active_filter
    clients = db.get_clients(status=status_filter)

    if not clients:
        return html.P("No clients found.", style={
            "color": COLORS["text_muted"], "fontSize": "0.9rem", "textAlign": "center", "padding": "24px",
        })

    # Get deal stats per client
    all_deals = db.get_deals()
    client_deals = {}
    for d in all_deals:
        cid = d["client_id"]
        if cid not in client_deals:
            client_deals[cid] = {"count": 0, "total_value": 0}
        client_deals[cid]["count"] += 1
        client_deals[cid]["total_value"] += d["value"]

    items = []
    for c in clients:
        status_color = STATUS_COLORS.get(c["status"], COLORS["text_muted"])
        deals_info = client_deals.get(c["id"], {"count": 0, "total_value": 0})

        items.append(
            html.Div(style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "12px 0", "borderBottom": f"1px solid {COLORS['border']}",
            }, children=[
                html.Div(children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "2px"}, children=[
                        html.Span(c["status"].upper(), style={
                            "background": status_color, "color": "#fff", "padding": "2px 8px",
                            "borderRadius": "4px", "fontSize": "0.6rem", "fontWeight": "700",
                        }),
                        html.Span(c["name"], style={
                            "color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600",
                        }),
                        html.Span(f"({c['company']})" if c.get("company") else "", style={
                            "color": COLORS["text_muted"], "fontSize": "0.8rem",
                        }),
                    ]),
                    html.Div(style={"display": "flex", "gap": "12px"}, children=[
                        html.Span(c["email"], style={"color": COLORS["text_muted"], "fontSize": "0.75rem"}) if c.get("email") else None,
                        html.Span(f"{deals_info['count']} deals — ${deals_info['total_value']:,.0f}", style={
                            "color": COLORS["accent"], "fontSize": "0.75rem",
                        }) if deals_info["count"] > 0 else html.Span("No deals", style={
                            "color": COLORS["text_muted"], "fontSize": "0.75rem",
                        }),
                    ]),
                ]),
                html.Div(style={"display": "flex", "gap": "6px"}, children=[
                    dbc.Button("Delete", id={"type": "crm-delete-client", "index": c["id"]},
                               size="sm", outline=True, color="danger", style={"fontSize": "0.7rem"}),
                ]),
            ])
        )
    return html.Div(items)


# Client actions (delete)
@callback(
    Output("crm-refresh", "data", allow_duplicate=True),
    Input({"type": "crm-delete-client", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def client_actions(n_clicks_list):
    if not ctx.triggered_id or not any(n for n in n_clicks_list if n):
        return no_update
    client_id = ctx.triggered_id["index"]
    db.delete_client(client_id)
    return datetime.now().timestamp()


# Render deal pipeline
@callback(
    Output("crm-deal-pipeline", "children"),
    Input("crm-refresh", "data"),
)
def render_deals(_):
    deals = db.get_deals()

    if not deals:
        return html.P("No deals in pipeline.", style={
            "color": COLORS["text_muted"], "fontSize": "0.9rem", "textAlign": "center", "padding": "24px",
        })

    # Group by stage
    grouped = {s: [] for s in STAGE_ORDER}
    for d in deals:
        grouped.setdefault(d["stage"], []).append(d)

    sections = []
    for stage in STAGE_ORDER:
        stage_deals = grouped.get(stage, [])
        if not stage_deals:
            continue
        stage_color = STAGE_COLORS.get(stage, COLORS["text_muted"])
        total = sum(d["value"] for d in stage_deals)

        sections.append(
            html.Div(style={"marginBottom": "16px"}, children=[
                html.Div(style={
                    "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                    "marginBottom": "8px",
                }, children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                        html.Span(stage.upper(), style={
                            "background": stage_color, "color": "#fff", "padding": "2px 10px",
                            "borderRadius": "4px", "fontSize": "0.65rem", "fontWeight": "700",
                        }),
                        html.Span(f"{len(stage_deals)} deal{'s' if len(stage_deals) != 1 else ''}", style={
                            "color": COLORS["text_muted"], "fontSize": "0.75rem",
                        }),
                    ]),
                    html.Span(f"${total:,.0f}", style={
                        "color": stage_color, "fontSize": "0.85rem", "fontWeight": "700",
                    }),
                ]),
            ] + [
                html.Div(style={
                    "padding": "10px 12px", "borderLeft": f"3px solid {stage_color}",
                    "background": COLORS["body_bg"], "borderRadius": "6px", "marginBottom": "6px",
                }, children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
                        html.Div(children=[
                            html.Span(d["title"], style={
                                "color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "600",
                            }),
                            html.Span(f" — {d['client_name']}", style={
                                "color": COLORS["text_muted"], "fontSize": "0.8rem",
                            }),
                        ]),
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                            html.Span(f"${d['value']:,.0f}", style={
                                "color": COLORS["text_primary"], "fontSize": "0.85rem", "fontWeight": "700",
                            }),
                            dbc.Button("Del", id={"type": "crm-delete-deal", "index": d["id"]},
                                       size="sm", outline=True, color="danger", style={"fontSize": "0.65rem", "padding": "2px 6px"}),
                        ]),
                    ]),
                    html.Div(style={"marginTop": "4px"}, children=[
                        html.Span(f"Close: {d['expected_close']}", style={
                            "color": COLORS["text_muted"], "fontSize": "0.7rem",
                        }) if d.get("expected_close") else None,
                    ]) if d.get("expected_close") else None,
                ])
                for d in stage_deals
            ]),
        )
    return html.Div(sections)


# Deal actions (delete)
@callback(
    Output("crm-refresh", "data", allow_duplicate=True),
    Input({"type": "crm-delete-deal", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def deal_actions(n_clicks_list):
    if not ctx.triggered_id or not any(n for n in n_clicks_list if n):
        return no_update
    deal_id = ctx.triggered_id["index"]
    db.delete_deal(deal_id)
    return datetime.now().timestamp()
