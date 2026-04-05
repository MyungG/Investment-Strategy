# -*- coding: utf-8 -*-
from dash import html
import dash_bootstrap_components as dbc


def _feature_card(icon, title, desc):
    return dbc.Col(html.Div([
        html.Div(icon, style={
            "fontSize": "28px", "marginBottom": "14px",
        }),
        html.H6(title, style={
            "color": "white", "fontWeight": "700",
            "fontSize": "15px", "marginBottom": "8px",
        }),
        html.P(desc, style={
            "color": "#64748b", "fontSize": "13px",
            "lineHeight": "1.7", "margin": 0,
        }),
    ], style={
        "background": "#161b22",
        "border": "1px solid #21262d",
        "borderRadius": "12px",
        "padding": "24px",
        "height": "100%",
    }), xs=12, sm=6, md=4, className="mb-4")


def _strategy_card(tag, title, color, desc, href, badge_list):
    return dbc.Col(html.A([
        html.Div([
            # Header
            html.Div([
                html.Span(tag, style={
                    "backgroundColor": color, "color": "#0d1117",
                    "borderRadius": "6px", "padding": "3px 10px",
                    "fontWeight": "800", "fontSize": "12px",
                    "marginRight": "10px",
                }),
                html.Span(title, style={
                    "color": "white", "fontWeight": "700", "fontSize": "16px",
                }),
            ], style={"marginBottom": "10px", "display": "flex", "alignItems": "center"}),

            html.P(desc, style={
                "color": "#94a3b8", "fontSize": "13px",
                "lineHeight": "1.7", "marginBottom": "16px",
            }),

            # Pattern badges
            html.Div([
                html.Span(b, style={
                    "backgroundColor": "#1e293b", "color": "#94a3b8",
                    "borderRadius": "4px", "padding": "3px 8px",
                    "fontSize": "11px", "marginRight": "6px",
                    "display": "inline-block", "marginBottom": "4px",
                }) for b in badge_list
            ]),

            # CTA
            html.Div([
                html.Span("\uc2a4\uce90\ub108 \uc5f4\uae30  \u2192", style={
                    "color": color, "fontSize": "13px", "fontWeight": "600",
                }),
            ], style={"marginTop": "18px"}),
        ]),
    ], href=href, style={"textDecoration": "none"}),
    style={
        "background": "#161b22",
        "border": f"1px solid {color}44",
        "borderRadius": "14px",
        "padding": "24px",
        "height": "100%",
        "transition": "border-color 0.2s",
    }, xs=12, md=6, lg=4, className="mb-4")


def layout():
    return html.Div([

        # ── Hero ─────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H1([
                    html.Span("SignalFinder", style={
                        "background": "linear-gradient(135deg, #6366f1, #8b5cf6)",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                    }),
                ], style={
                    "color": "white", "fontWeight": "800",
                    "fontSize": "42px", "lineHeight": "1.2",
                    "marginBottom": "20px",
                }),
                html.P(
                    "\ud22c\uc790\uc804\ub7b5\uc5d0 \ub9de\ub294 \uc9c4\uc785\ud0c0\uc810\uc744 \uc790\ub3d9\uc73c\ub85c \uc2a4\uce90\ub2dd\ud569\ub2c8\ub2e4.",
                    style={
                        "color": "white", "fontSize": "20px",
                        "fontWeight": "600", "lineHeight": "1.5",
                        "maxWidth": "620px", "marginBottom": "16px",
                    }
                ),
                html.P(
                    "\uc88b\uc740 \ud22c\uc790 \uc885\ubaa9\uc740 \uc2a4\uc2a4\ub85c \ub3c4\ub4dc\ub77c\uc9c0\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4. "
                    "\uac80\uc99d\ub41c \ud22c\uc790 \uc804\ub7b5\uc744 \uae30\ubc18\uc73c\ub85c \uc804\uccb4 \ud22c\uc790 \uc885\ubaa9\uc744 "
                    "\ub9e4\uc77c \uc790\ub3d9 \ubd84\uc11d\ud574 \uc2e4\uc81c \ub9e4\uc218\uac00 \uac00\ub2a5\ud55c \uc790\ub9ac\ub97c \ud544\ud130\ub9c1\ud569\ub2c8\ub2e4. "
                    "\uc120\uc815\ub41c \uc885\ubaa9\uc740 \ucc28\ud2b8\uc640 \uc120\uc815 \uc774\uc720\ub97c \ud568\uaed8 \uc81c\uacf5\ud558\uba70, "
                    "\uc5b4\ub5a4 \uc870\uac74\uc744 \ub9cc\uc871\ud588\ub294\uc9c0 \uc9c1\uc811 \ud655\uc778\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
                    style={
                        "color": "#64748b", "fontSize": "14px",
                        "lineHeight": "1.9", "maxWidth": "620px",
                        "marginBottom": "32px",
                    }
                ),
            ]),
        ], style={
            "padding": "72px 0 60px",
            "borderBottom": "1px solid #21262d",
            "marginBottom": "60px",
        }),

        # ── Features ─────────────────────────────────────────
        html.H4("\uc81c\uacf5 \uae30\ub2a5", style={
            "color": "white", "fontWeight": "700",
            "marginBottom": "24px",
        }),
        dbc.Row([
            _feature_card(
                "\ud83d\udd0d",
                "\uc790\ub3d9 \uc885\ubaa9 \uc2a4\uce94",
                "\uc804\uccb4 \uc0c1\uc7a5 \uc885\ubaa9\uc744 \ub9e4\uc77c \uc2a4\uce94\ud558\uc5ec "
                "\uc804\ub7b5 \uc870\uac74\uc744 \ub9cc\uc871\ud558\ub294 \uc885\ubaa9\ub9cc \ud544\ud130\ub9c1\ud569\ub2c8\ub2e4."
            ),
            _feature_card(
                "\ud83d\udcca",
                "\ud328\ud134 \uac10\uc9c0",
                "VCP\u00b7\uc774\uc911\ubc14\ub2e5\u00b7\ud50c\ub7ab \ubca0\uc774\uc2a4 \ub4f1 "
                "\uad6c\uccb4\uc801\uc778 \uc9c4\uc785 \ud328\ud134\uc744 \uc790\ub3d9\uc73c\ub85c \uac10\uc9c0\ud569\ub2c8\ub2e4."
            ),
            _feature_card(
                "\ud83d\udcc8",
                "\uc778\ud130\ub799\ud2f0\ube0c \ucc28\ud2b8",
                "\uc120\uc815 \uc885\ubaa9\uc758 \uce90\ub4e4\uc2a4\ud2f1 \ucc28\ud2b8\uc640 "
                "\uc120\uc815 \uc774\uc720\ub97c \uc2dc\uac01\uc801\uc73c\ub85c \ud655\uc778\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."
            ),
        ], style={"marginBottom": "60px"}),

        # ── Strategy List ─────────────────────────────────────
        html.H4("\uc804\ub7b5 \ubaa9\ub85d", style={
            "color": "white", "fontWeight": "700",
            "marginBottom": "8px",
        }),
        html.P(
            "\uac01 \uc804\ub7b5 \ud398\uc774\uc9c0\uc5d0\uc11c \uc804\ub7b5 \uc124\uba85\uacfc \uc2a4\uce94 \uacb0\uacfc\ub97c \ud568\uaed8 \ud655\uc778\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
            style={"color": "#64748b", "fontSize": "13px", "marginBottom": "24px"}
        ),
        dbc.Row([
            _strategy_card(
                "SEPA",
                "\uc131\uc7a5\uc8fc \uc9c4\uc785\uc810 \ubd84\uc11d",
                "#6366f1",
                "\ub9c8\ud06c \ubbf8\ub108\ube44\ub2c8\uc758 SEPA \uc804\ub7b5\uc744 \uae30\ubc18\uc73c\ub85c "
                "2\ub2e8\uacc4 \uc0c1\uc2b9\uad6d\uba74\uc758 \uc885\ubaa9\uc744 \ud544\ud130\ub9c1\ud558\uace0 "
                "\uc9c0\uc9c0\ub77c\uc778 \ucef4\ubc14\uc2a4\uc728 \ud328\ud134\uc5d0\uc11c "
                "\uc800\ub9ac\uc2a4\ud06c \uc9c4\uc785 \ud0c0\uc810\uc744 \uc2a4\uce94\ud569\ub2c8\ub2e4.",
                "/sepa",
                ["VCP", "\uc774\uc911\ubc14\ub2e5", "\ud50c\ub7ab \ubca0\uc774\uc2a4", "\ud53c\ubd07 \uc148\uc5c5"],
            ),
            _strategy_card(
                "VPA",
                "\uac70\ub798\ub7c9 \ud22c\uc790 \ubd84\uc11d",
                "#34d399",
                "\uc560\ub098 \ucfe8\ub9c1\uc758 VPA \uae30\ubc95\uc744 \uae30\ubc18\uc73c\ub85c "
                "\uc138\ub825 \uc8fc\uccb4\uc758 \uc2e4\uc9c8 \ub9e4\uc218\uc138\ub97c \uac10\uc9c0\ud569\ub2c8\ub2e4. "
                "\uc8fc\uac00\uc640 \uac70\ub798\ub7c9\uc758 \uad00\uacc4\ub97c \ubd84\uc11d\ud574 "
                "\uc2a4\ub9c8\ud2b8 \uba38\ub2c8\uc758 \ud589\ub3d9\uc744 \ud3ec\ucc29\ud569\ub2c8\ub2e4.",
                "/vpa",
                ["\uc2a4\ud1a0\ud551 \ubcfc\ub968", "\uacf5\uae09 \ubd80\uc7ac", "\ud14c\uc2a4\ud305", "\ub178\ub825 vs \uacb0\uacfc"],
            ),
        ]),

        # ── Footer note ───────────────────────────────────────
        html.Div(
            "\uc8fc\uc758: \ubcf8 \uc11c\ube44\uc2a4\ub294 \ud22c\uc790 \uc815\ubcf4 \uc81c\uacf5\uc744 \ubaa9\uc801\uc73c\ub85c \ud558\uba70, "
            "\ud22c\uc790 \uad8c\uc720\uac00 \uc544\ub2d9\ub2c8\ub2e4. \ubaa8\ub4e0 \ud22c\uc790 \ud310\ub2e8\uc740 \ubcf8\uc778\uc774 \uc9c1\uc811 \ud558\uc2dc\uae30 \ubc14\ub78d\ub2c8\ub2e4.",
            style={
                "color": "#374151", "fontSize": "12px",
                "borderTop": "1px solid #21262d",
                "paddingTop": "24px", "marginTop": "40px",
            }
        ),

    ], style={"padding": "40px 48px", "minHeight": "100vh", "background": "#0d1117"})
