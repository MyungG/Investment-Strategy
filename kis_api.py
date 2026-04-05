# -*- coding: utf-8 -*-
import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

APP_KEY    = os.getenv("KIS_APP_KEY", "")
APP_SECRET = os.getenv("KIS_APP_SECRET", "")
IS_REAL    = os.getenv("KIS_IS_REAL", "true").lower() == "true"

BASE_URL = (
    "https://openapi.koreainvestment.com:9443"
    if IS_REAL else
    "https://openapivts.koreainvestment.com:29443"
)

# ── Token 관리 (파일 캐시) ────────────────────────────────
_TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".kis_token.json")


def get_token() -> str:
    now = time.time()

    # 파일 캐시 확인
    if os.path.exists(_TOKEN_FILE):
        try:
            with open(_TOKEN_FILE, "r") as f:
                cache = json.load(f)
            if cache.get("token") and now < cache.get("expires_at", 0):
                return cache["token"]
        except Exception:
            pass

    # 새 토큰 발급
    r = requests.post(
        f"{BASE_URL}/oauth2/tokenP",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
        }),
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    token = data["access_token"]
    expires_at = now + data.get("expires_in", 86400) - 300  # 5분 여유

    with open(_TOKEN_FILE, "w") as f:
        json.dump({"token": token, "expires_at": expires_at}, f)

    return token


def _headers(tr_id: str) -> dict:
    return {
        "Content-Type": "application/json",
        "authorization": f"Bearer {get_token()}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }


def _get(path: str, tr_id: str, params: dict) -> dict:
    r = requests.get(
        f"{BASE_URL}{path}",
        headers=_headers(tr_id),
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


# ── 투자자 순매수 캐시 ────────────────────────────────────
_INVESTOR_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".kis_investor_cache.json")


def _load_investor_cache() -> dict:
    """캐시 파일 로드. 없으면 빈 dict 반환."""
    try:
        with open(_INVESTOR_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_investor_cache(key: str, data: list) -> None:
    """캐시에 key별 데이터와 저장 시각 기록."""
    cache = _load_investor_cache()
    cache[key] = {
        "data": data,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(_INVESTOR_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


# ── 종목별 투자자 순매수 ──────────────────────────────────

def get_investor_by_stock(ticker: str) -> dict | None:
    """
    특정 종목의 최근 1일(전일 기준) 외국인·기관 순매수량/순매수금액 반환.
    TR: FHKST01010900 — 장외에도 전일 데이터 제공.
    """
    try:
        data = _get(
            "/uapi/domestic-stock/v1/quotations/inquire-investor",
            tr_id="FHKST01010900",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": ticker,
            },
        )
        rows = data.get("output", [])
        if not rows:
            return None
        latest = rows[0]   # 가장 최근 거래일
        return {
            "ticker":        ticker,
            "date":          latest.get("stck_bsop_date", ""),
            "close":         latest.get("stck_clpr", "0"),
            "frgn_ntby_qty": int(latest.get("frgn_ntby_qty", "0") or "0"),
            "orgn_ntby_qty": int(latest.get("orgn_ntby_qty", "0") or "0"),
            "frgn_ntby_amt": int(latest.get("frgn_ntby_tr_pbmn", "0") or "0"),
            "orgn_ntby_amt": int(latest.get("orgn_ntby_tr_pbmn", "0") or "0"),
        }
    except Exception:
        return None


# ── 외국인/기관 순매수 상위 ────────────────────────────────

def get_investor_net_buy(market: str = "J", investor: str = "FRG", top: int = 10) -> tuple[list[dict], str]:
    """
    외국인/기관 순매수 상위 종목 (장중에만 실시간, 장외엔 마지막 캐시 반환)
    market:   J=전체(주식+ETF), W=ELW
    investor: FRG=외국인, ORG=기관합계
    반환: (데이터 리스트, 기준시각 문자열)
    """
    cache_key = f"{investor}_{market}"

    try:
        data = _get(
            "/uapi/domestic-stock/v1/quotations/foreign-institution-total",
            tr_id="FHPST02320000",
            params={
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20171",
                "fid_input_iscd": "0000",
                "fid_div_cls_code": "0",
                "fid_blng_cls_code": investor,
                "fid_trgt_cls_code": "0",
                "fid_trgt_exls_cls_code": "0",
                "fid_input_price_1": "",
                "fid_input_price_2": "",
                "fid_vol_cnt": "",
            },
        )
        result = data.get("output2", [])[:top]
    except Exception:
        result = []

    if result:
        _save_investor_cache(cache_key, result)
        return result, datetime.now().strftime("%Y-%m-%d %H:%M")

    # 장외 시간 → 캐시 반환
    cache = _load_investor_cache()
    entry = cache.get(cache_key, {})
    return entry.get("data", [])[:top], entry.get("saved_at", "")


# ── 거래량 순위 ────────────────────────────────────────────

def get_volume_ranking_split(top: int = 20) -> tuple[list[dict], list[dict]]:
    """
    KOSPI / KOSDAQ 각각 거래량 상위 top종목 반환.
    FDR StockListing(당일 스냅샷)의 Volume 컬럼 사용.
    반환: (kospi_top, kosdaq_top)
    """
    import FinanceDataReader as fdr

    def _to_rows(market_name: str) -> list[dict]:
        df = fdr.StockListing(market_name)[
            ["Code", "Name", "Close", "Changes", "ChagesRatio", "Volume"]
        ].dropna(subset=["Volume"])
        df = df[df["Volume"] > 0].sort_values("Volume", ascending=False).head(top)
        rows = []
        for _, r in df.iterrows():
            sign = "2" if r["Changes"] > 0 else ("5" if r["Changes"] < 0 else "3")
            rows.append({
                "hts_kor_isnm":   r["Name"],
                "mksc_shrn_iscd": str(r["Code"]).zfill(6),
                "stck_prpr":      str(int(r["Close"])),
                "prdy_vrss_sign": sign,
                "prdy_ctrt":      f"{r['ChagesRatio']:.2f}",
                "acml_vol":       str(int(r["Volume"])),
            })
        return rows

    return _to_rows("KOSPI"), _to_rows("KOSDAQ")


def get_volume_ranking(market: str = "J", top: int = 10) -> list[dict]:
    """
    거래량 순위
    market: J=전체(주식+ETF), W=ELW
    """
    data = _get(
        "/uapi/domestic-stock/v1/quotations/volume-rank",
        tr_id="FHPST01710000",
        params={
            "fid_cond_mrkt_div_code": market,
            "fid_cond_scr_div_code": "20171",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_blng_cls_code": "0",
            "fid_trgt_cls_code": "111111111",
            "fid_trgt_exls_cls_code": "000000",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_input_date_1": "",
        },
    )
    return data.get("output", [])[:top]


# ── 전일 기준 외국인/기관 순매수 랭킹 빌더 ─────────────────
_RANKING_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".kis_ranking_cache.json")


def build_investor_ranking(n: int = 100, top: int = 20) -> None:
    """
    KOSPI/KOSDAQ 각 시가총액 상위 n종목의 전일 투자자 순매수를 계산해 캐시 저장.
    장외 시간에도 동작 (inquire-investor는 전일 데이터 제공).
    ~n*2 * 0.15초 소요 (각 100종목 ≈ 30초).
    """
    import FinanceDataReader as fdr

    def _scan(market_name: str) -> list[dict]:
        df = fdr.StockListing(market_name)[["Code", "Name", "Marcap"]].dropna(subset=["Marcap"])
        df = df.sort_values("Marcap", ascending=False).head(n)
        rows = []
        for _, row in df.iterrows():
            ticker = str(row["Code"]).zfill(6)
            inv = get_investor_by_stock(ticker)
            if inv:
                inv["name"]   = row["Name"]
                inv["market"] = market_name
                rows.append(inv)
            time.sleep(0.15)
        return rows

    def _rank(items: list, key: str, top: int) -> tuple[list, list]:
        s = sorted(items, key=lambda x: x[key], reverse=True)
        return s[:top], s[-top:][::-1]

    print("  KOSPI 스캔 중...")
    kospi  = _scan("KOSPI")
    print("  KOSDAQ 스캔 중...")
    kosdaq = _scan("KOSDAQ")

    if not kospi and not kosdaq:
        return

    scan_date = (kospi or kosdaq)[0]["date"]

    frg_kp_buy,  frg_kp_sell  = _rank(kospi,  "frgn_ntby_qty", top)
    frg_kq_buy,  frg_kq_sell  = _rank(kosdaq, "frgn_ntby_qty", top)
    org_kp_buy,  org_kp_sell  = _rank(kospi,  "orgn_ntby_qty", top)
    org_kq_buy,  org_kq_sell  = _rank(kosdaq, "orgn_ntby_qty", top)

    cache = {
        "scan_date":       scan_date,
        "saved_at":        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "FRG_KOSPI_BUY":   frg_kp_buy,
        "FRG_KOSPI_SELL":  frg_kp_sell,
        "FRG_KOSDAQ_BUY":  frg_kq_buy,
        "FRG_KOSDAQ_SELL": frg_kq_sell,
        "ORG_KOSPI_BUY":   org_kp_buy,
        "ORG_KOSPI_SELL":  org_kp_sell,
        "ORG_KOSDAQ_BUY":  org_kq_buy,
        "ORG_KOSDAQ_SELL": org_kq_sell,
    }
    with open(_RANKING_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"Saved: {_RANKING_CACHE_FILE}  (KOSPI {len(kospi)} + KOSDAQ {len(kosdaq)} stocks, date={scan_date})")


def load_investor_ranking() -> dict:
    """캐시에서 외국인/기관 순매수 랭킹 로드. 없으면 빈 dict."""
    try:
        with open(_RANKING_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── 코스피/코스닥 지수 ─────────────────────────────────────

def get_index_data() -> list[dict]:
    """
    KOSPI(KS11), KOSDAQ(KQ11) 지수 반환.
    반환: [{"name": ..., "close": ..., "change": ..., "chg_rate": ...}, ...]
    """
    import FinanceDataReader as fdr
    from datetime import date, timedelta

    result = []
    indices = [("KOSPI", "KS11"), ("KOSDAQ", "KQ11")]
    start = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    for name, code in indices:
        try:
            df = fdr.DataReader(code, start).dropna(subset=["Close"])
            if df.empty:
                continue
            row      = df.iloc[-1]
            close    = float(row["Close"])
            comp     = float(row["Comp"])
            chg_rate = float(row["Change"]) * 100
            result.append({
                "name":     name,
                "close":    close,
                "change":   comp,
                "chg_rate": chg_rate,
                "dates":    df.index.strftime("%Y-%m-%d").tolist(),
                "closes":   df["Close"].tolist(),
                "opens":    df["Open"].tolist(),
                "highs":    df["High"].tolist(),
                "lows":     df["Low"].tolist(),
            })
        except Exception:
            pass
    return result


# ── 간단한 메모리 캐시 ────────────────────────────────────
_cache: dict = {}
_CACHE_TTL = 300  # 5분


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


# ── 해외 지수/환율/원자재 ──────────────────────────────────

def get_overseas_data() -> list[dict]:
    """
    미국 3대 지수, 닛케이, USD/KRW, WTI, 금 반환.
    반환: [{"name":..., "close":..., "change":..., "chg_rate":..., "dates":[], "closes":[]}, ...]
    """
    cached = _cache_get("overseas")
    if cached is not None:
        return cached

    import FinanceDataReader as fdr
    from datetime import date, timedelta
    from concurrent.futures import ThreadPoolExecutor

    targets = [
        ("S&P 500",     "^GSPC"),
        ("NASDAQ 100",  "QQQ"),
        ("DOW",         "DJI"),
        ("Nikkei225",   "JP.NIKKEI"),
        ("USD/KRW",     "USD/KRW"),
        ("WTI",         "CL=F"),
        ("Gold",        "GC=F"),
        ("VIX",         "VIX"),
        ("DXY",         "DX=F"),
        ("US 10Y",      "^TNX"),
    ]
    start = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    def _fetch(name, code):
        try:
            df = fdr.DataReader(code, start).dropna(subset=["Close"])
            if len(df) < 2:
                return None
            close = float(df["Close"].iloc[-1])
            prev  = float(df["Close"].iloc[-2])
            if name == "US 10Y":
                close /= 10
                prev  /= 10
            change   = close - prev
            chg_rate = (change / prev * 100) if prev else 0.0
            return {
                "name":     name,
                "close":    close,
                "change":   change,
                "chg_rate": chg_rate,
                "dates":    df.index.strftime("%Y-%m-%d").tolist(),
                "closes":   [v / 10 if name == "US 10Y" else v
                             for v in df["Close"].tolist()],
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(_fetch, name, code) for name, code in targets]

    order = {name: i for i, (name, _) in enumerate(targets)}
    result = sorted(
        [f.result() for f in futures if f.result() is not None],
        key=lambda x: order.get(x["name"], 99),
    )
    _cache_set("overseas", result)
    return result


# ── 미국 섹터 성과 ────────────────────────────────────────

_GICS_SECTORS = {
    "Technology":       ["AAPL", "MSFT", "NVDA", "AVGO", "AMD", "ORCL", "CRM", "ADBE", "TXN", "QCOM"],
    "Healthcare":       ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "AMGN", "PFE", "ISRG"],
    "Financials":       ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "AXP", "SPGI"],
    "Comm. Services":   ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS"],
    "Cons. Discret.":   ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG"],
    "Industrials":      ["GE", "CAT", "HON", "UNP", "RTX", "BA", "LMT", "DE", "ETN", "FDX"],
    "Energy":           ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO", "OXY"],
    "Cons. Staples":    ["PG", "COST", "WMT", "KO", "PEP", "PM", "MDLZ", "CL"],
    "Materials":        ["LIN", "APD", "ECL", "NEM", "FCX", "NUE", "ALB"],
    "Real Estate":      ["PLD", "AMT", "EQIX", "PSA", "WELL", "SPG", "O"],
    "Utilities":        ["NEE", "SO", "DUK", "AEP", "EXC", "SRE", "D"],
}


def get_sector_data() -> list[dict]:
    """
    GICS 11개 섹터 + 개별 종목 등락률 반환 (yfinance 배치).
    반환: [{"name":..., "avg_chg":..., "stocks":[{"ticker":..,"chg_rate":..}, ...]}, ...]
    """
    cached = _cache_get("sectors")
    if cached is not None:
        return cached

    import yfinance as yf

    all_tickers = [t for stocks in _GICS_SECTORS.values() for t in stocks]
    chg_rates   = {t: 0.0 for t in all_tickers}

    try:
        raw = yf.download(all_tickers, period="2d", progress=False, auto_adjust=True)
        closes = raw["Close"] if "Close" in raw else raw
        for ticker in all_tickers:
            try:
                col    = closes[ticker] if ticker in closes.columns else closes
                series = col.dropna()
                if len(series) >= 2:
                    prev = float(series.iloc[-2])
                    curr = float(series.iloc[-1])
                    chg_rates[ticker] = (curr - prev) / prev * 100 if prev else 0.0
            except Exception:
                pass
    except Exception:
        pass

    result = []
    for sector_name, tickers in _GICS_SECTORS.items():
        stocks = [{"ticker": t, "chg_rate": chg_rates.get(t, 0.0)} for t in tickers]
        avg    = sum(s["chg_rate"] for s in stocks) / len(stocks) if stocks else 0.0
        result.append({"name": sector_name, "avg_chg": avg, "stocks": stocks})

    result = sorted(result, key=lambda x: x["avg_chg"], reverse=True)
    _cache_set("sectors", result)
    return result


# ── CNN 공포탐욕 지수 ──────────────────────────────────────

def get_fear_greed() -> dict:
    """
    CNN Fear & Greed Index 반환.
    반환: {"score": int, "rating": str, "prev_close": int}
    """
    try:
        r = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        fg   = data["fear_and_greed"]
        return {
            "score":      round(float(fg["score"])),
            "rating":     fg["rating"],
            "prev_close": round(float(fg.get("previous_close", fg["score"]))),
        }
    except Exception:
        return {}

