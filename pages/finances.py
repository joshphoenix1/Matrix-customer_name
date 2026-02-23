"""
Finances page — revenue tracking, projections, outstanding invoices.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from datetime import date, datetime
from config import COLORS
import db

dash.register_page(__name__, path="/finances", name="Finances", order=8)

STATUS_COLORS = {
    "overdue": COLORS["danger"],
    "pending": COLORS["warning"],
    "paid": COLORS["success"],
}


def _kpi(label, value, subtitle=None, color=COLORS["text_primary"]):
    children = [
        html.P(
            label,
            style={
                "color": COLORS["text_muted"],
                "fontSize": "0.7rem",
                "margin": "0 0 4px 0",
                "textTransform": "uppercase",
                "letterSpacing": "1px",
            },
        ),
        html.P(
            value,
            style={
                "color": color,
                "fontSize": "1.5rem",
                "margin": 0,
                "fontWeight": "800",
            },
        ),
    ]
    if subtitle:
        children.append(
            html.P(
                subtitle,
                style={"color": COLORS["text_muted"], "fontSize": "0.7rem", "margin": "2px 0 0 0"},
            )
        )
    return html.Div(
        style={
            "textAlign": "center",
            "padding": "16px",
            "background": COLORS["card_bg"],
            "borderRadius": "12px",
            "flex": "1",
            "minWidth": "160px",
        },
        children=children,
    )


# ── Layout ──

layout = html.Div(
    children=[
        dcc.Store(id="finances-refresh", data=0),
        # Header
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div(
                    children=[
                        html.H2("Finances", style={"color": COLORS["text_primary"], "margin": 0}),
                        html.P(
                            "Track revenue, invoices, and financial projections.",
                            style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "margin": "4px 0 0 0"},
                        ),
                    ]
                ),
            ],
        ),
        # KPI row
        html.Div(
            id="finances-kpi-row",
            style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"},
        ),
        # Main grid
        dbc.Row(
            [
                # Left column: Revenue + Add Revenue
                dbc.Col(
                    [
                        # Add Revenue Entry
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['success']}",
                            },
                            children=[
                                html.H4(
                                    [html.I(className="bi bi-plus-circle", style={"marginRight": "10px"}), "Log Revenue"],
                                    style={"color": COLORS["text_primary"], "marginBottom": "16px", "fontSize": "1rem"},
                                ),
                                dbc.Input(id="rev-source", placeholder="Client / source name", className="mb-2",
                                          style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                dbc.Input(id="rev-amount", placeholder="Amount ($)", type="number", className="mb-2",
                                          style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                html.Div(
                                    style={"display": "flex", "gap": "8px", "marginBottom": "8px"},
                                    children=[
                                        dcc.Dropdown(
                                            id="rev-type",
                                            options=[{"label": "Recurring (MRR)", "value": "recurring"}, {"label": "One-time", "value": "one-time"}],
                                            value="recurring",
                                            placeholder="Type",
                                            style={"flex": "1"},
                                        ),
                                        dbc.Input(id="rev-period", placeholder="Period (e.g. Feb 2026)", value="",
                                                  style={"flex": "1", "background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                    ],
                                ),
                                dbc.Input(id="rev-date", type="date", value=date.today().isoformat(), className="mb-2",
                                          style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                dbc.Textarea(id="rev-notes", placeholder="Notes (optional)", className="mb-2",
                                             style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px", "minHeight": "60px"}),
                                dbc.Button(
                                    [html.I(className="bi bi-plus-lg", style={"marginRight": "6px"}), "Add Revenue"],
                                    id="rev-add-btn",
                                    color="success",
                                    size="sm",
                                    style={"background": COLORS["success"], "border": "none"},
                                ),
                                html.Div(id="rev-add-status", style={"marginTop": "8px"}),
                            ],
                        ),
                        # Revenue History
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['accent']}",
                            },
                            children=[
                                html.H4(
                                    [html.I(className="bi bi-graph-up-arrow", style={"marginRight": "10px"}), "Revenue History"],
                                    style={"color": COLORS["text_primary"], "marginBottom": "16px", "fontSize": "1rem"},
                                ),
                                html.Div(id="revenue-list"),
                            ],
                        ),
                    ],
                    md=6,
                ),
                # Right column: Invoices + Add Invoice
                dbc.Col(
                    [
                        # Add Invoice
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['warning']}",
                            },
                            children=[
                                html.H4(
                                    [html.I(className="bi bi-receipt", style={"marginRight": "10px"}), "New Invoice"],
                                    style={"color": COLORS["text_primary"], "marginBottom": "16px", "fontSize": "1rem"},
                                ),
                                dbc.Input(id="inv-client", placeholder="Client name", className="mb-2",
                                          style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                dbc.Input(id="inv-amount", placeholder="Amount ($)", type="number", className="mb-2",
                                          style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                dbc.Input(id="inv-due", type="date", value="", className="mb-2",
                                          style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px"}),
                                dbc.Textarea(id="inv-desc", placeholder="Description (optional)", className="mb-2",
                                             style={"background": COLORS["body_bg"], "border": f"1px solid {COLORS['border']}", "color": COLORS["text_primary"], "borderRadius": "8px", "minHeight": "60px"}),
                                dbc.Button(
                                    [html.I(className="bi bi-plus-lg", style={"marginRight": "6px"}), "Create Invoice"],
                                    id="inv-add-btn",
                                    color="warning",
                                    size="sm",
                                ),
                                html.Div(id="inv-add-status", style={"marginTop": "8px"}),
                            ],
                        ),
                        # Outstanding Invoices
                        html.Div(
                            style={
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "padding": "24px",
                                "marginBottom": "16px",
                                "borderLeft": f"4px solid {COLORS['danger']}",
                            },
                            children=[
                                html.Div(
                                    style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"},
                                    children=[
                                        html.H4(
                                            [html.I(className="bi bi-exclamation-triangle", style={"marginRight": "10px"}), "Invoices"],
                                            style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1rem"},
                                        ),
                                        html.Div(
                                            style={"display": "flex", "gap": "6px"},
                                            children=[
                                                dbc.Button("All", id="inv-filter-all", size="sm", outline=True, color="light", style={"fontSize": "0.75rem"}),
                                                dbc.Button("Outstanding", id="inv-filter-outstanding", size="sm", outline=True, color="warning", style={"fontSize": "0.75rem"}),
                                                dbc.Button("Paid", id="inv-filter-paid", size="sm", outline=True, color="success", style={"fontSize": "0.75rem"}),
                                            ],
                                        ),
                                    ],
                                ),
                                dcc.Store(id="inv-filter-store", data="all"),
                                html.Div(id="invoices-list"),
                            ],
                        ),
                    ],
                    md=6,
                ),
            ],
        ),
    ]
)


# ── Callbacks ──

@callback(
    Output("finances-kpi-row", "children"),
    Input("finances-refresh", "data"),
)
def update_kpis(_):
    rev = db.get_revenue_summary()
    inv = db.get_invoices_summary()

    return [
        _kpi("Total Revenue", f"${rev['total_revenue']:,.0f}", f"{rev['entry_count']} entries logged", COLORS["success"]),
        _kpi("Monthly Recurring (MRR)", f"${rev['mrr']:,.0f}", "recurring clients", COLORS["accent"]),
        _kpi("Outstanding Invoices", f"${inv['total_outstanding']:,.0f}", f"{inv['count']} unpaid", COLORS["warning"]),
        _kpi("Overdue", f"${inv['total_overdue']:,.0f}", "needs attention", COLORS["danger"]),
    ]


# ── Add Revenue ──

@callback(
    Output("rev-add-status", "children"),
    Output("finances-refresh", "data", allow_duplicate=True),
    Output("rev-source", "value"),
    Output("rev-amount", "value"),
    Output("rev-notes", "value"),
    Input("rev-add-btn", "n_clicks"),
    State("rev-source", "value"),
    State("rev-amount", "value"),
    State("rev-type", "value"),
    State("rev-period", "value"),
    State("rev-date", "value"),
    State("rev-notes", "value"),
    prevent_initial_call=True,
)
def add_revenue(n, source, amount, entry_type, period, entry_date, notes):
    if not n:
        return no_update, no_update, no_update, no_update, no_update
    if not source or not amount:
        return html.Span("Source and amount are required.", style={"color": COLORS["warning"], "fontSize": "0.85rem"}), no_update, no_update, no_update, no_update

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return html.Span("Invalid amount.", style={"color": COLORS["danger"], "fontSize": "0.85rem"}), no_update, no_update, no_update, no_update

    db.create_revenue_entry(source, amount, entry_type or "one-time", period or "", entry_date, notes or "")

    return (
        html.Span(f"${amount:,.0f} from {source} logged.", style={"color": COLORS["success"], "fontSize": "0.85rem"}),
        n,
        "",
        None,
        "",
    )


# ── Add Invoice ──

@callback(
    Output("inv-add-status", "children"),
    Output("finances-refresh", "data", allow_duplicate=True),
    Output("inv-client", "value"),
    Output("inv-amount", "value"),
    Output("inv-desc", "value"),
    Input("inv-add-btn", "n_clicks"),
    State("inv-client", "value"),
    State("inv-amount", "value"),
    State("inv-due", "value"),
    State("inv-desc", "value"),
    prevent_initial_call=True,
)
def add_invoice(n, client, amount, due_date, description):
    if not n:
        return no_update, no_update, no_update, no_update, no_update
    if not client or not amount:
        return html.Span("Client and amount are required.", style={"color": COLORS["warning"], "fontSize": "0.85rem"}), no_update, no_update, no_update, no_update

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return html.Span("Invalid amount.", style={"color": COLORS["danger"], "fontSize": "0.85rem"}), no_update, no_update, no_update, no_update

    db.create_invoice(client, amount, due_date or None, description or "")

    return (
        html.Span(f"Invoice for {client} — ${amount:,.0f} created.", style={"color": COLORS["success"], "fontSize": "0.85rem"}),
        n,
        "",
        None,
        "",
    )


# ── Invoice filter ──

@callback(
    Output("inv-filter-store", "data"),
    Input("inv-filter-all", "n_clicks"),
    Input("inv-filter-outstanding", "n_clicks"),
    Input("inv-filter-paid", "n_clicks"),
    prevent_initial_call=True,
)
def set_inv_filter(*_):
    tid = ctx.triggered_id
    if tid == "inv-filter-outstanding":
        return "outstanding"
    elif tid == "inv-filter-paid":
        return "paid"
    return "all"


# ── Render Invoices ──

@callback(
    Output("invoices-list", "children"),
    Input("finances-refresh", "data"),
    Input("inv-filter-store", "data"),
)
def render_invoices(_, active_filter):
    invoices = db.get_invoices()

    # Auto-mark overdue
    today = date.today().isoformat()
    for inv in invoices:
        if inv["status"] == "pending" and inv.get("due_date") and inv["due_date"] < today:
            db.update_invoice(inv["id"], status="overdue")
            inv["status"] = "overdue"

    # Filter
    if active_filter == "outstanding":
        invoices = [i for i in invoices if i["status"] != "paid"]
    elif active_filter == "paid":
        invoices = [i for i in invoices if i["status"] == "paid"]

    if not invoices:
        return html.P("No invoices found.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "textAlign": "center", "padding": "24px"})

    items = []
    for inv in invoices:
        status = inv["status"]
        status_color = STATUS_COLORS.get(status, COLORS["text_muted"])

        action_btn = []
        if status != "paid":
            action_btn.append(
                dbc.Button(
                    "Mark Paid",
                    id={"type": "inv-mark-paid", "index": inv["id"]},
                    size="sm",
                    color="success",
                    outline=True,
                    style={"fontSize": "0.7rem"},
                )
            )

        items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "12px 0",
                    "borderBottom": f"1px solid {COLORS['border']}",
                },
                children=[
                    html.Div(
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "2px"},
                                children=[
                                    html.Span(
                                        status.upper(),
                                        style={
                                            "background": status_color,
                                            "color": "#fff",
                                            "padding": "2px 8px",
                                            "borderRadius": "4px",
                                            "fontSize": "0.6rem",
                                            "fontWeight": "700",
                                        },
                                    ),
                                    html.Span(inv["client"], style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600"}),
                                ],
                            ),
                            html.Span(
                                f"Due: {inv.get('due_date', 'N/A')}" + (f" — {inv['description']}" if inv.get("description") else ""),
                                style={"color": COLORS["text_muted"], "fontSize": "0.75rem"},
                            ),
                        ]
                    ),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px"},
                        children=[
                            html.Span(f"${inv['amount']:,.0f}", style={"color": COLORS["text_primary"], "fontSize": "1rem", "fontWeight": "700"}),
                        ] + action_btn,
                    ),
                ],
            )
        )
    return html.Div(items)


# ── Mark Invoice Paid ──

@callback(
    Output("finances-refresh", "data", allow_duplicate=True),
    Input({"type": "inv-mark-paid", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def mark_paid(n_clicks_list):
    if not ctx.triggered_id or not any(n_clicks_list):
        return no_update
    invoice_id = ctx.triggered_id["index"]
    db.update_invoice(invoice_id, status="paid")
    return datetime.now().timestamp()


# ── Render Revenue History ──

@callback(
    Output("revenue-list", "children"),
    Input("finances-refresh", "data"),
)
def render_revenue(_):
    entries = db.get_revenue_entries(limit=30)

    if not entries:
        return html.P("No revenue entries yet.", style={"color": COLORS["text_muted"], "fontSize": "0.9rem", "textAlign": "center", "padding": "24px"})

    items = []
    for e in entries:
        type_color = COLORS["accent"] if e["entry_type"] == "recurring" else COLORS["info"]
        type_label = "MRR" if e["entry_type"] == "recurring" else "ONE-TIME"

        items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "10px 0",
                    "borderBottom": f"1px solid {COLORS['border']}",
                },
                children=[
                    html.Div(
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "2px"},
                                children=[
                                    html.Span(
                                        type_label,
                                        style={
                                            "background": type_color,
                                            "color": "#fff",
                                            "padding": "2px 8px",
                                            "borderRadius": "4px",
                                            "fontSize": "0.6rem",
                                            "fontWeight": "700",
                                        },
                                    ),
                                    html.Span(e["source"], style={"color": COLORS["text_primary"], "fontSize": "0.9rem", "fontWeight": "600"}),
                                ],
                            ),
                            html.Span(
                                e.get("entry_date", "") + (f" — {e['period']}" if e.get("period") else "") + (f" — {e['notes']}" if e.get("notes") else ""),
                                style={"color": COLORS["text_muted"], "fontSize": "0.75rem"},
                            ),
                        ]
                    ),
                    html.Span(
                        f"${e['amount']:,.0f}",
                        style={"color": COLORS["success"], "fontSize": "1rem", "fontWeight": "700"},
                    ),
                ],
            )
        )
    return html.Div(items)
