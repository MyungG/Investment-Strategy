# -*- coding: utf-8 -*-
"""
vpa_scanner.py

Anna Coulling VPA (Volume Price Analysis) \uc804\uccb4 \uc885\ubaa9 \uc2a4\uce94.
\uc2e4\ud589:
    python vpa_scanner.py

\uacb0\uacfc: vpa_signals_YYYYMMDD_HHMM.csv \uc800\uc7a5
"""
import sys
import pandas as pd
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

from data_fetcher import get_stock_list, get_ohlcv
from strategy import scan_vpa


def main():
    print("=" * 55)
    print("  VPA Scanner  (Anna Coulling Volume Price Analysis)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    stocks = get_stock_list()
    print(f"\n\uc804\uccb4 {len(stocks)}\uc885\ubaa9 \uc2a4\uce94 \uc2dc\uc791...\n")

    results = []
    for i, row in enumerate(stocks.itertuples(), 1):
        ticker = row.ticker
        name   = row.name
        if i % 100 == 0:
            print(f"  {i}/{len(stocks)} \uc644\ub8cc...")
        try:
            df = get_ohlcv(ticker, days=120)
            if df.empty:
                continue
            result = scan_vpa(df, ticker, name)
            if result:
                results.append(result)
        except Exception:
            continue

    if not results:
        print("\n\uc2e0\ud638 \uc5c6\uc74c.")
        return

    df_out = pd.DataFrame(results)
    fname  = datetime.now().strftime("vpa_signals_%Y%m%d_%H%M.csv")
    df_out.to_csv(fname, index=False, encoding="utf-8-sig")

    print(f"\n\uc644\ub8cc! {len(results)}\uc885\ubaa9 \uac10\uc9c0")
    print(f"\uc800\uc7a5: {fname}")
    print("\nTop 10:")
    for _, r in df_out.head(10).iterrows():
        print(f"  {r['ticker']} {r['name']:10s}  {r['pattern']:20s}  vol {r['vol_ratio']}")


if __name__ == "__main__":
    main()
