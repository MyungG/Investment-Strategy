import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_fetcher import get_ohlcv
from strategy import (
    check_trend_template, check_vcp, check_double_bottom,
    check_breakout, check_pivot, find_local_minima
)


BG = "#0d1117"
GRID = "#1e2530"


def build_chart(ticker: str, name: str, days: int = 120) -> go.Figure:
    df_full = get_ohlcv(ticker, days=250)
    if df_full.empty or len(df_full) < 200:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG,
                          font_color="white",
                          annotations=[dict(text="No data", showarrow=False,
                                            font=dict(size=20, color="white"))])
        return fig

    close_full = df_full["Close"]
    ma50_full  = close_full.rolling(50).mean()
    ma150_full = close_full.rolling(150).mean()
    ma200_full = close_full.rolling(200).mean()

    df    = df_full.tail(days).copy()
    ma50  = ma50_full.tail(days)
    ma150 = ma150_full.tail(days)
    ma200 = ma200_full.tail(days)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.02,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#ff3333"), fillcolor="#ff3333"),
        decreasing=dict(line=dict(color="#3399ff"), fillcolor="#3399ff"),
        name="Price",
        showlegend=False,
    ), row=1, col=1)

    # Moving averages
    for ma, color, label in [
        (ma50,  "#FFD700", "MA50"),
        (ma150, "#FF8C00", "MA150"),
        (ma200, "#00FF7F", "MA200"),
    ]:
        fig.add_trace(go.Scatter(
            x=df.index, y=ma,
            line=dict(color=color, width=1.8),
            name=label, hovertemplate=f"{label}: %{{y:,.0f}}<extra></extra>",
        ), row=1, col=1)

    # Volume bars
    colors = ["#ff3333" if c >= o else "#3399ff"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=colors, opacity=0.7,
        name="Volume", showlegend=False,
        hovertemplate="Vol: %{y:,.0f}<extra></extra>",
    ), row=2, col=1)

    # Pattern overlays
    trend = check_trend_template(df_full)
    db    = check_double_bottom(df_full)
    bo    = check_breakout(df_full)
    pv    = check_pivot(df_full)
    vcp   = check_vcp(df_full)

    # 52w high / low
    if trend:
        for val, label, color in [
            (trend["52w_high"], f"52w High {trend['52w_high']:,}", "#555555"),
            (trend["52w_low"],  f"52w Low {trend['52w_low']:,}",  "#555555"),
        ]:
            fig.add_hline(y=val, line=dict(color=color, width=1, dash="dot"),
                          opacity=0.5, row=1, col=1,
                          annotation_text=label,
                          annotation_font=dict(color="#777777", size=10),
                          annotation_position="bottom right")

    # Double Bottom
    if db:
        data60  = df_full.tail(60).reset_index(drop=True)
        close60 = data60["Close"]
        minima  = find_local_minima(close60, window=6)
        offset  = max(0, len(df) - 60)

        if len(minima) >= 2:
            b1_idx, b1_price = minima[-2]
            b2_idx, b2_price = minima[-1]
            neckline = close60.iloc[b1_idx:b2_idx + 1].max()
            dates = df.index.tolist()

            for idx, price, label, color in [
                (b1_idx, b1_price, "B1", "#ff6666"),
                (b2_idx, b2_price, "B2", "#ff9944"),
            ]:
                di = min(offset + idx, len(dates) - 1)
                fig.add_annotation(
                    x=dates[di], y=price * 0.96,
                    text=f"<b>{label}</b><br>{price:,}",
                    showarrow=True, arrowhead=2,
                    arrowcolor=color, font=dict(color=color, size=10),
                    ax=0, ay=30, row=1, col=1,
                )

            fig.add_hline(y=neckline, line=dict(color="#00ffcc", width=1.5, dash="dash"),
                          row=1, col=1,
                          annotation_text=f"Neckline {int(neckline):,}",
                          annotation_font=dict(color="#00ffcc", size=10),
                          annotation_position="top right")

    # Flat Base Breakout
    if bo:
        fig.add_hline(y=bo["box_high"],
                      line=dict(color="#FFD700", width=1.5, dash="dash"),
                      row=1, col=1,
                      annotation_text=f"Box High {bo['box_high']:,}",
                      annotation_font=dict(color="#FFD700", size=10),
                      annotation_position="top left")

    # Pivot
    if pv:
        fig.add_hline(y=pv["pivot_price"],
                      line=dict(color="#ff88ff", width=1.5, dash="dash"),
                      row=1, col=1,
                      annotation_text=f"Pivot {pv['pivot_price']:,}",
                      annotation_font=dict(color="#ff88ff", size=10),
                      annotation_position="top right")

    fig.update_layout(
        title=dict(text=f"<b>{name}  ({ticker})</b>",
                   font=dict(color="white", size=16), x=0.01),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color="white"),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=10, r=10, t=50, b=10),
        height=500,
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=GRID, showgrid=True)
    fig.update_yaxes(gridcolor=GRID, showgrid=True)

    return fig
