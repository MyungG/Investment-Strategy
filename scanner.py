import sys
import time
import pandas as pd
from datetime import datetime
from data_fetcher import get_stock_list, get_ohlcv
from strategy import analyze_stock
from chart import plot_stock

sys.stdout.reconfigure(encoding="utf-8")


def run_scan():
    print("=" * 65)
    print("  SEPA Pattern Scanner  (KOSPI + KOSDAQ)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    print("\nLoading stock list...")
    stock_list = get_stock_list()
    total = len(stock_list)
    print(f"Total: {total} stocks\n")
    print("Scanning...\n")

    results = []
    errors  = 0

    for i, row in enumerate(stock_list.itertuples(), 1):
        ticker = row.ticker
        name   = row.name
        market = row.market

        print(f"[{i:4d}/{total}] {ticker} ...", end="\r")

        try:
            df = get_ohlcv(ticker, days=250)
            result = analyze_stock(df, ticker, name)
            if result:
                result["market"] = market
                results.append(result)
                print(f"\n  >> [{market}] {ticker} | {result['pattern']}")
        except Exception as e:
            errors += 1

        time.sleep(0.05)

    # ── 결과 출력 ──────────────────────────────────────────
    print("\n" + "=" * 65)
    print(f"  Done | {total} stocks scanned | {len(results)} signals | {errors} errors")
    print("=" * 65)

    if not results:
        print("\nNo signals found.")
        return

    df_result = pd.DataFrame(results)

    # 패턴별 그룹 출력
    for pattern_type in ["VCP", "Double Bottom", "Flat Base Breakout", "Pivot Setup"]:
        subset = df_result[df_result["pattern"].str.contains(pattern_type)]
        if subset.empty:
            continue
        print(f"\n[ {pattern_type} — {len(subset)} stocks ]")
        print("-" * 65)
        cols = ["market", "ticker", "name", "price", "vs_ma50", "vol_ratio", "trend_score", "pattern"]
        print(subset[cols].to_string(index=False))

    # CSV 저장
    filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df_result.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {filename}")

    # 차트 자동 표시
    print(f"\nShowing charts for {len(results)} signal stocks...")
    for r in results:
        print(f"  -> {r['name']} ({r['ticker']})  [{r['pattern']}]")
        plot_stock(r["ticker"], r["name"], days=120)


if __name__ == "__main__":
    run_scan()
