import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages import sepa, home, market, vpa


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
)
app.title = "SignalFinder"
server = app.server


_NAV_LINKS = [
    ("\ud648",            "/",                 "#6366f1"),
    ("\uad6d\ub0b4\uc8fc\uc2dd", "/market/domestic",  "#fb923c"),
    ("\ud574\uc678\uc8fc\uc2dd", "/market/overseas",  "#60a5fa"),
    ("SEPA \uc804\ub7b5", "/sepa",             "#6366f1"),
    ("VPA \uc804\ub7b5",  "/vpa",              "#34d399"),
]


def _nav_link(label, href, active=False, accent="#6366f1"):
    if active:
        style = {
            "display": "block", "padding": "9px 14px",
            "borderRadius": "8px", "color": accent,
            "fontWeight": "700", "fontSize": "13px",
            "textDecoration": "none", "marginBottom": "2px",
            "backgroundColor": f"{accent}18",
            "borderLeft": f"3px solid {accent}",
        }
    else:
        style = {
            "display": "block", "padding": "9px 14px",
            "borderRadius": "8px", "color": "#94a3b8",
            "fontWeight": "600", "fontSize": "13px",
            "textDecoration": "none", "marginBottom": "2px",
            "backgroundColor": "#0d1117",
        }
    return html.A(label, href=href, style=style)


def _nav_section(title):
    return html.Div(title, style={
        "color": "#374151", "fontSize": "10px", "fontWeight": "700",
        "letterSpacing": "1px", "padding": "16px 14px 6px",
        "textTransform": "uppercase",
    })


def _build_sidebar(pathname):
    return [
        html.A([
            html.Span("SF", style={
                "background": "linear-gradient(135deg, #6366f1, #8b5cf6)",
                "color": "white", "borderRadius": "8px",
                "padding": "4px 10px", "fontWeight": "800",
                "fontSize": "18px", "marginRight": "8px",
            }),
            html.Span("SignalFinder", style={
                "color": "white", "fontWeight": "700", "fontSize": "16px",
            }),
        ], href="/", style={"textDecoration": "none", "display": "flex",
                            "alignItems": "center", "marginBottom": "32px"}),

        _nav_link("\ud648", "/",
                  active=(pathname == "/"), accent="#6366f1"),

        _nav_section("\uc2dc\uc7a5"),
        _nav_link("\uad6d\ub0b4\uc8fc\uc2dd", "/market/domestic",
                  active=(pathname == "/market/domestic"), accent="#fb923c"),
        _nav_link("\ud574\uc678\uc8fc\uc2dd", "/market/overseas",
                  active=(pathname == "/market/overseas"), accent="#60a5fa"),

        _nav_section("\uc804\ub7b5"),
        _nav_link("SEPA \uc804\ub7b5", "/sepa",
                  active=(pathname == "/sepa"), accent="#6366f1"),
        _nav_link("VPA \uc804\ub7b5", "/vpa",
                  active=(pathname == "/vpa"), accent="#34d399"),
    ]


# ── Sidebar ────────────────────────────────────────────────
SIDEBAR = html.Div(
    id="sidebar-nav",
    className="sidebar-nav",
    style={
        "width": "200px",
        "minHeight": "100vh",
        "background": "#0d1117",
        "borderRight": "1px solid #21262d",
        "padding": "28px 12px",
        "position": "fixed",
        "top": 0, "left": 0,
        "fontFamily": "Inter, sans-serif",
    }
)


app.layout = html.Div([
    dcc.Location(id="url"),
    SIDEBAR,
    html.Div(
        id="page-content",
        style={
            "marginLeft": "200px",
            "fontFamily": "Inter, sans-serif",
            "background": "#0d1117",
            "minHeight": "100vh",
        }
    ),
    dcc.Store(id="_scroll-dummy"),
    dcc.Store(id="_vpa-scroll-dummy"),
], style={"background": "#0d1117"})


app.clientside_callback(
    """
    function(children) {
        if (children) {
            setTimeout(function() {
                var el = document.getElementById('chart-area');
                if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
            }, 150);
        }
        return null;
    }
    """,
    Output("_scroll-dummy", "data"),
    Input("chart-area", "children"),
    prevent_initial_call=True,
)

app.clientside_callback(
    """
    function(children) {
        if (children) {
            setTimeout(function() {
                var el = document.getElementById('vpa-chart-area');
                if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
            }, 150);
        }
        return null;
    }
    """,
    Output("_vpa-scroll-dummy", "data"),
    Input("vpa-chart-area", "children"),
    prevent_initial_call=True,
)


@app.callback(
    Output("page-content", "children"),
    Output("sidebar-nav", "children"),
    Input("url", "pathname"),
)
def route(pathname):
    sidebar = _build_sidebar(pathname)
    if pathname == "/sepa":
        return sepa.layout(), sidebar
    if pathname == "/market/domestic":
        return market.layout_domestic(), sidebar
    if pathname == "/market/overseas":
        return market.layout_overseas(), sidebar
    if pathname == "/vpa":
        return vpa.layout(), sidebar
    return home.layout(), sidebar




# Register chart callbacks
PATTERN_CRITERIA = {
    "Double Bottom": [
        ("B1 \u00b7 B2 (\uc774\uc911\ubc14\ub2e5)",
         "60\uc77c \ub0b4 \ub450 \uac1c\uc758 \uc800\uc810\uc774 \uc11c\ub85c 5% \uc774\ub0b4 \uac00\uaca9 \ucc28\uc774, "
         "\uc800\uc810 \uac04\uaca9\uc740 10~50\uc77c"),
        ("\ub125\ub77c\uc778",
         "\ub450 \uc800\uc810 \uc0ac\uc774\uc758 \ucd5c\uace0\uac00 \u2014 \uc774 \uc120\uc744 \uac70\ub798\ub7c9 \uc218\ubc18\uc73c\ub85c "
         "\ub3cc\ud30c\ud560 \ub54c \ub9e4\uc218 \uc2e0\ud638"),
    ],
    "Pivot Setup": [
        ("\ud53c\ubd07 \uac00\uaca9",
         "20\uc77c \uace0\uc810\uc758 98~103% \uad6c\uac04 \u2014 \uc800\ud56d\uc120 \uc9c1\uc804"),
        ("\uac70\ub798\ub7c9 \uc870\uac74",
         "\ucd5c\uadfc \uac70\ub798\ub7c9\uc774 20\uc77c \ud3c9\uade0\uc758 80% \ubbf8\ub9cc\uc73c\ub85c \uc218\ucd95 \u2014 "
         "\ub9e4\ub3c4 \uc5c6\uc774 \uc870\uc6a9\ud55c \uad6c\uac04"),
    ],
    "VCP": [
        ("\ubcc0\ub3d9\uc131 \uc218\ucd95 3\uad6c\uac04",
         "\uc8fc\uac00 \ub4f1\ub77d\ud3ed\uc744 3\uad6c\uac04\uc73c\ub85c \ub098\ub220 \uac01 \uad6c\uac04\uc774 "
         "\uc774\uc804 \uad6c\uac04\uc758 80% \ubbf8\ub9cc\uc73c\ub85c \uc904\uc5b4\ub4e0 \uac83"),
        ("\ub9c8\uc9c0\ub9c9 \uad6c\uac04",
         "\ucd5c\uc885 \ub4f1\ub77d\ud3ed 10% \ubbf8\ub9cc \u2014 \ub3cc\ud30c \uc804 \uc5d0\ub108\uc9c0 \uc751\uccd5 \uc0c1\ud0dc"),
    ],
    "Flat Base Breakout": [
        ("\ubc15\uc2a4\uad8c \uc870\uac74",
         "20\uc77c\uac04 \uc8fc\uac00 \ub4f1\ub77d\ud3ed 15% \ubbf8\ub9cc\uc73c\ub85c \ud69f\ubcf4"),
        ("\ub3cc\ud30c \uc870\uac74",
         "\ubc15\uc2a4 \uc0c1\ub2e8 \ub3cc\ud30c + \uac70\ub798\ub7c9 20\uc77c \ud3c9\uade0 \ub300\ube44 1.5\ubc30 \uc774\uc0c1"),
    ],
}


@app.callback(
    Output("chart-area", "children"),
    Input({"type": "chart-btn", "index": dash.ALL}, "n_clicks"),
    dash.State("signals-store", "data"),
    prevent_initial_call=True,
)
def show_chart(n_clicks_list, data):
    import pandas as pd
    from dash import ctx, no_update
    from components.chart_plotly import build_chart
    from pages.sepa import _reason_text

    if not any(n for n in n_clicks_list if n):
        return no_update

    idx     = ctx.triggered_id["index"]
    row     = pd.Series(data[idx])
    ticker  = str(row["ticker"]).zfill(6)
    name    = row["name"]
    pattern = row.get("pattern", "")

    fig    = build_chart(ticker, name, days=120)
    reason = _reason_text(ticker, row)

    # 첫 번째 항목(가격 요약)과 나머지 근거 항목 분리
    items = [s.strip() for s in reason.split("  |  ") if s.strip()]
    price_summary = items[0] if items else ""
    signal_items  = items[1:] if len(items) > 1 else []

    reason_blocks = [
        html.Div(price_summary, style={
            "color": "#64748b", "fontSize": "12px",
            "marginBottom": "12px", "fontFamily": "monospace",
        }),
    ] + [
        html.Div([
            html.Span("\u25cf", style={
                "color": "#6366f1", "marginRight": "10px", "fontSize": "10px",
                "flexShrink": "0", "marginTop": "4px",
            }),
            html.Span(item, style={
                "color": "#e2e8f0", "fontSize": "14px", "lineHeight": "1.6",
            }),
        ], style={
            "background": "#1e293b",
            "border": "1px solid #334155",
            "borderLeft": "3px solid #6366f1",
            "borderRadius": "6px",
            "padding": "10px 14px",
            "marginBottom": "8px",
            "display": "flex",
            "alignItems": "flex-start",
        })
        for item in signal_items
    ]

    # 패턴별 판단 기준 섹션
    criteria = PATTERN_CRITERIA.get(pattern, [])
    criteria_blocks = [
        html.Div([
            html.Div(label, style={
                "color": "#f59e0b", "fontSize": "12px",
                "fontWeight": "700", "marginBottom": "3px",
            }),
            html.Div(desc, style={
                "color": "#94a3b8", "fontSize": "12px", "lineHeight": "1.7",
            }),
        ], style={
            "background": "#1c1a0f",
            "border": "1px solid #2d2a10",
            "borderLeft": "3px solid #f59e0b",
            "borderRadius": "6px",
            "padding": "10px 14px",
            "marginBottom": "8px",
        })
        for label, desc in criteria
    ]

    criteria_section = html.Div([
        html.Div("\ud310\ub2e8 \uae30\uc900", style={
            "color": "#f59e0b", "fontSize": "12px", "fontWeight": "700",
            "letterSpacing": "1px", "marginBottom": "12px",
            "marginTop": "20px",
        }),
        *criteria_blocks,
    ]) if criteria_blocks else html.Div()

    return html.Div([
        html.Hr(style={"borderColor": "#21262d", "marginTop": "32px"}),
        html.H5(f"{name}  ({ticker})",
                style={"color": "white", "marginBottom": "16px"}),
        dcc.Graph(figure=fig, config={"displayModeBar": True,
                                      "modeBarButtonsToRemove": ["lasso2d", "select2d"]}),
        html.Div([
            html.Div("\uc120\uc815 \uadfc\uac70", style={
                "color": "#6366f1", "fontSize": "12px", "fontWeight": "700",
                "letterSpacing": "1px", "marginBottom": "12px",
            }),
            *reason_blocks,
            criteria_section,
        ], style={
            "background": "#0f172a",
            "border": "1px solid #1e293b",
            "borderRadius": "10px",
            "padding": "18px 20px",
            "marginTop": "16px",
        }),
    ])


@app.callback(
    Output("vpa-chart-area", "children"),
    dash.Input({"type": "vpa-chart-btn", "index": dash.ALL}, "n_clicks"),
    dash.State("vpa-signals-store", "data"),
    prevent_initial_call=True,
)
def show_vpa_chart(n_clicks_list, data):
    import pandas as pd
    from dash import ctx, no_update
    from components.chart_plotly import build_chart
    from pages.vpa import _vpa_reason_text, VPA_COLORS, VPA_KO

    if not any(n for n in n_clicks_list if n):
        return no_update

    idx     = ctx.triggered_id["index"]
    row     = pd.Series(data[idx])
    ticker  = str(row["ticker"]).zfill(6)
    name    = row["name"]
    pattern = row.get("pattern", "")
    color   = VPA_COLORS.get(pattern, "#888")

    fig    = build_chart(ticker, name, days=120)
    reason = _vpa_reason_text(row)

    items = [s.strip() for s in reason.split("  |  ") if s.strip()]
    price_summary = items[0] if items else ""
    signal_items  = items[1:] if len(items) > 1 else []

    reason_blocks = [
        html.Div(price_summary, style={
            "color": "#64748b", "fontSize": "12px",
            "marginBottom": "12px", "fontFamily": "monospace",
        }),
    ] + [
        html.Div([
            html.Span("\u25cf", style={
                "color": color, "marginRight": "10px", "fontSize": "10px",
                "flexShrink": "0", "marginTop": "4px",
            }),
            html.Span(item, style={
                "color": "#e2e8f0", "fontSize": "14px", "lineHeight": "1.6",
            }),
        ], style={
            "background": "#1e293b",
            "border": "1px solid #334155",
            "borderLeft": f"3px solid {color}",
            "borderRadius": "6px",
            "padding": "10px 14px",
            "marginBottom": "8px",
            "display": "flex",
            "alignItems": "flex-start",
        })
        for item in signal_items
    ]

    return html.Div([
        html.Hr(style={"borderColor": "#21262d", "marginTop": "32px"}),
        html.H5(f"{name}  ({ticker})",
                style={"color": "white", "marginBottom": "16px"}),
        dcc.Graph(figure=fig, config={"displayModeBar": True,
                                      "modeBarButtonsToRemove": ["lasso2d", "select2d"]}),
        html.Div([
            html.Div(VPA_KO.get(pattern, pattern), style={
                "color": color, "fontSize": "12px", "fontWeight": "700",
                "letterSpacing": "1px", "marginBottom": "12px",
            }),
            *reason_blocks,
        ], style={
            "background": "#0f172a",
            "border": "1px solid #1e293b",
            "borderRadius": "10px",
            "padding": "18px 20px",
            "marginTop": "16px",
        }),
    ])


if __name__ == "__main__":
    app.run(debug=False, port=8060)
