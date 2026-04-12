# -*- coding: utf-8 -*-
import glob
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc


VPA_COLORS = {
    "Stopping Volume":   "#34d399",
    "No Supply":         "#60a5fa",
    "Testing":           "#a78bfa",
    "Effort vs Result":  "#fbbf24",
    "No Demand":         "#f87171",
}

VPA_ICONS = {
    "Stopping Volume":   "S",
    "No Supply":         "N",
    "Testing":           "T",
    "Effort vs Result":  "E",
    "No Demand":         "D",
}

VPA_KO = {
    "Stopping Volume":   "\uc2a4\ud1a0\ud551 \ubcfc\ub968",
    "No Supply":         "\uacf5\uae09 \ubd80\uc7ac",
    "Testing":           "\ud14c\uc2a4\ud305",
    "Effort vs Result":  "\ub178\ub825 vs \uacb0\uacfc",
    "No Demand":         "\uc218\uc694 \ubd80\uc7ac",
}


# ── Data ───────────────────────────────────────────────────

def load_latest_signals() -> pd.DataFrame:
    files = sorted(glob.glob("vpa_signals_*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.read_csv(files[-1], encoding="utf-8-sig")
    scan_date = files[-1].replace("vpa_signals_", "").replace(".csv", "")
    df["scan_date"] = scan_date[:8]
    return df


def _vpa_reason_text(row: pd.Series) -> str:
    parts = []
    price    = row.get("price", "")
    vol      = row.get("vol_ratio", "")
    vs_ma50  = row.get("vs_ma50", "")
    patterns = row.get("patterns", "")

    parts.append(
        f"\ud604\uc7ac\uac00 {int(price):,}  |  \uac70\ub798\ub7c9 {vol}  |  vs MA50 {vs_ma50}"
    )

    pattern_map = {
        "Stopping Volume": (
            "\uc138\ub825\uad8c\uc758 \ub9e4\ub3c4 \ud648\uc2b9\uc774 \uc18c\uc9c4\ub418\ub294 \uc2a4\ud1a0\ud551 \ubcfc\ub968 \ud655\uc778. "
            "\uac70\ub798\ub7c9\uc774 \ud3c9\uc18c\uc758 1.5\ubc30 \uc774\uc0c1\uc774\uba70 \uc885\uac00\uac00 \ubc14 \uc0c1\ub2e8 \uc720\uc9c0 \u2014 "
            "\ud558\ub77d \ud6c4 \uad34\ub3c4\uc218\uc815 \uc2e0\ud638."
        ),
        "No Supply": (
            "\uacf5\uae09 \ubd80\uc7ac \ud655\uc778. \uc800\ub7c9\uc758 \ud558\ub77d\uc73c\ub85c \ub9e4\ub3c4 \ud569\ub825\uc774 \uc18c\uc9c4\ub428. "
            "MA50 \uc704\uc5d0\uc11c \ubc1c\uc0dd \u2014 \ub9e4\uc218\uc138\ub825\uc774 \uc8fc\ub3c4\ud560 \uc900\ube44 \uc0c1\ud0dc."
        ),
        "Testing": (
            "\ud14c\uc2a4\ud305 \ud655\uc778. \ud3c9\uade0\ubcf4\ub2e4\ub3c4 \uc801\uc740 \uac70\ub798\ub7c9\uc73c\ub85c \uc9c0\uc9c0\uc120 \ud558\ub77d \ud14c\uc2a4\ud2b8 \uc2dc\ub3c4 \u2014 "
            "\ubcc4\ub2e4\ub978 \ud558\ub77d \uc5c6\uc774 \ubc18\ub4f1. \ub9e4\uc218\uc138\ub825\uc774 \uc8fc\ub3c4\ud558\ub294 \uc870\uc6a9\ud55c \uad6c\uac04."
        ),
        "Effort vs Result": (
            "\ub178\ub825 vs \uacb0\uacfc \ud655\uc778. \uac15\ud55c \uac70\ub798\ub7c9(2\ubc30 \uc774\uc0c1)\uc744 \uc218\ubc18\ud55c \ub300\ud615 \uc591\ubd09. "
            "\uc885\uac00\uac00 \ubc14 \uc0c1\ub2e8(70% \uc774\uc0c1) \uc720\uc9c0 \u2014 \uc218\uc694\uc758 \uc801\uadf9\uc801 \ucc38\uc5ec\ub97c \uc758\ubbf8."
        ),
        "No Demand": (
            "\uc218\uc694 \ubd80\uc7ac \ud655\uc778. \uc800\ub7c9\uc758 \uc591\ubd09\uc73c\ub85c \ub9e4\uc218\uc138\ub825 \ubbf8\uc57d. "
            "\uac00\uaca9 \uc0c1\uc2b9\uc5d0\ub3c4 \uc2e4\uc9c8 \uc218\uc694\uac00 \ub4a4\ub530\ub974\uc9c0 \uc54a\uc558\uc74c \u2014 \uc8fc\uc758 \ud544\uc694."
        ),
    }

    for p in str(patterns).split(" + "):
        p = p.strip()
        if p in pattern_map:
            parts.append(pattern_map[p])

    return "  |  ".join(parts)


# ── UI Helpers ─────────────────────────────────────────────

def _metric(label, value, positive=None):
    color = "#34d399" if positive is True else "#f87171" if positive is False else "#94a3b8"
    return html.Div([
        html.Div(label, style={"color": "#666", "fontSize": "10px"}),
        html.Div(value, style={"color": color, "fontWeight": "600", "fontSize": "13px"}),
    ])


def make_vpa_card(row: pd.Series, idx: int) -> dbc.Col:
    ticker   = str(row["ticker"]).zfill(6)
    name     = row["name"]
    pattern  = row.get("pattern", "")
    price    = row.get("price", 0)
    vs_ma50  = str(row.get("vs_ma50", ""))
    vol      = row.get("vol_ratio", "")
    patterns = row.get("patterns", pattern)
    color    = VPA_COLORS.get(pattern, "#888")
    icon     = VPA_ICONS.get(pattern, "?")
    ko       = VPA_KO.get(pattern, pattern)

    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(icon, style={
                    "background": color, "color": "#0d1117",
                    "borderRadius": "5px", "padding": "2px 9px",
                    "fontWeight": "800", "fontSize": "11px", "marginRight": "8px",
                }),
                html.Span(ko, style={"color": color, "fontSize": "11px", "fontWeight": "600"}),
            ], style={"marginBottom": "10px"}),

            html.H6(name, style={"color": "white", "marginBottom": "2px", "fontSize": "15px"}),
            html.Div(ticker, style={"color": "#555", "fontSize": "11px", "marginBottom": "12px"}),

            html.Div([
                _metric("\uac00\uaca9", f"{int(price):,}"),
                _metric("vs MA50", vs_ma50, positive=vs_ma50.startswith("+")),
                _metric("\uac70\ub798\ub7c9", str(vol)),
            ], style={"display": "flex", "gap": "10px", "marginBottom": "14px",
                      "flexWrap": "wrap"}),

            html.Div(str(patterns), style={
                "color": "#64748b", "fontSize": "11px", "marginBottom": "12px",
                "lineHeight": "1.4",
            }) if " + " in str(patterns) else html.Div(),

            dbc.Button("\ucc28\ud2b8 \ubcf4\uae30", id={"type": "vpa-chart-btn", "index": idx},
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


# ── VPA Strategy Explanation ───────────────────────────────

def _vpa_pillar(icon, title, color, desc):
    return dbc.Col(html.Div([
        html.Div([
            html.Span(icon, style={
                "background": color, "color": "#0d1117",
                "borderRadius": "5px", "width": "26px", "height": "26px",
                "display": "inline-flex", "alignItems": "center",
                "justifyContent": "center", "fontWeight": "800",
                "fontSize": "11px", "marginRight": "10px",
            }),
            html.Span(title, style={"color": color, "fontWeight": "700", "fontSize": "14px"}),
        ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"}),
        html.P(desc, style={"color": "#94a3b8", "fontSize": "13px", "lineHeight": "1.6", "margin": 0}),
    ], style={
        "background": "#161b22", "border": f"1px solid {color}33",
        "borderRadius": "10px", "padding": "16px", "height": "100%",
    }), xs=12, sm=6, md=4, lg=True, className="mb-3")


def build_strategy_section():
    return html.Div([

        html.H3("VPA \uc804\ub7b5\uc774\ub780?",
                style={"color": "white", "fontWeight": "700", "marginBottom": "8px"}),
        html.P(
            "VPA(Volume Price Analysis)\ub294 \uc560\ub098 \ucfe8\ub9c1(Anna Coulling)\uc758 \uac70\ub798\ub7c9 \ud22c\uc790 \uae30\ubc95\uc785\ub2c8\ub2e4. "
            "\uc8fc\uac00\uc758 \ub4f1\ub77d\ud3ed(\uc2a4\ud504\ub808\ub4dc)\uacfc \uac70\ub798\ub7c9\uc744 \ud568\uaed8 \ubd84\uc11d\ud574 "
            "\uc138\ub825 \uc8fc\uccb4(\uc2a4\ub9c8\ud2b8 \uba38\ub2c8)\uc758 \ud589\ub3d9\uc744 \uac10\uc9c0\ud569\ub2c8\ub2e4.",
            style={"color": "#94a3b8", "fontSize": "14px", "marginBottom": "28px", "maxWidth": "760px"}
        ),

        dbc.Row([
            _vpa_pillar("S", "Stopping Volume", "#34d399",
                        "\uc138\ub825 \uc8fc\uccb4\uac00 \ub9e4\ub3c4 \ubb3c\ub7c9\uc744 \ud761\uc218\ud569\ub2c8\ub2e4. "
                        "\uacf5\uae09 \uacfc\uc789\ub2e4\ub294 \uc2e0\ud638\ub85c, \ud558\ub77d \ubb34\ub825\ud654\uc758 \uc2dc\uc791\uc744 \uc758\ubbf8\ud569\ub2c8\ub2e4."),
            _vpa_pillar("N", "No Supply", "#60a5fa",
                        "\ub9e4\ub3c4 \uc138\ub825\uc774 \uc788\ub294\ub370 \uac70\ub798\ub7c9\uc774 \uc801\uc2b5\ub2c8\ub2e4. "
                        "\uc2a4\ub9c8\ud2b8 \uba38\ub2c8\uac00 \uc8fc\uc2dd\uc744 \ud568\ubd80\ub85c \ub098\ub204\uc9c0 \uc54a\uc544 \uc2e4\uc9c8 \uacf5\uae09\uc774 \uc5c6\ub294 \uc0c1\ud0dc."),
            _vpa_pillar("T", "Testing", "#a78bfa",
                        "\uc601\ub9ac\ud55c \uac70\ub798\ub7c9\uc73c\ub85c \uc9c0\uc9c0\uc120\uc744 \ud14c\uc2a4\ud2b8\ud569\ub2c8\ub2e4. "
                        "\ud558\ub77d\ub9cc\ud07c \uacf5\uae09\uc774 \ub098\ud0c0\ub098\uc9c0 \uc54a\uc73c\uba74 \ub9e4\uc218\uc138 \uc720\uc9c0 \ud655\uc778."),
            _vpa_pillar("E", "Effort vs Result", "#fbbf24",
                        "\uac15\ud55c \uac70\ub798\ub7c9(2\ubc30 \uc774\uc0c1)\uc744 \uc218\ubc18\ud55c \ub300\ud615 \uc591\ubd09. "
                        "\uc218\uc694\uac00 \uc2e4\uc9c8\uc801\uc73c\ub85c \uc720\uc785\ub418\uc5b4 \uc0c1\uc2b9 \uc720\uc9c0\ub97c \ud655\uc778\ud558\ub294 \uc2e0\ud638."),
            _vpa_pillar("D", "No Demand", "#f87171",
                        "\uc800\ub7c9 \uc591\ubd09\uc73c\ub85c \uc218\uc694 \ubd80\uc7ac\ub97c \uc758\ubbf8\ud569\ub2c8\ub2e4. "
                        "\uac00\uaca9\uc774 \uc0c1\uc2b9\ud574\ub3c4 \uc2e4\uc9c8 \uc218\uc694\uac00 \ub4a4\ub530\ub974\uc9c0 \uc54a\uc544 \uc8fc\uc758 \ud544\uc694."),
        ], className="mb-4"),

        html.Div([
            html.H5("VPA \ud3ec\uc9c0\uc158 \uc2dc\uadf8\ub110  (\uc2a4\ud1a0\ud551 \u00b7 \uacf5\uae09\ubd80\uc7ac \u00b7 \ud14c\uc2a4\ud305 \u00b7 \ub178\ub825\uacb0\uacfc)",
                    style={"color": "white", "fontWeight": "600", "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col(html.Div([
                    html.Span("\uc2a4\ud504\ub808\ub4dc", style={
                        "background": "#1e293b", "color": "#6366f1",
                        "borderRadius": "4px", "padding": "1px 7px",
                        "fontSize": "11px", "fontWeight": "700", "marginRight": "8px",
                    }),
                    html.Span("\uce94\ub4e4\uc758 \uace0\uc800\uac00 \ucc28\uc774 \u2014 \uc791\uc744\uc218\ub85d \uc800\ud56d \ucef4\ud50c\ub809\uc2a4 \ud604\uc0c1",
                              style={"color": "#cbd5e1", "fontSize": "13px"}),
                ], style={"marginBottom": "10px"}), xs=12, sm=6, md=4),
                dbc.Col(html.Div([
                    html.Span("\uac70\ub798\ub7c9", style={
                        "background": "#1e293b", "color": "#6366f1",
                        "borderRadius": "4px", "padding": "1px 7px",
                        "fontSize": "11px", "fontWeight": "700", "marginRight": "8px",
                    }),
                    html.Span("20\uc77c \ud3c9\uade0 \ub300\ube44 \ube44\uc728\ub85c \ud3c9\uac00 \u2014 \ub192\uc744\uc218\ub85d \uc138\ub825 \uc8fc\uccb4 \uac1c\uc785 \uac00\ub2a5\uc131",
                              style={"color": "#cbd5e1", "fontSize": "13px"}),
                ], style={"marginBottom": "10px"}), xs=12, sm=6, md=4),
                dbc.Col(html.Div([
                    html.Span("\uc885\uac00 \uc704\uce58", style={
                        "background": "#1e293b", "color": "#6366f1",
                        "borderRadius": "4px", "padding": "1px 7px",
                        "fontSize": "11px", "fontWeight": "700", "marginRight": "8px",
                    }),
                    html.Span("\uce94\ub4e4 \ubc94\uc704 \ub0b4 \uc885\uac00\uac00 \uc5b4\ub514\uc5d0 \uc788\ub294\uc9c0 \u2014 0=\uc800\uc810, 1=\uace0\uc810",
                              style={"color": "#cbd5e1", "fontSize": "13px"}),
                ], style={"marginBottom": "10px"}), xs=12, sm=6, md=4),
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
    cards_row = html.Div(
        "\uc2a4\uce94\ub108 \ub370\uc774\ud130\uac00 \uc5c6\uc2b5\ub2c8\ub2e4. vpa_scanner.py\ub97c \uba3c\uc800 \uc2e4\ud589\ud558\uc138\uc694.",
        style={"color": "#666", "padding": "20px"}
    )

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
            c = VPA_COLORS.get(pat, "#888")
            badges.append(html.Span(
                f"{VPA_KO.get(pat, pat)}  {cnt}",
                className="me-2",
                style={"backgroundColor": c, "color": "#0d1117",
                       "fontSize": "12px", "padding": "5px 12px",
                       "borderRadius": "6px", "fontWeight": "700",
                       "display": "inline-block"},
            ))

        cards_row = dbc.Row([
            make_vpa_card(row, i)
            for i, (_, row) in enumerate(df.iterrows())
        ])

    return html.Div([

        build_strategy_section(),

        html.Hr(style={"borderColor": "#21262d", "margin": "8px 0 32px"}),

        html.Div([
            html.H4("\uc624\ub298\uc758 VPA \uc2dc\uadf8\ub110",
                    style={"color": "white", "fontWeight": "700", "marginBottom": "4px"}),
            html.Div([
                html.Span(
                    f"\ub9c8\uc9c0\ub9c9 \uc2a4\uce94: {scan_date[:4]}-{scan_date[4:6]}-{scan_date[6:]}"
                    if scan_date else "\uc2a4\uce94 \ub370\uc774\ud130 \uc5c6\uc74c",
                    style={"color": "#555", "fontSize": "12px", "marginRight": "16px"}
                ),
                html.Span("KOSPI + KOSDAQ  |  \uc804\uccb4 \uc885\ubaa9 \uc2a4\uce94",
                          style={"color": "#555", "fontSize": "12px"}),
            ], style={"marginBottom": "16px"}),
            html.Div(badges, style={"marginBottom": "20px"}),
        ]),

        cards_row,

        html.Div(id="vpa-chart-area", style={"marginTop": "16px"}),

        dcc.Store(id="vpa-signals-store", data=df.to_dict("records") if not df.empty else []),

    ], className="page-wrap")
