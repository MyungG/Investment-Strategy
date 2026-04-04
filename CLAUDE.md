# SignalFinder - CLAUDE.md

## 프로젝트 개요
투자전략에 맞는 진입타점을 자동으로 스캐닝하는 웹 대시보드.
국내주식(KOSPI+KOSDAQ) → 향후 해외주식, 코인 추가 예정.

## 기술 스택
- **웹 프레임워크**: Dash + dash-bootstrap-components (DARKLY 테마)
- **차트**: Plotly (웹), mplfinance (standalone)
- **데이터**: FinanceDataReader (종목 리스트 + OHLCV)
- **언어**: Python만 사용 (JavaScript 없음)

## 파일 구조
```
app.py              # 웹 앱 진입점, 라우팅, 콜백
scanner.py          # 전체 종목 스캔 → signals_YYYYMMDD_HHMM.csv 저장
strategy.py         # 전략 로직 (트렌드 템플릿, 패턴 감지)
data_fetcher.py     # 종목 리스트 + OHLCV 수집
chart.py            # matplotlib standalone 차트 (개발용)
pages/home.py       # 홈 페이지 (서비스 소개)
pages/sepa.py       # SEPA 전략 페이지 (전략 설명 + 스캔 결과)
components/chart_plotly.py  # Plotly 차트 컴포넌트
```

## 실행 방법
```bash
python scanner.py   # 먼저 실행 → signals_*.csv 생성
python app.py       # 웹 서버 실행 → http://127.0.0.1:8050
```

## 중요 규칙

### 한글 처리
- 모든 Python 파일 상단에 `# -*- coding: utf-8 -*-` 포함
- 한글 문자열은 반드시 유니코드 이스케이프(`\uXXXX`)로 작성
- 파일에 한글을 직접 쓰면 cp949 인코딩 오류 발생

### 차트
- 양봉: 빨간색(`#ff3333`), 음봉: 파란색(`#3399ff`) — 한국 관례
- 차트 내 텍스트는 영어만 사용 (한글 렌더링 깨짐)
- MA 기간: MA50, MA150, MA200 (SEPA 표준)

### 패턴 키 이름 (CSV/코드 내부용, 변경 금지)
```
"VCP", "Double Bottom", "Flat Base Breakout", "Pivot Setup"
```
한글 표시명은 `PATTERN_KO` 딕셔너리에서 별도 관리 (pages/sepa.py)

### 색상 테마
- 배경: `#0d1117`
- 카드 배경: `#161b22`
- 테두리: `#21262d`
- 강조(보라): `#6366f1`
- VCP: `#a78bfa`, 이중바닥: `#34d399`, 플랫베이스: `#fbbf24`, 피봇: `#60a5fa`

## SEPA 전략 조건
**트렌드 템플릿 (7조건 모두 충족 시 2단계 상승)**
1. 현재가 > MA150, MA200
2. MA150 > MA200
3. MA200 상승 기울기
4. MA50 > MA150, MA200
5. 현재가 > MA50
6. 현재가 > 52주 저점 + 30%
7. 현재가 < 52주 고점 × 1.25 (25% 이내)

**패턴 감지 기준**
- VCP: 3구간 등락폭이 각각 이전의 80% 미만, 마지막 구간 10% 미만
- 이중바닥: 60일 내 두 저점이 5% 이내, 간격 10~50일
- 플랫베이스: 20일 등락폭 15% 미만 횡보 후 거래량 1.5배 돌파
- 피봇: 20일 고점의 98~103%, 거래량 20일 평균 80% 미만

## GitHub
https://github.com/MyungG/Investment-Strategy

## 향후 추가 예정
- 해외주식 스캐너
- 비트코인/코인 스캐너
- APScheduler로 매일 자동 스캔 (장 시작 전)
- Telegram 알림 연동
- Render 배포
