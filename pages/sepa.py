import glob
import pandas as pd
from dash import dcc, html, no_update
import dash_bootstrap_components as dbc
from data_fetcher import get_ohlcv
from strategy import (
    check_trend_template, check_vcp, check_double_bottom,
    check_breakout, check_pivot
)
from components.chart_plotly import build_chart


PATTERN_COLORS = {
    "VCP":                "#a78bfa",
    "Double Bottom":      "#34d399",
    "Flat Base Breakout": "#fbbf24",
    "Pivot Setup":        "#60a5fa",
}

PATTERN_ICONS = {
    "VCP":                "V",
    "Double Bottom":      "W",
    "Flat Base Breakout": "B",
    "Pivot Setup":        "P",
}

PATTERN_KO = {
    "VCP":                "VCP (\ubcc0\ub3d9\uc131 \uc218\ucd95)",
    "Double Bottom":      "\uc774\uc911\ubc14\ub2e5",
    "Flat Base Breakout": "\ud50c\ub7ab \ubca0\uc774\uc2a4 \ub3cc\ud30c",
    "Pivot Setup":        "\ud53c\ubd07 \uc14b\uc5c5",
}


# ── Data ───────────────────────────────────────────────────

def load_latest_signals() -> pd.DataFrame:
    files = sorted(glob.glob("signals_*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.read_csv(files[-1], encoding="utf-8-sig")
    scan_date = files[-1].replace("signals_", "").replace(".csv", "")
    df["scan_date"] = scan_date[:8]
    return df


def _reason_text(ticker: str, row: pd.Series) -> str:
    df = get_ohlcv(ticker, days=250)
    if df.empty or len(df) < 200:
        return ""
    close    = df["Close"]
    cur      = close.iloc[-1]
    high_52w = close.tail(252).max()
    low_52w  = close.tail(252).min()
    avg_vol  = df["Volume"].iloc[-20:].mean()
    last_vol = df["Volume"].iloc[-1]

    parts = [
        f"\ud604\uc7ac\uac00 {int(cur):,}  |  52\uc8fc \uace0\uc810 {int(high_52w):,}  "
        f"\uc800\uc810 {int(low_52w):,}  |  \uac70\ub798\ub7c9 {last_vol/avg_vol:.1f}x (20\uc77c \ud3c9\uade0)"
    ]
    trend = check_trend_template(df)
    if trend:
        parts.append(f"2\ub2e8\uacc4 \uc0c1\uc2b9 \ud655\uc778 ({trend['passed']}/7) \u2014 "
                     f"MA50 {trend['ma50']:,} / MA150 {trend['ma150']:,} / MA200 {trend['ma200']:,}")
    db = check_double_bottom(df)
    if db:
        parts.append(f"{db['bottom1']:,}\uc5d0\uc11c \ub450 \ubc88 \ub9e4\uc218\uc138\uac00 \ud655\uc778\ub428. "
                     f"\ub137\ub77c\uc778 \ub3cc\ud30c {db['neckline']:,} (\ud604\uc7ac\uac00 \ucc28\uc774: {db['dist_from_neckline']}).")
    vcp = check_vcp(df)
    if vcp:
        parts.append(f"\ubcc0\ub3d9\uc131 \uc218\ucd95: {vcp['range1']} > {vcp['range2']} > {vcp['range3']} "
                     f"\u2014 \ub3cc\ud30c \uc804 \uc5d0\ub108\uc9c0 \uc751\uccd5 \uc911.")
    bo = check_breakout(df)
    if bo:
        parts.append(f"\ubc15\uc2a4 \uace0\uc810 {bo['box_high']:,} \ub3cc\ud30c, \uac70\ub798\ub7c9 {bo['vol_ratio']} "
                     f"({bo['box_range']} \ud1b5\ud569 \ud6c4).")
    pv = check_pivot(df)
    if pv:
        parts.append(f"\ud53c\ubc97 {pv['pivot_price']:,} (\ud604\uc7ac\uac00 \ucc28\uc774: {pv['distance']}). "
                     f"\uac70\ub798\ub7c9 \uc218\ucd95 \uc911 \u2014 \uc800\ub9ac\uc2a4\ud06c \uc9c4\uc785 \uad6c\uac04.")
    return "  |  ".join(parts)


# ── UI Helpers ─────────────────────────────────────────────

def _metric(label, value, positive=None):
    color = "#34d399" if positive is True else "#f87171" if positive is False else "#94a3b8"
    return html.Div([
        html.Div(label, style={"color": "#666", "fontSize": "10px"}),
        html.Div(value, style={"color": color, "fontWeight": "600", "fontSize": "13px"}),
    ])


def make_stock_card(row: pd.Series, idx: int) -> dbc.Col:
    ticker  = str(row["ticker"]).zfill(6)
    name    = row["name"]
    pattern = row.get("pattern", "")
    market  = row.get("market", "")
    price   = row.get("price", 0)
    vs_ma50 = str(row.get("vs_ma50", ""))
    vol     = row.get("vol_ratio", "")
    score   = row.get("trend_score", "")
    color      = PATTERN_COLORS.get(pattern, "#888")
    icon       = PATTERN_ICONS.get(pattern, "?")
    pattern_ko = PATTERN_KO.get(pattern, pattern)

    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(icon, style={
                    "background": color, "color": "#0d1117",
                    "borderRadius": "5px", "padding": "2px 9px",
                    "fontWeight": "800", "fontSize": "11px", "marginRight": "8px",
                }),
                html.Span(pattern_ko, style={"color": color, "fontSize": "11px", "fontWeight": "600"}),
                html.Span(market, style={"float": "right", "color": "#555", "fontSize": "11px"}),
            ], style={"marginBottom": "10px"}),

            html.H6(name, style={"color": "white", "marginBottom": "2px", "fontSize": "15px"}),
            html.Div(ticker, style={"color": "#555", "fontSize": "11px", "marginBottom": "12px"}),

            html.Div([
                _metric("\uac00\uaca9", f"{int(price):,}"),
                _metric("vs MA50", vs_ma50, positive=vs_ma50.startswith("+")),
                _metric("\uac70\ub798\ub7c9", str(vol)),
                _metric("\ud2b8\ub80c\ub4dc", str(score)),
            ], style={"display": "flex", "gap": "10px", "marginBottom": "14px",
                      "flexWrap": "wrap"}),

            dbc.Button("\ucc28\ud2b8 \ubcf4\uae30", id={"type": "chart-btn", "index": idx},
                       size="sm", style={
                           "width": "100%", "background": "transparent",
                           "border": f"1px solid {color}", "color": color,
                           "fontWeight": "600", "fontSize": "12px",
                       }),
        ])
    ], style={
        "background": "#161b22", "border": "1px solid #21262d",
        "borderRadius": "12px", "height": "100%",
    }), xs=12, sm=6, md=4, lg=3, className="mb-3")


# ── SEPA Strategy Explanation ──────────────────────────────

def _pillar(num, title, color, desc):
    return dbc.Col(html.Div([
        html.Div([
            html.Span(num, style={
                "background": color, "color": "#0d1117",
                "borderRadius": "50%", "width": "26px", "height": "26px",
                "display": "inline-flex", "alignItems": "center",
                "justifyContent": "center", "fontWeight": "800",
                "fontSize": "12px", "marginRight": "10px",
            }),
            html.Span(title, style={"color": color, "fontWeight": "700", "fontSize": "15px"}),
        ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"}),
        html.P(desc, style={"color": "#94a3b8", "fontSize": "13px", "lineHeight": "1.6", "margin": 0}),
    ], style={
        "background": "#161b22", "border": f"1px solid {color}33",
        "borderRadius": "10px", "padding": "16px", "height": "100%",
    }), xs=12, sm=6, md=4, lg=True, className="mb-3")


def _trend_cond(num, text):
    return dbc.Col(html.Div([
        html.Span(num, style={
            "background": "#1e293b", "color": "#6366f1",
            "borderRadius": "4px", "padding": "1px 7px",
            "fontSize": "11px", "fontWeight": "700", "marginRight": "8px",
        }),
        html.Span(text, style={"color": "#cbd5e1", "fontSize": "13px"}),
    ], style={"marginBottom": "10px"}), xs=12, sm=6, md=4)


def build_strategy_section():
    return html.Div([

    # Title
    html.H3("SEPA \uc804\ub7b5\uc774\ub780?",
            style={"color": "white", "fontWeight": "700", "marginBottom": "8px"}),
    html.P(
        "SEPA(Specific Entry Point Analysis)\ub294 \ub9c8\ud06c \ubbf8\ub108\ube44\ub2c8\uc758 "
        "\uc131\uc7a5\uc8fc \ud22c\uc790 \uc804\ub7b5\uc785\ub2c8\ub2e4. "
        "\uae30\uc220\uc801 \ucd94\uc138 \ubd84\uc11d\uacfc \uc815\ubc00\ud55c \uc9c4\uc785 \ud0c0\uc774\ubc0d\uc744 \uacb0\ud569\ud574 "
        "\uae09\ub4f1 \ud655\ub960\uc774 \ub192\uc740 \uc885\ubaa9\uc744 \uc0ac\uc804\uc5d0 \ud3ec\ucc29\ud569\ub2c8\ub2e4.",
        style={"color": "#94a3b8", "fontSize": "14px", "marginBottom": "28px", "maxWidth": "760px"}
    ),

    # 5 pillars
    dbc.Row([
        _pillar("1", "\ucd94\uc138", "#6366f1",
                "2\ub2e8\uacc4 \uc0c1\uc2b9 \uad6d\uba74\uc774\uc5b4\uc57c \ud569\ub2c8\ub2e4. "
                "\uc8fc\uac00\uac00 MA50, MA150, MA200 \uc704\uc5d0 \uc815\ubc30\uc5f4\ub418\uc5b4 \uc788\uc5b4\uc57c \ud558\uba70 "
                "MA200\uc774 \uc6b0\uc0c1\ud5a5 \uae30\uc6b8\uae30\ub97c \uc720\uc9c0\ud574\uc57c \ud569\ub2c8\ub2e4."),
        _pillar("2", "\uc9c4\uc785 \ud0c0\uc774\ubc0d", "#34d399",
                "\ub9ac\uc2a4\ud06c\ub294 \uc801\uace0 \uc218\uc775\uc740 \ud070 \uc790\ub9ac\ub97c \uae30\ub2e4\ub9bd\ub2c8\ub2e4. "
                "\uac74\uc804\ud55c \ube2f\uc2dc \ud6c4 VCP, \uc774\uc911\ubc14\ub2e5, "
                "\ud50c\ub7ab \ubca0\uc774\uc2a4 \ud328\ud134\uc774 \ud615\uc131\ub420 \ub54c \uc9c4\uc785\ud569\ub2c8\ub2e4."),
        _pillar("3", "\ubcc0\ub3d9\uc131 \uc218\ucd95", "#fbbf24",
                "\uc8fc\uac00 \ub4f1\ub77d\ud3ed\uc774 \uc810\uc810 \uc900\uc5b4\ub4ed\ub2c8\ub2e4. "
                "\uac70\ub798\ub7c9\ub3c4 \ub9d0\ub77c\uac11\ub2c8\ub2e4. "
                "\ub2e4\uc74c \uc0c1\uc2b9\uc744 \uc704\ud55c \uc5d0\ub108\uc9c0\uac00 \ucd95\uc801\ub418\ub294 \uc2e0\ud638\uc785\ub2c8\ub2e4."),
        _pillar("4", "\ud53c\ubc97 \ub3cc\ud30c", "#f472b6",
                "\uac15\ud55c \uac70\ub798\ub7c9(1.5\ubc30 \uc774\uc0c1)\uc744 \uc218\ubc18\ud55c "
                "\ud53c\ubc97 \ub3cc\ud30c \uc2dc \ub9e4\uc218\ud569\ub2c8\ub2e4. "
                "\ub3cc\ud30c\ub97c \ud655\uc778\ud558\uae30 \uc804\uc5d0 \uc808\ub300 \uc120\ub9e4\ub9ac\ud558\uc9c0 \ub9c8\uc138\uc694."),
        _pillar("5", "\ub9e4\ub3c4 \uc6d0\uce59", "#60a5fa",
                "\ubca0\uc774\uc2a4 \uc544\ub798\uc5d0 \uc190\uc808\uc120\uc744 \uc124\uc815\ud569\ub2c8\ub2e4. "
                "\ubaa8\uba58\ud140\uc774 \uc2a4\ub7ec\uc9c0\uac70\ub098 "
                "3\ub2e8\uacc4 \ubd84\uc0b0 \uc2e0\ud638\uac00 \ubcf4\uc77c \ub54c \ub9e4\ub3c4\ud569\ub2c8\ub2e4."),
    ], className="mb-4"),

    # Trend Template detail
    html.Div([
        html.H5("2\ub2e8\uacc4 \ud2b8\ub80c\ub4dc \ud15c\ud50c\ub9bf  (7\uac00\uc9c0 \uc870\uac74)",
                style={"color": "white", "fontWeight": "600", "marginBottom": "16px"}),
        dbc.Row([
            _trend_cond(num, text) for num, text in [
                ("1", "\ud604\uc7ac\uac00 > MA150, MA200"),
                ("2", "MA150 > MA200"),
                ("3", "MA200 \uc0c1\uc2b9 \uae30\uc6b8\uae30 \uc720\uc9c0"),
                ("4", "MA50 > MA150, MA200"),
                ("5", "\ud604\uc7ac\uac00 > MA50"),
                ("6", "\ud604\uc7ac\uac00 \uac00 52\uc8fc \uc800\uc810\ubcf4\ub2e4 30% \uc774\uc0c1 \uc704"),
                ("7", "\ud604\uc7ac\uac00\uac00 52\uc8fc \uace0\uc810\uc758 25% \uc774\ub0b4"),
            ]
        ]),
    ], style={
        "background": "#0f172a", "border": "1px solid #1e293b",
        "borderRadius": "12px", "padding": "20px 24px", "marginBottom": "40px",
    }),

], style={"marginBottom": "8px"})


# ── Main Layout ────────────────────────────────────────────

def layout() -> html.Div:
    df = load_latest_signals()

    scan_date = ""
    total     = 0
    badges    = []
    cards_row = html.Div("\uc2a4\uce90\ub108 \ub370\uc774\ud130\uac00 \uc5c6\uc2b5\ub2c8\ub2e4. scanner.py\ub97c \uba3c\uc800 \uc2e4\ud589\ud558\uc138\uc694.",
                          style={"color": "#666", "padding": "20px"})

    if not df.empty:
        scan_date = df["scan_date"].iloc[0] if "scan_date" in df.columns else ""
        total     = len(df)
        pattern_counts = df["pattern"].value_counts().to_dict()

        badges = [
            html.Span(f"\uc804\uccb4  {total}", className="me-2",
                      style={"backgroundColor": "#4b5563", "color": "white",
                             "fontSize": "12px", "padding": "5px 12px",
                             "borderRadius": "6px", "fontWeight": "700",
                             "display": "inline-block"}),
        ]
        for pat, cnt in pattern_counts.items():
            c = PATTERN_COLORS.get(pat, "#888")
            badges.append(html.Span(
                f"{PATTERN_KO.get(pat, pat)}  {cnt}",
                className="me-2",
                style={"backgroundColor": c, "color": "#0d1117",
                       "fontSize": "12px", "padding": "5px 12px",
                       "borderRadius": "6px", "fontWeight": "700",
                       "display": "inline-block"},
            ))

        cards_row = dbc.Row([
            make_stock_card(row, i)
            for i, (_, row) in enumerate(df.iterrows())
        ])

    return html.Div([

        # ── SEPA Explanation ──────────────────────────────
        build_strategy_section(),

        html.Hr(style={"borderColor": "#21262d", "margin": "8px 0 32px"}),

        # ── Scanner Results ───────────────────────────────
        html.Div([
            html.H4("\uc624\ub298\uc758 \uc2dc\uadf8\ub110", style={"color": "white", "fontWeight": "700",
                                              "marginBottom": "4px"}),
            html.Div([
                html.Span(
                    f"\ub9c8\uc9c0\ub9c9 \uc2a4\uce94: {scan_date[:4]}-{scan_date[4:6]}-{scan_date[6:]}"
                    if scan_date else "\uc2a4\uce94 \ub370\uc774\ud130 \uc5c6\uc74c",
                    style={"color": "#555", "fontSize": "12px", "marginRight": "16px"}
                ),
                html.Span("KOSPI + KOSDAQ  |  2,772\uc885\ubaa9 \uc2a4\uce94",
                          style={"color": "#555", "fontSize": "12px"}),
            ], style={"marginBottom": "16px"}),
            html.Div(badges, style={"marginBottom": "20px"}),
        ]),

        cards_row,

        # ── Chart Area (populated on click) ───────────────
        html.Div(id="chart-area", style={"marginTop": "16px"}),

        dcc.Store(id="signals-store", data=df.to_dict("records") if not df.empty else []),

    ], style={"padding": "32px 36px", "minHeight": "100vh", "background": "#0d1117"})
