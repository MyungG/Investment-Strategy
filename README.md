# SignalFinder

투자전략에 맞는 진입타점을 자동으로 스캐닝하는 웹 대시보드입니다.

---

## 주요 기능

- 전체 상장 종목(KOSPI + KOSDAQ)을 매일 자동 분석해 전략 조건을 만족하는 종목 필터링
- SEPA(성장주), VPA(거래량) 두 가지 독립적인 투자전략 스캐너 운영
- 선정 종목의 인터랙티브 캔들 차트 + 선정 근거 + 판단 기준 제공
- 국내 시장 지수, 외국인/기관 매매동향, 거래대금 상위 종목 실시간 제공
- 해외 주요 지수, 공포탐욕지수, 섹터별 등락률 조회
- GitHub Actions로 매 평일 장 마감 후 자동 스캔 및 CSV 커밋

---

## 프로그램 구조

```
SignalFinder/
│
├── app.py                      # Dash 웹 앱 진입점, 라우팅 및 콜백 등록
│
├── scanner.py                  # SEPA 전체 종목 스캔 → signals_YYYYMMDD_HHMM.csv
├── vpa_scanner.py              # VPA 전체 종목 스캔 → vpa_signals_YYYYMMDD_HHMM.csv
├── market_scanner.py           # 시장 지표 보조 스캔
│
├── strategy.py                 # SEPA 전략 로직 (트렌드 템플릿, 패턴 감지)
├── data_fetcher.py             # 종목 리스트 및 OHLCV 수집 (FinanceDataReader)
├── kis_api.py                  # 한국투자증권 API (외국인/기관 매매동향, 해외지수 등)
│
├── pages/
│   ├── home.py                 # 홈 페이지 (서비스 소개 + 전략 목록)
│   ├── sepa.py                 # SEPA 전략 페이지 (전략 설명 + 스캔 결과)
│   ├── vpa.py                  # VPA 전략 페이지 (전략 설명 + 스캔 결과)
│   └── market.py               # 시장 정보 페이지 (국내 / 해외 분리)
│
├── components/
│   └── chart_plotly.py         # Plotly 인터랙티브 캔들 차트 컴포넌트
│
├── api/
│   └── index.py                # Vercel 배포용 WSGI 엔트리포인트
│
├── investor_cache.json         # 외국인/기관 매매동향 캐시 (GitHub Actions가 매일 갱신)
│
└── .github/workflows/
    └── scan.yml                # 매 평일 4PM KST 자동 스캔 워크플로우
```

### 데이터 흐름

```
[GitHub Actions — 평일 오후 4시 KST]
    └→ scanner.py       → signals_YYYYMMDD_HHMM.csv 커밋
    └→ vpa_scanner.py   → vpa_signals_YYYYMMDD_HHMM.csv 커밋
    └→ kis_api.py       → investor_cache.json 커밋
    └→ git push → Vercel 자동 재배포

[웹 서버 — app.py]
    └→ /                → pages/home.py
    └→ /sepa            → pages/sepa.py
    │       └→ signals_*.csv 읽어 종목 카드 표시
    │       └→ 차트 보기 클릭 시 캔들 차트 + 선정 근거 표시
    └→ /vpa             → pages/vpa.py
    │       └→ vpa_signals_*.csv 읽어 종목 카드 표시
    │       └→ VPA 패턴 해석 + 스프레드/거래량/종가 위치 지표 표시
    └→ /market/domestic → pages/market.py (국내)
    │       └→ KOSPI/KOSDAQ 지수, 거래대금 상위, 외국인/기관 매매동향
    └→ /market/overseas → pages/market.py (해외)
            └→ 주요 해외지수, 공포탐욕지수, 섹터별 등락률
```

---

## 설치

**Python 3.10 이상 권장**

```bash
pip install -r requirements.txt
```

`requirements.txt` 주요 패키지:

```
dash
dash-bootstrap-components
plotly
pandas
requests
python-dotenv
finance-datareader @ git+https://github.com/FinanceData/FinanceDataReader.git
yfinance
gunicorn
```

---

## 실행 방법

### 1. 종목 스캔

```bash
python scanner.py      # SEPA 스캔
python vpa_scanner.py  # VPA 스캔
```

완료되면 `signals_YYYYMMDD_HHMM.csv`, `vpa_signals_YYYYMMDD_HHMM.csv` 파일이 생성됩니다.

### 2. 웹 대시보드 실행

```bash
python app.py
```

브라우저에서 http://127.0.0.1:8050 접속

### 3. 환경변수 설정 (시장 정보 탭 사용 시)

한국투자증권 Open API 키가 필요합니다.

```
KIS_APP_KEY=발급받은_앱키
KIS_APP_SECRET=발급받은_시크릿
KIS_IS_REAL=true
```

`.env` 파일에 저장하거나 Vercel 환경변수로 등록합니다.

---

## 전략 설명

### SEPA (Specific Entry Point Analysis)

마크 미너비니의 성장주 투자 전략으로, 2단계 상승국면의 종목에서 저리스크 진입타점을 찾습니다.

**트렌드 템플릿 (7가지 조건 모두 충족 시 선정)**

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
| VCP | 변동성 수축 패턴 — 3구간 등락폭이 순차적으로 줄어들며 매물대 소화 |
| 이중바닥 | 60일 내 두 저점이 5% 이내 가격 차이, 간격 10~50일 |
| 플랫 베이스 돌파 | 20일간 15% 미만 횡보 후 거래량 1.5배 동반 상단 돌파 |
| 피봇 셋업 | 20일 고점 98~103% 구간에서 거래량 평균 80% 미만으로 수축 중 |

---

### VPA (Volume Price Analysis)

애나 쿨링의 거래량-가격 분석 기법으로, 세력 주체의 실질 매수세를 포착합니다.

**감지 패턴**

| 패턴 | 설명 |
|------|------|
| Stopping Volume | 대량 거래와 함께 하락 모멘텀이 멈추는 구간 — 세력이 매도 물량 흡수 |
| No Supply | 거래량이 적은 하락 — 실질 매도 압력 없음을 의미 |
| Testing | 평균보다 적은 거래량으로 지지선 하락 테스트 후 반등 확인 |
| Effort vs Result | 강한 거래량을 수반한 대형 양봉 — 수요의 적극적 참여 신호 |
| No Demand | 저량 양봉으로 매수세 미약 — 추가 상승 신뢰도 낮음 |

**보조 지표 (종목 카드)**

| 지표 | 설명 |
|------|------|
| 스프레드 | 캔들 고저가 차이 — 작을수록 저항 컴플렉스 현상 |
| 거래량 | 20일 평균 대비 비율 |
| 종가 위치 | 캔들 범위 내 종가 위치 (0=저점, 1=고점) |

---

## 페이지 구성

| URL | 설명 |
|-----|------|
| `/` | 홈 — 서비스 소개 및 전략 목록 |
| `/sepa` | SEPA 전략 — 전략 설명 + 오늘의 스캔 결과 |
| `/vpa` | VPA 전략 — 전략 설명 + 오늘의 스캔 결과 |
| `/market/domestic` | 시장 정보 (국내) — 지수, 거래대금 상위, 외국인/기관 동향 |
| `/market/overseas` | 시장 정보 (해외) — 주요 해외지수, 공포탐욕지수, 섹터 등락률 |

---

## 자동화 (GitHub Actions)

`.github/workflows/scan.yml`이 매 평일 오후 4시(KST) 자동으로 실행됩니다.

1. SEPA 스캐너 실행 → `signals_*.csv` 생성
2. VPA 스캐너 실행 → `vpa_signals_*.csv` 생성
3. 한투 API로 외국인/기관 데이터 수집 → `investor_cache.json` 갱신
4. 변경된 파일 자동 커밋 및 푸시
5. Vercel 자동 재배포 트리거

Repository Secrets 필요: `KIS_APP_KEY`, `KIS_APP_SECRET`

---

## 배포

[Vercel](https://vercel.com)을 통해 무료 배포 중입니다.
`api/index.py`가 Flask WSGI 엔트리포인트 역할을 하며, `vercel.json`으로 라우팅을 처리합니다.
