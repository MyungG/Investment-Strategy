import pandas as pd
import numpy as np


# ─────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────

def find_local_minima(series: pd.Series, window: int = 8) -> list[tuple[int, float]]:
    arr = series.values
    result = []
    for i in range(window, len(arr) - window):
        if arr[i] == arr[i - window:i + window + 1].min():
            result.append((i, arr[i]))
    return result


def find_local_maxima(series: pd.Series, window: int = 8) -> list[tuple[int, float]]:
    arr = series.values
    result = []
    for i in range(window, len(arr) - window):
        if arr[i] == arr[i - window:i + window + 1].max():
            result.append((i, arr[i]))
    return result


def ma_slope(series: pd.Series, window: int = 20) -> float:
    """최근 window일 간 이동평균선 기울기 (% / 일)"""
    ma = series.rolling(20).mean()
    recent = ma.dropna().tail(window)
    if len(recent) < 2:
        return 0.0
    return (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100


# ─────────────────────────────────────────
# 1차 필터: 세파 트렌드 템플릿 (Stage 2)
# ─────────────────────────────────────────

def check_trend_template(df: pd.DataFrame) -> dict | None:
    """
    세파 2단계 트렌드 템플릿 7가지 조건:
    1. 현재가 > 150MA and 200MA
    2. 150MA > 200MA
    3. 200MA가 상승 기울기 (최소 1개월)
    4. 50MA > 150MA and 200MA
    5. 현재가 > 50MA
    6. 현재가 > 52주 저점 * 1.30 (30% 이상 위)
    7. 현재가 > 52주 고점 * 0.75 (고점의 25% 이내)
    """
    if len(df) < 200:
        return None

    close = df["Close"]
    cur   = close.iloc[-1]

    ma50  = close.rolling(50).mean().iloc[-1]
    ma150 = close.rolling(150).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]

    low_52w  = close.tail(252).min()
    high_52w = close.tail(252).max()

    # 200MA 기울기: 최근 20일 기준
    slope_200 = ma_slope(close, window=20)

    conditions = {
        "price > MA150 & MA200": cur > ma150 and cur > ma200,
        "MA150 > MA200":         ma150 > ma200,
        "MA200 uptrend":         slope_200 > 0,
        "MA50 > MA150 & MA200":  ma50 > ma150 and ma50 > ma200,
        "price > MA50":          cur > ma50,
        "price > 52w low +30%":  cur > low_52w * 1.30,
        "price within 25% of 52w high": cur > high_52w * 0.75,
    }

    passed = sum(conditions.values())
    if passed < 6:  # 7개 중 6개 이상 통과
        return None

    return {
        "conditions": conditions,
        "passed": passed,
        "ma50":  round(ma50),
        "ma150": round(ma150),
        "ma200": round(ma200),
        "52w_low":  round(low_52w),
        "52w_high": round(high_52w),
        "slope_200": round(slope_200, 2),
    }


def check_min_volume(df: pd.DataFrame, min_vol: int = 100_000) -> bool:
    return df["Volume"].iloc[-20:].mean() >= min_vol


# ─────────────────────────────────────────
# 패턴 1: VCP (Volatility Contraction Pattern)
# ─────────────────────────────────────────

def check_vcp(df: pd.DataFrame) -> dict | None:
    """
    세파 VCP:
    - 최근 60일에서 2~4번의 변동성 축소
    - 각 축소폭이 이전보다 최소 1/3 이상 줄어야 함
    - 마지막 축소폭이 10% 미만 (타이트한 수렴)
    - 거래량 감소
    - 현재가가 60일 고점의 85% 이상
    """
    data = df.tail(60).reset_index(drop=True)
    if len(data) < 45:
        return None

    close  = data["Close"]
    high   = data["High"]
    low    = data["Low"]
    volume = data["Volume"]

    # 로컬 고점 찾기
    maxima = find_local_maxima(close, window=5)
    minima = find_local_minima(close, window=5)

    if len(maxima) < 2 or len(minima) < 2:
        return None

    # 고점-저점 쌍으로 축소폭 계산
    contractions = []
    for i in range(min(len(maxima), len(minima), 4)):
        if i < len(maxima) and i < len(minima):
            peak = maxima[i][1]
            trough_idx = minima[i][0] if minima[i][0] > maxima[i][0] else (minima[i+1][1] if i+1 < len(minima) else None)
            if trough_idx is None:
                continue
            trough = minima[i][1] if minima[i][0] > maxima[i][0] else (minima[i+1][1] if i+1 < len(minima) else peak)
            contraction = (peak - trough) / peak * 100
            contractions.append(round(contraction, 1))

    # 단순화: 3구간 분할로 변동폭 계산
    period = len(data) // 3
    ranges = []
    vol_avgs = []
    for i in range(3):
        chunk = data.iloc[i * period:(i + 1) * period]
        h = chunk["High"].max()
        l = chunk["Low"].min()
        mid = chunk["Close"].mean()
        ranges.append((h - l) / mid * 100)
        vol_avgs.append(chunk["Volume"].mean())

    # 변동폭 수축 확인
    if not (ranges[0] > ranges[1] > ranges[2]):
        return None

    # 마지막 구간 10% 미만
    if ranges[2] >= 10.0:
        return None

    # 각 구간이 이전보다 최소 20% 이상 줄어야 함
    if not (ranges[1] < ranges[0] * 0.8 and ranges[2] < ranges[1] * 0.8):
        return None

    # 거래량 수축 (1구간 > 3구간)
    if vol_avgs[0] <= vol_avgs[2]:
        return None

    # 현재가가 60일 고점의 85% 이상 (상단 위치)
    high_60 = data["High"].max()
    cur = data["Close"].iloc[-1]
    if cur < high_60 * 0.85:
        return None

    return {
        "pattern": "VCP",
        "range1": f"{ranges[0]:.1f}%",
        "range2": f"{ranges[1]:.1f}%",
        "range3": f"{ranges[2]:.1f}%",
        "contraction": f"{ranges[2] / ranges[0] * 100:.0f}% of initial",
        "vol_contraction": vol_avgs[0] > vol_avgs[2],
    }


# ─────────────────────────────────────────
# 패턴 2: 이중바닥 (Double Bottom)
# ─────────────────────────────────────────

def check_double_bottom(df: pd.DataFrame) -> dict | None:
    """
    - 최근 60일 두 개의 저점
    - 두 저점 가격 차이 5% 이내
    - 저점 간격 10~50일
    - 두 번째 저점 거래량 < 첫 번째 (매도세 약화)
    - 현재가가 네크라인 ±3% ~ +5%
    """
    data   = df.tail(60).reset_index(drop=True)
    close  = data["Close"]
    volume = data["Volume"]

    minima = find_local_minima(close, window=6)
    if len(minima) < 2:
        return None

    b1_idx, b1_price = minima[-2]
    b2_idx, b2_price = minima[-1]

    if abs(b1_price - b2_price) / b1_price > 0.05:
        return None

    gap = b2_idx - b1_idx
    if not (10 <= gap <= 50):
        return None

    neckline = close.iloc[b1_idx:b2_idx + 1].max()
    cur      = close.iloc[-1]
    dist     = (cur - neckline) / neckline * 100

    if not (-3.0 <= dist <= 5.0):
        return None

    if volume.iloc[b2_idx] >= volume.iloc[b1_idx] * 1.2:
        return None

    return {
        "pattern": "Double Bottom",
        "bottom1": round(b1_price),
        "bottom2": round(b2_price),
        "neckline": round(neckline),
        "dist_from_neckline": f"{dist:+.1f}%",
    }


# ─────────────────────────────────────────
# 패턴 3: 박스권 돌파 (Flat Base Breakout)
# ─────────────────────────────────────────

def check_breakout(df: pd.DataFrame) -> dict | None:
    """
    세파 플랫 베이스:
    - 20일 횡보 범위 15% 이내
    - 오늘 종가 > 20일 최고가 (돌파)
    - 오늘 거래량 > 20일 평균 * 1.5
    - 돌파 직전 거래량 감소 (피봇 확인)
    """
    if len(df) < 25:
        return None

    box    = df.iloc[-21:-1]
    cur_close  = df["Close"].iloc[-1]
    cur_volume = df["Volume"].iloc[-1]

    box_high  = box["High"].max()
    box_low   = box["Low"].min()
    box_range = (box_high - box_low) / box_low * 100
    avg_vol   = box["Volume"].mean()

    # 박스권 범위 15% 이내
    if box_range > 15.0:
        return None

    # 돌파
    if cur_close <= box_high:
        return None

    # 거래량 확인
    vol_ratio = cur_volume / avg_vol
    if vol_ratio < 1.5:
        return None

    # 피봇 전 거래량 감소 확인 (직전 3일 평균이 20일 평균보다 낮아야)
    pre_pivot_vol = df["Volume"].iloc[-4:-1].mean()
    pivot_dryup   = pre_pivot_vol < avg_vol

    return {
        "pattern": "Flat Base Breakout",
        "box_high":    round(box_high),
        "box_range":   f"{box_range:.1f}%",
        "breakout":    f"{(cur_close - box_high) / box_high * 100:+.1f}%",
        "vol_ratio":   f"{vol_ratio:.1f}x",
        "pivot_dryup": pivot_dryup,
    }


# ─────────────────────────────────────────
# 피봇 지점 감지
# ─────────────────────────────────────────

def check_pivot(df: pd.DataFrame) -> dict | None:
    """
    피봇 지점: 베이스 완성 후 돌파 직전 타이밍
    - 최근 5일 거래량이 평균 이하로 감소 (매도 물량 소진)
    - 현재가가 20일 고점의 98~103% (피봇 근처)
    - 아직 돌파하지 않은 상태
    """
    if len(df) < 25:
        return None

    close     = df["Close"]
    volume    = df["Volume"]
    cur_close = close.iloc[-1]
    avg_vol   = volume.iloc[-21:-1].mean()
    recent_vol = volume.iloc[-5:].mean()
    high_20   = df["High"].iloc[-21:-1].max()

    # 거래량 감소 (피봇 전 dry-up)
    vol_dryup = recent_vol < avg_vol * 0.8

    # 가격이 20일 고점 근처 (98~103%)
    near_pivot = 0.98 <= cur_close / high_20 <= 1.03

    if not (vol_dryup and near_pivot):
        return None

    return {
        "pattern": "Pivot Setup",
        "pivot_price": round(high_20),
        "distance":    f"{(cur_close / high_20 - 1) * 100:+.1f}%",
        "vol_dryup":   f"{recent_vol / avg_vol:.1f}x avg",
    }


# ─────────────────────────────────────────
# 종합 분석
# ─────────────────────────────────────────

def analyze_stock(df: pd.DataFrame, ticker: str, name: str) -> dict | None:
    """
    1차: 세파 트렌드 템플릿 + 최소 거래량
    2차: VCP / 이중바닥 / 플랫 베이스 돌파 / 피봇 셋업
    """
    if len(df) < 200:
        return None

    # 1차 필터
    if not check_min_volume(df):
        return None

    trend = check_trend_template(df)
    if trend is None:
        return None

    # 패턴 감지
    patterns = []
    details  = {}

    vcp = check_vcp(df)
    if vcp:
        patterns.append(vcp["pattern"])
        details.update({k: v for k, v in vcp.items() if k != "pattern"})

    db = check_double_bottom(df)
    if db:
        patterns.append(db["pattern"])
        details.update({k: v for k, v in db.items() if k != "pattern"})

    bo = check_breakout(df)
    if bo:
        patterns.append(bo["pattern"])
        details.update({k: v for k, v in bo.items() if k != "pattern"})

    pv = check_pivot(df)
    if pv:
        patterns.append(pv["pattern"])
        details.update({k: v for k, v in pv.items() if k != "pattern"})

    if not patterns:
        return None

    close     = df["Close"]
    volume    = df["Volume"]
    cur_close = close.iloc[-1]
    ma50      = close.rolling(50).mean().iloc[-1]
    avg_vol20 = volume.iloc[-20:].mean()

    return {
        "ticker":      ticker,
        "name":        name,
        "price":       int(cur_close),
        "ma50":        int(ma50),
        "vs_ma50":     f"{(cur_close - ma50) / ma50 * 100:+.1f}%",
        "vol_ratio":   f"{volume.iloc[-1] / avg_vol20:.1f}x",
        "trend_score": f"{trend['passed']}/7",
        "pattern":     " + ".join(patterns),
        **details,
    }


# ─────────────────────────────────────────
# VPA (Volume Price Analysis) — Anna Coulling
# ─────────────────────────────────────────

def _vpa_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """VPA 분석용 보조 컬럼 추가."""
    d = df.copy()
    d["spread"]       = d["High"] - d["Low"]
    d["body"]         = (d["Close"] - d["Open"]).abs()
    d["close_pos"]    = (d["Close"] - d["Low"]) / d["spread"].replace(0, np.nan)
    d["vol_ma20"]     = d["Volume"].rolling(20).mean()
    d["spread_ma20"]  = d["spread"].rolling(20).mean()
    d["vol_ratio"]    = d["Volume"] / d["vol_ma20"]
    d["spread_ratio"] = d["spread"] / d["spread_ma20"].replace(0, np.nan)
    d["is_up"]        = d["Close"] >= d["Open"]
    return d


def check_stopping_volume(df: pd.DataFrame) -> dict | None:
    """
    Stopping Volume (하락 멈춤 신호)
    - 최근 5일 내 하락 추세
    - 고거래량 (20일 평균 1.5배 이상)
    - 좁은 스프레드 or 긴 아래꼬리 (종가가 중간 이상)
    """
    if len(df) < 25:
        return None
    d = _vpa_metrics(df)
    row = d.iloc[-1]

    # 최근 5일 하락 추세 확인
    recent_trend = d["Close"].iloc[-6:-1].mean()
    if row["Close"] >= recent_trend * 1.01:
        return None

    if (row["vol_ratio"] >= 1.5
            and row["close_pos"] >= 0.5
            and row["spread_ratio"] <= 1.0):
        return {
            "pattern":   "Stopping Volume",
            "vol_ratio": round(float(row["vol_ratio"]), 2),
            "close_pos": round(float(row["close_pos"]), 2),
        }
    return None


def check_no_supply(df: pd.DataFrame) -> dict | None:
    """
    No Supply (공급 없음 — 매수 신호)
    - 하락 캔들
    - 거래량 < 20일 평균의 70%
    - 좁은 스프레드
    - MA50 위에 위치 (상승 추세 컨텍스트)
    """
    if len(df) < 55:
        return None
    d = _vpa_metrics(df)
    row   = d.iloc[-1]
    ma50  = df["Close"].rolling(50).mean().iloc[-1]

    if (not row["is_up"]
            and row["vol_ratio"] <= 0.70
            and row["spread_ratio"] <= 0.80
            and row["Close"] > ma50):
        return {
            "pattern":   "No Supply",
            "vol_ratio": round(float(row["vol_ratio"]), 2),
        }
    return None


def check_no_demand(df: pd.DataFrame) -> dict | None:
    """
    No Demand (수요 없음 — 약세 경고)
    - 상승 캔들
    - 거래량 < 20일 평균의 70%
    - 좁은 스프레드
    """
    if len(df) < 25:
        return None
    d = _vpa_metrics(df)
    row = d.iloc[-1]

    if (row["is_up"]
            and row["vol_ratio"] <= 0.70
            and row["spread_ratio"] <= 0.80):
        return {
            "pattern":   "No Demand",
            "vol_ratio": round(float(row["vol_ratio"]), 2),
        }
    return None


def check_testing(df: pd.DataFrame) -> dict | None:
    """
    Testing (지지 확인 신호)
    - 저거래량 (< 50% of avg)
    - 좁은 스프레드
    - 전일 대비 소폭 하락 또는 보합
    - MA50 위에 위치
    """
    if len(df) < 55:
        return None
    d = _vpa_metrics(df)
    row   = d.iloc[-1]
    prev  = d.iloc[-2]
    ma50  = df["Close"].rolling(50).mean().iloc[-1]

    price_change = (row["Close"] - prev["Close"]) / prev["Close"] * 100

    if (row["vol_ratio"] <= 0.50
            and row["spread_ratio"] <= 0.70
            and -2.0 <= price_change <= 0.5
            and row["Close"] > ma50):
        return {
            "pattern":   "Testing",
            "vol_ratio": round(float(row["vol_ratio"]), 2),
            "chg":       round(price_change, 2),
        }
    return None


def check_effort_vs_result(df: pd.DataFrame) -> dict | None:
    """
    Effort vs Result — 강한 매수세 확인
    - 고거래량 (2배 이상)
    - 큰 상승 캔들 (스프레드가 평균 이상)
    - 종가가 당일 고점 근처
    """
    if len(df) < 25:
        return None
    d = _vpa_metrics(df)
    row = d.iloc[-1]

    if (row["is_up"]
            and row["vol_ratio"] >= 2.0
            and row["spread_ratio"] >= 1.2
            and row["close_pos"] >= 0.70):
        return {
            "pattern":   "Effort vs Result",
            "vol_ratio": round(float(row["vol_ratio"]), 2),
            "spread_ratio": round(float(row["spread_ratio"]), 2),
        }
    return None


# ── 종목별 VPA 종합 스캔 ───────────────────────────────────

VPA_BULLISH = ["Stopping Volume", "No Supply", "Testing", "Effort vs Result"]
VPA_BEARISH = ["No Demand"]

VPA_COLORS = {
    "Stopping Volume":   "#34d399",
    "No Supply":         "#60a5fa",
    "Testing":           "#a78bfa",
    "Effort vs Result":  "#fbbf24",
    "No Demand":         "#f87171",
}


def scan_vpa(df: pd.DataFrame, ticker: str, name: str) -> dict | None:
    """
    VPA 패턴 종합 스캔.
    bullish 패턴 1개 이상 감지 시 반환.
    """
    if len(df) < 60:
        return None

    checks = [
        check_stopping_volume(df),
        check_no_supply(df),
        check_testing(df),
        check_effort_vs_result(df),
    ]
    matched = [c for c in checks if c]
    if not matched:
        return None

    close     = df["Close"]
    volume    = df["Volume"]
    cur       = float(close.iloc[-1])
    ma50      = float(close.rolling(50).mean().iloc[-1])
    avg_vol20 = float(volume.iloc[-20:].mean())
    vol_ratio = float(volume.iloc[-1] / avg_vol20)

    patterns = [c["pattern"] for c in matched]

    return {
        "ticker":    ticker,
        "name":      name,
        "price":     int(cur),
        "vol_ratio": f"{vol_ratio:.1f}x",
        "vs_ma50":   f"{(cur - ma50) / ma50 * 100:+.1f}%",
        "pattern":   patterns[0],          # 대표 패턴
        "patterns":  " + ".join(patterns),
        "signal":    "bullish" if patterns[0] in VPA_BULLISH else "bearish",
    }
