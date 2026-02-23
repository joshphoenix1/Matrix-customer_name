"""
Chat page — Matrix AI Assistant conversation interface.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from config import COLORS, COMPANY_NAME
import db
from services.claude_client import chat as claude_chat

dash.register_page(__name__, path="/chat", name="Chat", order=2)

# ── Layout ──

layout = html.Div(
    style={"padding": "0"},
    children=[
        dcc.Store(id="chat-conversation-id", storage_type="session"),
        dcc.Store(id="chat-loading-state", data=False),

        html.Div(
            style={"display": "flex", "height": "calc(100vh - 40px)"},
            children=[
                # Conversation sidebar
                html.Div(
                    style={
                        "width": "240px",
                        "minWidth": "240px",
                        "background": COLORS["sidebar_bg"],
                        "borderRight": f"1px solid {COLORS['border']}",
                        "padding": "16px",
                        "overflowY": "auto",
                        "display": "flex",
                        "flexDirection": "column",
                    },
                    children=[
                        dbc.Button(
                            [html.I(className="bi bi-plus-lg", style={"marginRight": "8px"}), "New Chat"],
                            id="btn-new-chat",
                            color="primary",
                            size="sm",
                            className="mb-2",
                            style={"width": "100%", "background": COLORS["accent"], "border": "none"},
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-trash3", style={"marginRight": "8px"}), "Delete History"],
                            id="btn-delete-history",
                            color="danger",
                            size="sm",
                            outline=True,
                            className="mb-3",
                            style={"width": "100%", "fontSize": "0.8rem"},
                        ),
                        html.Div(id="conversation-list"),
                    ],
                ),
                # Chat area
                html.Div(
                    style={"flex": "1", "display": "flex", "flexDirection": "column", "padding": "20px"},
                    children=[
                        html.Div(
                            style={"marginBottom": "16px"},
                            children=[
                                html.H2(
                                    f"{COMPANY_NAME} Matrix AI Assistant",
                                    style={"color": COLORS["text_primary"], "margin": 0, "fontSize": "1.3rem"},
                                ),
                                html.P(
                                    "Your AI executive assistant — powered by strategic frameworks from the world's top CEOs.",
                                    style={"color": COLORS["text_muted"], "fontSize": "0.85rem", "margin": "4px 0 0 0"},
                                ),
                            ],
                        ),
                        # Messages display
                        html.Div(
                            id="chat-messages-container",
                            style={
                                "flex": "1",
                                "overflowY": "auto",
                                "padding": "16px",
                                "background": COLORS["card_bg"],
                                "borderRadius": "12px",
                                "marginBottom": "16px",
                            },
                        ),
                        # Loading indicator
                        html.Div(
                            id="chat-typing-indicator",
                            style={"display": "none", "marginBottom": "8px"},
                            children=[
                                dbc.Spinner(size="sm", color="light", spinner_style={"marginRight": "8px"}),
                                html.Span("Matrix AI Assistant is thinking...", style={"color": COLORS["text_muted"], "fontSize": "0.85rem"}),
                            ],
                        ),
                        # Input area
                        html.Div(
                            style={"display": "flex", "gap": "8px"},
                            children=[
                                dbc.Input(
                                    id="chat-input",
                                    placeholder="Ask your Matrix AI Assistant anything...",
                                    type="text",
                                    style={
                                        "flex": "1",
                                        "background": COLORS["card_bg"],
                                        "border": f"1px solid {COLORS['border']}",
                                        "color": COLORS["text_primary"],
                                        "borderRadius": "8px",
                                    },
                                    debounce=False,
                                ),
                                dbc.Button(
                                    html.I(className="bi bi-send-fill"),
                                    id="btn-send-chat",
                                    color="primary",
                                    style={"background": COLORS["accent"], "border": "none", "borderRadius": "8px"},
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ── Helpers ──

def _render_message(role, content):
    is_user = role == "user"
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "flex-end" if is_user else "flex-start",
            "marginBottom": "12px",
        },
        children=[
            html.Div(
                style={
                    "maxWidth": "75%",
                    "padding": "12px 16px",
                    "borderRadius": "12px",
                    "background": COLORS["accent"] if is_user else "#2D2D44",
                    "color": COLORS["text_primary"],
                    "fontSize": "0.9rem",
                    "lineHeight": "1.6",
                    "whiteSpace": "pre-wrap",
                },
                children=[dcc.Markdown(content, style={"margin": 0, "color": COLORS["text_primary"]})],
            ),
        ],
    )


def _render_conversation_list():
    convos = db.get_conversations()
    if not convos:
        return html.P(
            "No conversations yet.",
            style={"color": COLORS["text_muted"], "fontSize": "0.8rem"},
        )
    items = []
    for c in convos[:20]:
        items.append(
            html.Div(
                c["title"],
                id={"type": "conv-item", "index": c["id"]},
                n_clicks=0,
                className="conversation-item",
                style={
                    "padding": "8px 12px",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "color": COLORS["text_secondary"],
                    "fontSize": "0.85rem",
                    "marginBottom": "4px",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                },
            )
        )
    return html.Div(items)


# ── Callbacks ──

@callback(
    Output("chat-conversation-id", "data"),
    Output("conversation-list", "children", allow_duplicate=True),
    Input("btn-new-chat", "n_clicks"),
    prevent_initial_call=True,
)
def new_conversation(n):
    if not n:
        return no_update, no_update
    conv_id = db.create_conversation()
    return conv_id, _render_conversation_list()


@callback(
    Output("chat-conversation-id", "data", allow_duplicate=True),
    Input({"type": "conv-item", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def select_conversation(n_clicks):
    if not ctx.triggered_id or not any(n_clicks):
        return no_update
    return ctx.triggered_id["index"]


@callback(
    Output("conversation-list", "children"),
    Input("chat-conversation-id", "data"),
)
def refresh_conversation_list(_):
    return _render_conversation_list()


@callback(
    Output("chat-messages-container", "children"),
    Input("chat-conversation-id", "data"),
)
def load_messages(conv_id):
    if not conv_id:
        return html.Div(
            style={"textAlign": "center", "padding": "60px 20px"},
            children=[
                html.H3("Start a conversation", style={"color": COLORS["text_muted"], "fontWeight": "400"}),
                html.P(
                    "Click 'New Chat' to begin talking with your Matrix AI Assistant.",
                    style={"color": COLORS["text_muted"], "fontSize": "0.9rem"},
                ),
            ],
        )
    messages = db.get_messages(conv_id)
    if not messages:
        return html.Div(
            style={"textAlign": "center", "padding": "60px 20px"},
            children=[
                html.P(
                    "What would you like to discuss?",
                    style={"color": COLORS["text_muted"], "fontSize": "0.95rem"},
                ),
            ],
        )
    return html.Div([_render_message(m["role"], m["content"]) for m in messages])


@callback(
    Output("chat-messages-container", "children", allow_duplicate=True),
    Output("chat-input", "value"),
    Output("conversation-list", "children", allow_duplicate=True),
    Output("chat-typing-indicator", "style"),
    Input("btn-send-chat", "n_clicks"),
    Input("chat-input", "n_submit"),
    State("chat-input", "value"),
    State("chat-conversation-id", "data"),
    prevent_initial_call=True,
)
def send_message(n_clicks, n_submit, message, conv_id):
    if not message or not message.strip():
        return no_update, no_update, no_update, no_update

    if not conv_id:
        conv_id = db.create_conversation()

    # Get Claude response (synchronous for V1)
    response = claude_chat(message.strip(), conv_id)

    # Reload messages
    messages = db.get_messages(conv_id)
    rendered = html.Div([_render_message(m["role"], m["content"]) for m in messages])

    return rendered, "", _render_conversation_list(), {"display": "none"}


@callback(
    Output("chat-conversation-id", "data", allow_duplicate=True),
    Output("conversation-list", "children", allow_duplicate=True),
    Output("chat-messages-container", "children", allow_duplicate=True),
    Input("btn-delete-history", "n_clicks"),
    prevent_initial_call=True,
)
def delete_all_history(n):
    if not n:
        return no_update, no_update, no_update
    with db.get_db() as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM conversations")
    return None, _render_conversation_list(), html.Div(
        style={"textAlign": "center", "padding": "60px 20px"},
        children=[
            html.H3("Start a conversation", style={"color": COLORS["text_muted"], "fontWeight": "400"}),
            html.P(
                "Click 'New Chat' to begin talking with your Matrix AI Assistant.",
                style={"color": COLORS["text_muted"], "fontSize": "0.9rem"},
            ),
        ],
    )
