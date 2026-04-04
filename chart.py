# -*- coding: utf-8 -*-
import sys
import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from data_fetcher import get_ohlcv
from strategy import (
    check_trend_template, check_vcp, check_double_bottom,
    check_breakout, check_pivot, find_local_minima
)

sys.stdout.reconfigure(encoding="utf-8")


def plot_stock(ticker: str, name: str, days: int = 120):
    df_full = get_ohlcv(ticker, days=250)
    if df_full.empty or len(df_full) < 200:
        print(f"{ticker}: insufficient data")
        return

    close_full = df_full["Close"]
    ma50_full  = close_full.rolling(50).mean()
    ma150_full = close_full.rolling(150).mean()
    ma200_full = close_full.rolling(200).mean()

    df    = df_full.tail(days).copy()
    ma50  = ma50_full.tail(days)
    ma150 = ma150_full.tail(days)
    ma200 = ma200_full.tail(days)

    add_plots = [
        mpf.make_addplot(ma50,  color="#FFD700", width=2.0),
        mpf.make_addplot(ma150, color="#FF8C00", width=2.0),
        mpf.make_addplot(ma200, color="#00FF7F", width=2.5),
    ]

    style = mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        gridstyle="--",
        gridcolor="#2a2a2a",
        facecolor="#0d1117",
        figcolor="#0d1117",
        marketcolors=mpf.make_marketcolors(
            up="#ff3333",
            down="#3399ff",
            edge="inherit",
            wick="inherit",
            volume="inherit",
        ),
        rc={"axes.labelcolor": "white", "xtick.color": "white", "ytick.color": "white"},
    )

    fig, axes = mpf.plot(
        df,
        type="candle",
        style=style,
        title=f"\n[{ticker}]  {name}",
        volume=True,
        addplot=add_plots,
        figsize=(16, 10),
        returnfig=True,
        datetime_format="%y/%m/%d",
    )

    ax = axes[0]
    ax.title.set_color("white")
    ax.title.set_fontsize(14)

    # MA labels at right edge
    xmax = len(df) - 1
    for ma_series, color, label in [
        (ma50,  "#FFD700", "MA50"),
        (ma150, "#FF8C00", "MA150"),
        (ma200, "#00FF7F", "MA200"),
    ]:
        val = ma_series.iloc[-1]
        if pd.isna(val):
            continue
        ax.annotate(
            f"{label}  {int(val):,}",
            xy=(xmax, val),
            xytext=(xmax + 0.8, val),
            color=color, fontsize=8, fontweight="bold", va="center",
        )

    checklist = []
    trend = check_trend_template(df_full)
    vcp   = check_vcp(df_full)
    db    = check_double_bottom(df_full)
    bo    = check_breakout(df_full)
    pv    = check_pivot(df_full)

    # --- Trend Template ---
    if trend:
        checklist.append(("=== SEPA Trend Template ===", None))
        label_map = {
            "price > MA150 & MA200":           "Price > MA150 & MA200",
            "MA150 > MA200":                   "MA150 > MA200",
            "MA200 uptrend":                   "MA200 uptrend",
            "MA50 > MA150 & MA200":            "MA50 > MA150 & MA200",
            "price > MA50":                    "Price > MA50",
            "price > 52w low +30%":            "Price > 52w Low +30%",
            "price within 25% of 52w high":    "Price within 25% of 52w High",
        }
        for key, ok in trend["conditions"].items():
            checklist.append((label_map.get(key, key), ok))

        ax.axhline(y=trend["52w_high"], color="#666666", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.axhline(y=trend["52w_low"],  color="#666666", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.text(1, trend["52w_high"], f"52w H {trend['52w_high']:,}", color="#999999", fontsize=7, va="bottom")
        ax.text(1, trend["52w_low"],  f"52w L {trend['52w_low']:,}",  color="#999999", fontsize=7, va="top")

    # --- VCP ---
    if vcp:
        checklist.append(("=== VCP Pattern ===", None))
        checklist.append(("Volatility contraction detected", True))
        checklist.append((f"Range: {vcp['range1']} > {vcp['range2']} > {vcp['range3']}", True))
        checklist.append((f"Volume contracting: {vcp['vol_contraction']}", vcp["vol_contraction"]))

        data60 = df_full.tail(60).reset_index(drop=True)
        period = len(data60) // 3
        offset = max(0, len(df) - 60)
        for i in range(1, 3):
            xpos = offset + i * period
            ax.axvline(x=xpos, color="#8888ff", linewidth=1.0, linestyle=":", alpha=0.7)
            ax.text(xpos + 0.3, ax.get_ylim()[1], f"S{i+1}", color="#8888ff", fontsize=7, va="top")

    # --- Double Bottom ---
    if db:
        checklist.append(("=== Double Bottom ===", None))
        checklist.append((f"Bottom 1: {db['bottom1']:,}", True))
        checklist.append((f"Bottom 2: {db['bottom2']:,}", True))
        checklist.append((f"Neckline: {db['neckline']:,}  ({db['dist_from_neckline']})", True))

        data60  = df_full.tail(60).reset_index(drop=True)
        close60 = data60["Close"]
        minima  = find_local_minima(close60, window=6)
        offset  = max(0, len(df) - 60)

        if len(minima) >= 2:
            b1_idx, b1_price = minima[-2]
            b2_idx, b2_price = minima[-1]
            neckline = close60.iloc[b1_idx:b2_idx + 1].max()

            ax.annotate(f"B1\n{int(b1_price):,}",
                        xy=(offset + b1_idx, b1_price),
                        xytext=(offset + b1_idx - 4, b1_price * 0.94),
                        color="#ff6666", fontsize=8, fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color="#ff6666", lw=1.5))
            ax.annotate(f"B2\n{int(b2_price):,}",
                        xy=(offset + b2_idx, b2_price),
                        xytext=(offset + b2_idx + 2, b2_price * 0.94),
                        color="#ff9944", fontsize=8, fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color="#ff9944", lw=1.5))
            ax.axhline(y=neckline, color="#00ffcc", linewidth=1.5, linestyle="--", alpha=0.9)
            ax.text(len(df) - 1, neckline * 1.004,
                    f"Neckline  {int(neckline):,}",
                    color="#00ffcc", fontsize=8, fontweight="bold", ha="right", va="bottom")

    # --- Flat Base Breakout ---
    if bo:
        checklist.append(("=== Flat Base Breakout ===", None))
        checklist.append((f"Box range: {bo['box_range']}  (< 15%)", True))
        checklist.append((f"Breakout: {bo['breakout']} above box high", True))
        checklist.append((f"Volume: {bo['vol_ratio']}  (> 1.5x)", True))
        checklist.append((f"Pre-pivot vol dry-up: {bo['pivot_dryup']}", bo["pivot_dryup"]))

        ax.axhline(y=bo["box_high"], color="#FFD700", linewidth=1.5, linestyle="--", alpha=0.9)
        ax.text(1, bo["box_high"] * 1.004,
                f"Box High  {bo['box_high']:,}", color="#FFD700", fontsize=8, fontweight="bold", va="bottom")

    # --- Pivot Setup ---
    if pv:
        checklist.append(("=== Pivot Setup ===", None))
        checklist.append((f"Pivot: {pv['pivot_price']:,}  ({pv['distance']})", True))
        checklist.append((f"Vol dry-up: {pv['vol_dryup']}", True))

        ax.axhline(y=pv["pivot_price"], color="#ff88ff", linewidth=1.5, linestyle="--", alpha=0.9)
        ax.text(len(df) - 1, pv["pivot_price"] * 1.004,
                f"Pivot  {pv['pivot_price']:,}",
                color="#ff88ff", fontsize=8, fontweight="bold", ha="right", va="bottom")

    # --- Right panel checklist ---
    fig.text(0.905, 0.90, "[ SEPA Checklist ]",
             color="white", fontsize=10, fontweight="bold",
             transform=fig.transFigure, ha="left")
    y = 0.84
    for label, passed in checklist:
        if passed is None:
            fig.text(0.905, y, label, color="#66aaff", fontsize=8, fontweight="bold",
                     transform=fig.transFigure, ha="left")
        else:
            color  = "#44ff88" if passed else "#ff4444"
            symbol = "[+]" if passed else "[-]"
            fig.text(0.905, y, f"{symbol} {label}", color=color, fontsize=7.5,
                     transform=fig.transFigure, ha="left")
        y -= 0.045

    # --- Bottom explanation panel ---
    reason = _build_reason(ticker, trend, vcp, db, bo, pv, df_full)
    fig.text(
        0.01, 0.005, reason,
        color="#cccccc", fontsize=8,
        transform=fig.transFigure, ha="left", va="bottom",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#111827", edgecolor="#334155", alpha=0.95),
    )

    plt.subplots_adjust(right=0.89, bottom=0.20)
    plt.show()


def _build_reason(ticker, trend, vcp, db, bo, pv, df_full) -> str:
    close    = df_full["Close"]
    cur      = close.iloc[-1]
    high_52w = close.tail(252).max()
    low_52w  = close.tail(252).min()
    avg_vol  = df_full["Volume"].iloc[-20:].mean()
    last_vol = df_full["Volume"].iloc[-1]

    lines = []
    lines.append(
        f"WHY [{ticker}] WAS SELECTED"
        f"  |  Price: {int(cur):,}"
        f"  |  52w High: {int(high_52w):,}  Low: {int(low_52w):,}"
        f"  |  Today vol: {last_vol/avg_vol:.1f}x 20d avg"
    )

    if trend:
        s = trend["passed"]
        lines.append(
            f"[Trend] Stage 2 confirmed ({s}/7) "
            f"-- MA50:{trend['ma50']:,}  MA150:{trend['ma150']:,}  MA200:{trend['ma200']:,} "
            f"(slope {trend['slope_200']:+.2f}%/20d)"
        )

    if vcp:
        lines.append(
            f"[VCP]  Price range shrinking {vcp['range1']} -> {vcp['range2']} -> {vcp['range3']}"
            f" -- sellers running out, stock coiling up before breakout"
        )

    if db:
        lines.append(
            f"[Double Bottom]  Buyers defended {db['bottom1']:,} twice"
            f" -- neckline breakout at {db['neckline']:,} triggers entry  "
            f"(currently {db['dist_from_neckline']} from neckline)"
        )

    if bo:
        lines.append(
            f"[Breakout]  Broke above {bo['box_high']:,} with {bo['vol_ratio']} volume"
            f" after tight {bo['box_range']} consolidation -- institutional accumulation signal"
        )

    if pv:
        lines.append(
            f"[Pivot]  Sitting {pv['distance']} from pivot {pv['pivot_price']:,}"
            f" -- volume drying up ({pv['vol_dryup']}), low-risk entry zone forming"
        )

    return "\n".join(lines)
