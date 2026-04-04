# SignalFinder

투자전략에 맞는 진입타점을 자동으로 스캐닝하는 웹 대시보드입니다.

---

## 주요 기능

- 전체 상장 종목을 매일 자동 분석해 전략 조건을 만족하는 종목 필터링
- VCP, 이중바닥, 플랫 베이스 돌파, 피봇 셋업 패턴 자동 감지
- 선정 종목의 인터랙티브 차트 + 선정 근거 + 판단 기준 제공

---

## 프로그램 구조

```
SignalFinder/
│
├── app.py                  # Dash 웹 앱 진입점, 라우팅 및 콜백 등록
│
├── scanner.py              # 전체 종목 스캔 실행 스크립트
│                           # 실행 시 signals_YYYYMMDD_HHMM.csv 생성
│
├── strategy.py             # 전략 로직 (트렌드 템플릿, 패턴 감지 함수)
│
├── data_fetcher.py         # 종목 리스트 및 OHLCV 데이터 수집 (FinanceDataReader)
│
├── chart.py                # matplotlib 기반 standalone 차트 (개발용)
│
├── pages/
│   ├── home.py             # 홈 페이지 레이아웃 (서비스 소개)
│   └── sepa.py             # SEPA 전략 페이지 (전략 설명 + 스캔 결과)
│
└── components/
    └── chart_plotly.py     # Plotly 기반 인터랙티브 차트 컴포넌트
```

### 데이터 흐름

```
scanner.py 실행
    └→ data_fetcher.py로 전체 종목 리스트 수집
    └→ 종목별 OHLCV 데이터 수집
    └→ strategy.py로 전략 조건 분석
    └→ 조건 만족 종목 → signals_YYYYMMDD_HHMM.csv 저장

app.py 실행 (웹 서버)
    └→ / (홈)       → pages/home.py
    └→ /sepa        → pages/sepa.py
                         └→ 최신 signals_*.csv 읽어 종목 카드 표시
                         └→ 차트 보기 클릭 시 실시간 차트 + 근거 표시
```

---

## 설치

**Python 3.9 이상 권장**

```bash
pip install dash dash-bootstrap-components plotly pandas FinanceDataReader
```

---

## 실행 방법

### 1. 종목 스캔

웹 실행 전에 스캐너를 먼저 실행해 결과 파일을 생성합니다.

```bash
python scanner.py
```

완료되면 `signals_YYYYMMDD_HHMM.csv` 파일이 생성됩니다.

### 2. 웹 대시보드 실행

```bash
python app.py
```

브라우저에서 http://127.0.0.1:8050 접속

---

## 전략 설명

### SEPA (Specific Entry Point Analysis)

마크 미너비니의 성장주 투자 전략으로, 2단계 상승국면의 종목에서 저리스크 진입타점을 찾습니다.

**트렌드 템플릿 (7가지 조건)**

| # | 조건 |
|---|------|
| 1 | 현재가 > MA150, MA200 |
| 2 | MA150 > MA200 |
| 3 | MA200 상승 기울기 유지 |
| 4 | MA50 > MA150, MA200 |
| 5 | 현재가 > MA50 |
| 6 | 현재가가 52주 저점보다 30% 이상 위 |
| 7 | 현재가가 52주 고점의 25% 이내 |

**감지 패턴**

| 패턴 | 설명 |
|------|------|
| VCP | 변동성 수축 패턴 — 3구간 등락폭이 순차적으로 줄어드는 것 |
| 이중바닥 | 60일 내 두 저점이 5% 이내 가격 차이, 넥라인 돌파 시 매수 신호 |
| 플랫 베이스 돌파 | 20일간 15% 미만 횡보 후 거래량 동반 상단 돌파 |
| 피봇 셋업 | 20일 고점 98~103% 구간에서 거래량 수축 중인 종목 |

---

## 페이지 구성

| URL | 설명 |
|-----|------|
| `/` | 홈 — 서비스 소개 및 전략 목록 |
| `/sepa` | SEPA 전략 — 전략 설명 + 오늘의 스캔 결과 |
