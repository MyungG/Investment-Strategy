# -*- coding: utf-8 -*-
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from kis_api import get_volume_ranking_split, get_investor_realtime, get_index_data, get_overseas_data, get_fear_greed, get_sector_data


# ── Index cards ────────────────────────────────────────────

def _sector_heatmap(sectors: list) -> html.Div:
    if not sectors:
        return html.Div()

    def _bg(rate):
        clamped = max(-3.0, min(3.0, rate))
        ratio   = abs(clamped) / 3.0
        if rate > 0:
            return f"rgb({int(15+ratio*20)},{int(50+ratio*130)},{int(15+ratio*20)})"
        elif rate < 0:
            return f"rgb({int(50+ratio*130)},{int(15+ratio*20)},{int(15+ratio*20)})"
        return "rgb(30,30,35)"

    def _stock_box(s):
        r    = s["chg_rate"]
        bg   = _bg(r)
        tc   = "#bbf7d0" if r > 0 else ("#fecaca" if r < 0 else "#94a3b8")
        sign = "+" if r > 0 else ""
        return html.Div([
            html.Div(s["ticker"], style={
                "color": "white", "fontSize": "10px", "fontWeight": "700",
                "marginBottom": "2px",
            }),
            html.Div(f"{sign}{r:.1f}%", style={
                "color": tc, "fontSize": "9px", "fontFamily": "monospace",
            }),
        ], style={
            "background": bg,
            "borderRadius": "4px",
            "padding": "5px 7px",
            "minWidth": "52px",
            "textAlign": "center",
        })

    sector_blocks = []
    for s in sectors:
        avg  = s["avg_chg"]
        tc   = "#86efac" if avg > 0 else ("#fca5a5" if avg < 0 else "#94a3b8")
        sign = "+" if avg > 0 else ""
        sector_blocks.append(html.Div([
            html.Div([
                html.Span(s["name"], style={
                    "color": "white", "fontSize": "11px", "fontWeight": "700",
                }),
                html.Span(f"  {sign}{avg:.2f}%", style={
                    "color": tc, "fontSize": "11px", "fontWeight": "600",
                    "fontFamily": "monospace",
                }),
            ], style={"marginBottom": "8px"}),
            html.Div([_stock_box(st) for st in s["stocks"]], style={
                "display": "flex", "flexWrap": "wrap", "gap": "4px",
            }),
        ], style={
            "background": "#161b22",
            "border": "1px solid #21262d",
            "borderLeft": f"3px solid {'#22c55e' if avg > 0 else ('#ef4444' if avg < 0 else '#374151')}",
            "borderRadius": "8px",
            "padding": "12px 14px",
            "marginBottom": "8px",
        }))

    return html.Div([
        html.Div("US \uc139\ud130  (GICS)", style={
            "color": "#94a3b8", "fontSize": "11px", "fontWeight": "700",
            "letterSpacing": "1px", "marginBottom": "12px",
        }),
        html.Div(sector_blocks),
    ], style={"marginBottom": "32px"})


_MACRO_NAMES = {"VIX", "DXY", "US 10Y"}
_MARKET_NAMES = {"S&P 500", "NASDAQ 100", "DOW", "Nikkei225", "USD/KRW", "WTI", "Gold"}


def _fear_greed_card(fg: dict) -> html.Div:
    if not fg:
        return html.Div()
    score = fg.get("score", 50)
    rating = fg.get("rating", "")
    prev  = fg.get("prev_close", score)
    diff  = score - prev

    # 색상 매핑
    if score <= 25:
        color, label = "#ef4444", "Extreme Fear"
    elif score <= 45:
        color, label = "#f97316", "Fear"
    elif score <= 55:
        color, label = "#eab308", "Neutral"
    elif score <= 75:
        color, label = "#84cc16", "Greed"
    else:
        color, label = "#22c55e", "Extreme Greed"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"color": color, "size": 36}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickcolor": "#374151", "tickfont": {"color": "#555", "size": 9}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#0d1117",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   25], "color": "#1a0a0a"},
                {"range": [25,  45], "color": "#1a1000"},
                {"range": [45,  55], "color": "#1a1a00"},
                {"range": [55,  75], "color": "#0a1a00"},
                {"range": [75, 100], "color": "#001a00"},
            ],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.8, "value": score},
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        margin=dict(l=20, r=20, t=10, b=10),
        height=180,
    )

    diff_color = "#22c55e" if diff >= 0 else "#ef4444"
    diff_str   = f"{diff:+.0f} \uc804\uc77c\ub300\ube44"

    return html.Div([
        html.Div([
            html.Span("Fear & Greed Index", style={
                "color": "#94a3b8", "fontSize": "11px",
                "fontWeight": "700", "letterSpacing": "1px",
            }),
            html.Span(f"  CNN", style={"color": "#374151", "fontSize": "10px"}),
        ], style={"marginBottom": "4px"}),
        dcc.Graph(figure=fig, config={"displayModeBar": False},
                  style={"marginBottom": "0px"}),
        html.Div([
            html.Span(label, style={
                "color": color, "fontSize": "16px", "fontWeight": "700",
            }),
            html.Span(f"  {diff_str}", style={
                "color": diff_color, "fontSize": "11px", "marginLeft": "10px",
            }),
        ], style={"textAlign": "center", "paddingBottom": "4px"}),
    ], style={
        "background": "#161b22",
        "border": "1px solid #21262d",
        "borderTop": f"2px solid {color}",
        "borderRadius": "10px",
        "padding": "16px 20px",
        "minWidth": "220px", "flex": "1",
    })


def _overseas_section(items: list, fg: dict = None) -> html.Div:
    if not items and not fg:
        return html.Div()

    def _card(item):
        name     = item["name"]
        close    = item["close"]
        change   = item["change"]
        chg_rate = item["chg_rate"]
        dates    = item.get("dates", [])
        closes   = item.get("closes", [])

        if change > 0:
            c, arrow = "#ff3333", "\u25b2"
        elif change < 0:
            c, arrow = "#3399ff", "\u25bc"
        else:
            c, arrow = "#94a3b8", "\u2014"

        # 포맷
        if name == "USD/KRW":
            close_fmt = f"{close:,.2f}"
        elif name in ("WTI", "Gold"):
            close_fmt = f"${close:,.2f}"
        else:
            close_fmt = f"{close:,.2f}"

        chg_fmt  = f"{change:+.2f}"
        rate_fmt = f"{chg_rate:+.2f}%"

        # 미니 라인차트
        line_color = c
        fig = go.Figure()
        if closes:
            fig.add_trace(go.Scatter(
                x=dates, y=closes,
                mode="lines",
                line=dict(color=line_color, width=1.5),
                fill="tozeroy",
                fillcolor=line_color.replace(")", ",0.08)").replace("rgb", "rgba") if "rgb" in line_color else
                          f"rgba({int(line_color[1:3],16)},{int(line_color[3:5],16)},{int(line_color[5:7],16)},0.08)",
                showlegend=False,
            ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=2, b=0), height=60,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showline=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showline=False),
            hovermode=False,
        )

        # VIX / US 10Y 해석 라벨
        interp = None
        if name == "VIX":
            if close < 15:
                interp, ic = "\uc548\uc815", "#22c55e"
            elif close < 25:
                interp, ic = "\uc8fc\uc758", "#eab308"
            elif close < 35:
                interp, ic = "\uacf5\ud3ec", "#f97316"
            else:
                interp, ic = "\ud328\ub2c9", "#ef4444"
        elif name == "US 10Y":
            close_fmt = f"{close:.2f}%"
            chg_fmt   = f"{change:+.3f}%p"
            if close < 3.5:
                interp, ic = "\uc800\uae08\ub9ac", "#22c55e"
            elif close < 4.5:
                interp, ic = "\uc911\ub9bd", "#eab308"
            else:
                interp, ic = "\uace0\uae08\ub9ac \ubd80\ub2f4", "#ef4444"

        return html.Div([
            html.Div([
                html.Span(name, style={"color": "#94a3b8", "fontSize": "11px",
                                       "fontWeight": "700", "letterSpacing": "0.5px"}),
                html.Span(f"  {interp}", style={"color": ic, "fontSize": "10px",
                                                "fontWeight": "600"}) if interp else html.Span(),
            ], style={"marginBottom": "6px"}),
            html.Div(close_fmt, style={
                "color": "white", "fontSize": "18px", "fontWeight": "700",
                "fontFamily": "monospace", "marginBottom": "2px",
            }),
            html.Div([
                html.Span(f"{arrow} {chg_fmt}", style={"color": c, "fontSize": "11px", "fontWeight": "600"}),
                html.Span(f"  ({rate_fmt})", style={"color": c, "fontSize": "11px"}),
            ], style={"marginBottom": "4px"}),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ], style={
            "background": "#161b22",
            "border": "1px solid #21262d",
            "borderRadius": "10px",
            "padding": "14px 16px",
            "flex": "1", "minWidth": "120px",
        })

    macro_items  = [i for i in items if i["name"] in _MACRO_NAMES]
    market_items = [i for i in items if i["name"] in _MARKET_NAMES]

    def _section(title, cards):
        return html.Div([
            html.Div(title, style={
                "color": "#94a3b8", "fontSize": "11px", "fontWeight": "700",
                "letterSpacing": "1px", "marginBottom": "12px",
            }),
            html.Div(cards, style={"display": "flex", "gap": "12px", "flexWrap": "wrap"}),
        ], style={"marginBottom": "28px"})

    # 매크로 행: F&G + VIX + DXY + US10Y
    macro_cards = ([_fear_greed_card(fg)] if fg else []) + [_card(i) for i in macro_items]

    return html.Div([
        _section("\ub9e4\ud06c\ub85c  \uc9c0\ud45c", macro_cards),
        _section("\uc8fc\uc694  \uc2dc\uc7a5", [_card(i) for i in market_items]),
    ])


def _index_chart(idx: dict, accent: str) -> dcc.Graph:
    dates  = idx.get("dates",  [])
    closes = idx.get("closes", [])
    opens  = idx.get("opens",  [])
    highs  = idx.get("highs",  [])
    lows   = idx.get("lows",   [])

    up_color   = "#ff3333"
    down_color = "#3399ff"

    colors = []
    for i in range(len(closes)):
        o = opens[i] if i < len(opens) else closes[i]
        colors.append(up_color if closes[i] >= o else down_color)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dates, open=opens, high=highs, low=lows, close=closes,
        increasing_line_color=up_color, decreasing_line_color=down_color,
        increasing_fillcolor=up_color, decreasing_fillcolor=down_color,
        line_width=1,
        showlegend=False,
        name="",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=4, b=0),
        height=140,
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            showline=False, rangeslider_visible=False,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#21262d", zeroline=False,
            showticklabels=True, tickfont=dict(color="#555", size=9),
            showline=False, tickformat=",.0f",
        ),
        hovermode="x unified",
    )
    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"marginTop": "12px"},
    )


def _index_cards(indices: list) -> html.Div:
    cards = []
    for idx in indices:
        name     = idx["name"]
        close    = idx["close"]
        change   = idx["change"]
        chg_rate = idx["chg_rate"]

        if change > 0:
            c, arrow = "#ff3333", "\u25b2"
        elif change < 0:
            c, arrow = "#3399ff", "\u25bc"
        else:
            c, arrow = "#94a3b8", "\u2014"

        close_fmt = f"{close:,.2f}"
        chg_fmt   = f"{change:+.2f}"
        rate_fmt  = f"{chg_rate:+.2f}%"
        accent    = "#fb923c" if name == "KOSPI" else "#e879f9"

        cards.append(html.Div([
            html.Div(name, style={
                "color": accent, "fontSize": "11px", "fontWeight": "700",
                "letterSpacing": "1.5px", "marginBottom": "10px",
            }),
            html.Div(close_fmt, style={
                "color": "white", "fontSize": "28px", "fontWeight": "700",
                "letterSpacing": "-0.5px", "marginBottom": "4px",
                "fontFamily": "monospace",
            }),
            html.Div([
                html.Span(f"{arrow} {chg_fmt}", style={"color": c, "fontWeight": "600", "fontSize": "14px"}),
                html.Span(f"  ({rate_fmt})", style={"color": c, "fontSize": "13px"}),
            ]),
            _index_chart(idx, accent),
        ], style={
            "background": "#161b22",
            "border": "1px solid #21262d",
            "borderTop": f"2px solid {accent}",
            "borderRadius": "10px",
            "padding": "20px 24px",
            "flex": "1",
        }))

    return html.Div(cards, style={
        "display": "flex", "gap": "16px", "marginBottom": "28px",
    })


# ── Row builders ───────────────────────────────────────────

def _vol_row(item: dict, rank: int) -> html.Tr:
    name   = item.get("hts_kor_isnm", "")
    ticker = item.get("mksc_shrn_iscd", "")
    price  = item.get("stck_prpr", "0")
    sign   = item.get("prdy_vrss_sign", "3")
    chg    = item.get("prdy_ctrt", "0.00")
    vol    = item.get("acml_vol", "0")
    if sign in ("1", "2"):
        c, arrow = "#ff3333", "\u25b2"
    elif sign in ("4", "5"):
        c, arrow = "#3399ff", "\u25bc"
    else:
        c, arrow = "#94a3b8", "\u2014"
    try:
        price_fmt = f"{int(price):,}"
        vol_fmt   = f"{int(vol):,}"
    except (ValueError, TypeError):
        price_fmt, vol_fmt = price, vol

    return html.Tr([
        html.Td(str(rank), style={"color": "#555", "width": "28px",
                                  "textAlign": "center", "padding": "5px 4px"}),
        html.Td([
            html.Div(name,   style={"color": "white", "fontWeight": "600", "fontSize": "12px"}),
            html.Div(ticker, style={"color": "#555",  "fontSize": "10px"}),
        ], style={"padding": "5px 6px"}),
        html.Td(price_fmt, style={"color": "white",  "textAlign": "right",
                                   "fontSize": "12px", "padding": "5px 4px"}),
        html.Td([
            html.Span(arrow + "\u00a0", style={"color": c}),
            html.Span(f"{chg}%", style={"color": c, "fontWeight": "600"}),
        ], style={"textAlign": "right", "fontSize": "12px", "padding": "5px 4px"}),
        html.Td(vol_fmt, style={"color": "#94a3b8", "textAlign": "right",
                                 "fontSize": "11px", "padding": "5px 4px"}),
    ], style={"borderBottom": "1px solid #1e293b"})


def _inv_row(item: dict, rank: int, qty_key: str) -> html.Tr:
    name   = item.get("name", "")
    ticker = item.get("ticker", "")
    price  = item.get("close", "0")
    ntby   = item.get(qty_key, 0)
    try:
        price_fmt = f"{int(price):,}"
        ntby_val  = int(ntby)
        ntby_fmt  = f"{ntby_val:+,}"
    except (ValueError, TypeError):
        price_fmt, ntby_fmt, ntby_val = str(price), str(ntby), 0
    color = "#ff3333" if ntby_val < 0 else "#34d399"

    return html.Tr([
        html.Td(str(rank), style={"color": "#555", "width": "28px",
                                  "textAlign": "center", "padding": "5px 4px"}),
        html.Td([
            html.Div(name,   style={"color": "white", "fontWeight": "600", "fontSize": "12px"}),
            html.Div(ticker, style={"color": "#555",  "fontSize": "10px"}),
        ], style={"padding": "5px 6px"}),
        html.Td(price_fmt, style={"color": "white", "textAlign": "right",
                                   "fontSize": "12px", "padding": "5px 4px"}),
        html.Td(ntby_fmt,  style={"color": color,  "textAlign": "right",
                                   "fontSize": "12px", "fontWeight": "600",
                                   "padding": "5px 4px"}),
    ], style={"borderBottom": "1px solid #1e293b"})


# ── Table ──────────────────────────────────────────────────

def _table(cols: list, rows: list) -> html.Table:
    return html.Table([
        html.Thead(html.Tr([
            html.Th(c, style={
                "color": "#374151", "fontSize": "10px", "fontWeight": "700",
                "letterSpacing": "0.5px", "padding": "0 4px 8px",
                "textAlign": "right" if i > 1 else ("center" if i == 0 else "left"),
            }) for i, c in enumerate(cols)
        ])),
        html.Tbody(rows if rows else [
            html.Tr(html.Td(
                "\ub370\uc774\ud130 \uc5c6\uc74c",
                colSpan=len(cols),
                style={"color": "#555", "fontSize": "12px",
                       "padding": "20px 0", "textAlign": "center"},
            ))
        ]),
    ], style={"width": "100%", "borderCollapse": "collapse"})


# ── Shared tab style ───────────────────────────────────────

_TAB = {"fontSize": "11px"}


# ── Cards ──────────────────────────────────────────────────

def _vol_card(kp_rows: list, kq_rows: list) -> html.Div:
    cols = ["#", "\uc885\ubaa9", "\ud604\uc7ac\uac00", "\ub4f1\ub77d\ub960", "\uac70\ub798\ub7c9"]
    return html.Div([
        html.Div("\uac70\ub798\ub7c9 \uc21c\uc704  TOP 20", style={
            "color": "#60a5fa", "fontSize": "12px", "fontWeight": "700",
            "letterSpacing": "1px", "marginBottom": "12px",
        }),
        dbc.Tabs([
            dbc.Tab(
                html.Div(_table(cols, kp_rows), style={"paddingTop": "12px"}),
                label="\ucf54\uc2a4\ud53c", tab_style=_TAB,
                active_label_style={"color": "#fb923c", "fontWeight": "700"},
            ),
            dbc.Tab(
                html.Div(_table(cols, kq_rows), style={"paddingTop": "12px"}),
                label="\ucf54\uc2a4\ub2e5", tab_style=_TAB,
                active_label_style={"color": "#e879f9", "fontWeight": "700"},
            ),
        ], style={"borderBottom": "1px solid #21262d"}),
    ], style={
        "background": "#161b22", "border": "1px solid #21262d",
        "borderRadius": "12px", "padding": "20px 24px", "height": "100%",
    })


def _investor_card(title: str, color: str, date_label: str,
                   kp_buy: list, kp_sell: list,
                   kq_buy: list, kq_sell: list,
                   qty_key: str) -> html.Div:
    cols = ["#", "\uc885\ubaa9", "\uc885\uac00", "\uc21c\ub9e4\uc218(\uc8fc)"]

    def rows(data):
        return [_inv_row(d, i + 1, qty_key) for i, d in enumerate(data)]

    def buy_sell_tabs(buy_rows, sell_rows):
        return dbc.Tabs([
            dbc.Tab(
                html.Div(_table(cols, buy_rows),  style={"paddingTop": "10px"}),
                label="\uc21c\ub9e4\uc218", tab_style=_TAB,
                active_label_style={"color": "#34d399", "fontWeight": "700"},
            ),
            dbc.Tab(
                html.Div(_table(cols, sell_rows), style={"paddingTop": "10px"}),
                label="\uc21c\ub9e4\ub3c4", tab_style=_TAB,
                active_label_style={"color": "#f87171", "fontWeight": "700"},
            ),
        ])

    return html.Div([
        html.Div([
            html.Span(title, style={"color": color, "fontSize": "12px",
                                    "fontWeight": "700", "letterSpacing": "1px"}),
            html.Span(
                f"\u00a0\u2014 {date_label}" if date_label else "",
                style={"color": "#374151", "fontSize": "10px", "marginLeft": "6px"},
            ),
        ], style={"marginBottom": "12px"}),

        dbc.Tabs([
            dbc.Tab(
                html.Div(buy_sell_tabs(rows(kp_buy), rows(kp_sell)),
                         style={"paddingTop": "10px"}),
                label="\ucf54\uc2a4\ud53c", tab_style=_TAB,
                active_label_style={"color": "#fb923c", "fontWeight": "700"},
            ),
            dbc.Tab(
                html.Div(buy_sell_tabs(rows(kq_buy), rows(kq_sell)),
                         style={"paddingTop": "10px"}),
                label="\ucf54\uc2a4\ub2e5", tab_style=_TAB,
                active_label_style={"color": "#e879f9", "fontWeight": "700"},
            ),
        ], style={"borderBottom": "1px solid #21262d"}),
    ], style={
        "background": "#161b22", "border": "1px solid #21262d",
        "borderRadius": "12px", "padding": "20px 24px", "height": "100%",
    })


# ── Layouts ────────────────────────────────────────────────

def _safe(fn, *args, default=None, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default


def layout_domestic() -> html.Div:
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_indices  = ex.submit(_safe, get_index_data,           default=[])
        f_vol      = ex.submit(_safe, get_volume_ranking_split, default=([], []), top=20)
        f_investor = ex.submit(_safe, get_investor_realtime,    default={}, top=20)

    indices = f_indices.result()
    vol_kp, vol_kq = f_vol.result()
    r = f_investor.result()

    saved_at   = r.get("saved_at", "")
    date_label = saved_at

    vol_kp_rows = [_vol_row(item, i + 1) for i, item in enumerate(vol_kp)]
    vol_kq_rows = [_vol_row(item, i + 1) for i, item in enumerate(vol_kq)]

    subtitle = html.P(
        f"\ub370\uc774\ud130 \uae30\uc900: {saved_at}" if saved_at else "",
        style={"color": "#374151", "fontSize": "12px", "marginBottom": "28px"}
    )

    return html.Div([
        html.H3("\uad6d\ub0b4\uc8fc\uc2dd",
                style={"color": "white", "fontWeight": "700", "marginBottom": "20px"}),
        _index_cards(indices) if indices else html.Div(),
        subtitle,
        dbc.Row([
            dbc.Col(_vol_card(vol_kp_rows, vol_kq_rows),
                    xs=12, lg=4, className="mb-4"),
            dbc.Col(
                _investor_card(
                    "\uc678\uad6d\uc778  TOP 20", "#34d399", date_label,
                    r.get("FRG_BUY",  []),
                    r.get("FRG_SELL", []),
                    r.get("FRG_BUY",  []),
                    r.get("FRG_SELL", []),
                    "frgn_ntby_qty",
                ),
                xs=12, lg=4, className="mb-4",
            ),
            dbc.Col(
                _investor_card(
                    "\uae30\uad00  TOP 20", "#f59e0b", date_label,
                    r.get("ORG_BUY",  []),
                    r.get("ORG_SELL", []),
                    r.get("ORG_BUY",  []),
                    r.get("ORG_SELL", []),
                    "orgn_ntby_qty",
                ),
                xs=12, lg=4, className="mb-4",
            ),
        ], style={"display": "flex", "flexWrap": "wrap", "alignItems": "stretch"}),
    ], style={"padding": "32px 36px", "minHeight": "100vh", "background": "#0d1117"})


def layout_overseas() -> html.Div:
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_overseas = ex.submit(_safe, get_overseas_data, default=[])
        f_fg       = ex.submit(_safe, get_fear_greed,    default={})
        f_sectors  = ex.submit(_safe, get_sector_data,   default=[])

    overseas = f_overseas.result()
    fg       = f_fg.result()
    sectors  = f_sectors.result()

    return html.Div([
        html.H3("\ud574\uc678\uc8fc\uc2dd",
                style={"color": "white", "fontWeight": "700", "marginBottom": "20px"}),
        _overseas_section(overseas, fg),
        _sector_heatmap(sectors),
    ], style={"padding": "32px 36px", "minHeight": "100vh", "background": "#0d1117"})
