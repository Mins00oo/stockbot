# Stock Bot — API 정의서

- **작성일**: 2026-06-25
- **상태**: 오늘 슬라이스(키 연결 → 홈 보유목록) 범위 확정. 나머지 도메인은 추후 추가.
- **응답 방식**: HTTP 상태코드 + 표준 에러 바디 (성공=2xx+데이터, 실패=4xx/5xx+에러)
- **용도**: 백엔드·프론트가 *같은 계약*을 보고 병렬 개발하는 인터페이스.

---

## 1. 공통 규칙

- **Base URL**: (개발) `http://<백엔드host>:8000` — 실기기는 PC의 LAN IP, 시뮬레이터는 localhost
- **인증**: 보호 엔드포인트는 헤더 **`X-Pairing-Key: <키>`** 필수. 없거나 틀리면 `401`. (`/health`만 공개)
- **성공 응답**: `2xx` + 데이터 직접 (봉투 없음)
- **에러 응답**: `4xx/5xx` + 표준 바디:
  ```json
  { "error": { "code": "에러코드", "message": "사용자에게 보여줄 메시지" } }
  ```

### 에러 처리 방침 (중앙 관리)
- 서비스 코드에 code·message를 **박지 않음.** 중앙 카탈로그 + 전역 핸들러로 관리.
  - **`core/errors.py`** — 에러 단일 출처(커스텀 예외: code·status·message 한 곳)
  - **전역 예외 핸들러**(main.py 1곳) — 예외를 `{error:{code,message}}` + 상태코드로 변환
  - 서비스는 `raise NotConnected()` 처럼 **타입 예외만 던짐** (포맷 없음)
  - (Spring의 `@RestControllerAdvice` + `@ExceptionHandler` + 에러 enum 과 동일 패턴)

---

## 2. 에러 코드 카탈로그

| code | HTTP | message | 언제 |
|---|---|---|---|
| `UNAUTHORIZED` | 401 | 페어링 키가 올바르지 않아요 | 페어링 키 없음/틀림 |
| `VALIDATION_ERROR` | 422 | 입력값이 올바르지 않아요 | 요청 바디 형식 오류 |
| `TOSS_AUTH_FAILED` | 400 | 토스 키가 올바르지 않아요 | 토스가 키를 거부(연결 시) |
| `NOT_CONNECTED` | 409 | 토스 계좌를 먼저 연결해 주세요 | 토스 미연결 상태에서 보유조회 |
| `TOSS_UNAVAILABLE` | 502 | 토스 서버에 연결할 수 없어요 | 토스 API 장애/응답불가 |
| `INTERNAL` | 500 | 일시적인 오류가 발생했어요 | 서버 내부 오류 |

---

## 3. 엔드포인트 (오늘 범위 5개)

### ① `GET /health` — 헬스체크
- 헤더: 없음 · 바디: 없음
- **200**: `{ "status": "ok" }`

### ② `POST /auth/pairing/verify` — 페어링 키 검증 (온보딩 1단계)
- 헤더: `X-Pairing-Key`
- 바디: 없음 (키는 헤더로)
- **200**: `{ "valid": true }`
- 에러: **401** `UNAUTHORIZED`

### ③ `POST /auth/toss/connect` — 토스 계좌 연결 (온보딩 2단계)
- 헤더: `X-Pairing-Key`
- 바디:
  ```json
  { "appKey": "tskey_live_...", "secretKey": "sk_..." }
  ```
- 동작: 토스 OAuth 토큰 발급 → `/accounts`로 `accountSeq` 획득 → 키 **암호화 후 DB 저장**
- **200**:
  ```json
  { "connected": true, "account": { "seq": "12345678", "name": "토스증권 계좌" } }
  ```
- 에러: **400** `TOSS_AUTH_FAILED`(토스 키 거부) · **422** `VALIDATION_ERROR`(바디 누락) · **401** `UNAUTHORIZED` · **502** `TOSS_UNAVAILABLE`

### ③-2 `GET /auth/status` — 연결 상태 (앱 실행 게이트)
- 헤더: `X-Pairing-Key`
- 바디: 없음
- 동작: 백엔드 DB에 토스 자격증명(암호화 키)이 있는지로 연결 여부 판단. 앱이 실행 시 호출해 **연결됨→홈 / 미연결→2단계(toss-key)** 로 라우팅.
- **200**: `{ "connected": true }` (미연결이면 `false`)
- 에러: **401** `UNAUTHORIZED`

### ④ `GET /portfolio/holdings` — 보유 종목 (홈)
- 헤더: `X-Pairing-Key`
- 바디: 없음
- **200**:
  ```json
  {
    "totalValueKrw": 12500000,
    "totalPnlKrw": 320000,
    "totalPnlRate": 2.6,
    "totalPurchaseKrw": 12180000,
    "holdings": [
      {
        "symbol": "005930", "name": "삼성전자", "market": "KR",
        "quantity": 10, "avgPrice": 70000, "currentPrice": 72000,
        "evalAmount": 720000, "evalAmountKrw": 720000,
        "pnl": 20000, "pnlRate": 2.86, "currency": "KRW"
      },
      {
        "symbol": "AAPL", "name": "Apple", "market": "US",
        "quantity": 5, "avgPrice": 180.0, "currentPrice": 195.0,
        "evalAmount": 975.0, "evalAmountKrw": 1350000,
        "pnl": 75.0, "pnlRate": 8.33, "currency": "USD"
      }
    ]
  }
  ```
- 에러: **409** `NOT_CONNECTED`(연결 전) · **401** `UNAUTHORIZED` · **502** `TOSS_UNAVAILABLE`

#### holdings[] 필드
| 필드 | 타입 | 설명 |
|---|---|---|
| `symbol` | string | 종목코드 (KR 6자리 / US 티커) |
| `name` | string | 종목명 |
| `market` | `"KR"` \| `"US"` | 시장 |
| `quantity` | number | 보유 수량 |
| `avgPrice` | number | 평균 단가 (해당 통화) |
| `currentPrice` | number | 현재가 (해당 통화) |
| `evalAmount` | number | 평가금액 (해당 통화, 표시용) |
| `evalAmountKrw` | number | 평가금액 원화환산 (정렬·합계용) |
| `pnl` | number | 평가손익 (해당 통화) |
| `pnlRate` | number | 손익률(%) |
| `currency` | `"KRW"` \| `"USD"` | 통화 |

- **총합은 토스 raw**: `totalValueKrw`·`totalPnlKrw`·`totalPnlRate`·`totalPurchaseKrw`(투자원금)는 우리가 합산·계산하지 않고 **토스 계좌 overview 값(환율·수수료 반영)을 그대로** 사용 → 토스 앱과 숫자 일치. (종목별 `evalAmountKrw`만 정렬·표시용으로 환율 환산)
- **현재가**: holdings의 `lastPrice` 사용. 실시간성은 프론트가 `/holdings`를 **3초 주기 재조회**(포그라운드·장중)로 확보 — 별도 `/prices` 미사용.
- **색상**(상승=빨강/하락=파랑)은 **프론트가 `pnl` 부호로 판단** (한국식). 정렬은 `evalAmountKrw` 내림차순.

---

## 3-A. 종목 상세 화면 엔드포인트 (stocks)

> 토스 시세 + (US) Finnhub 펀더멘털. `market`(KR/US) 미지정 시 symbol로 추론(6자리=KR). 모두 `X-Pairing-Key` 필수. 비보유 종목도 동작(보유 현황은 `/portfolio/holdings`에서 별도 조합).

### ⑤ `GET /stocks/{symbol}` — 종목 상세(정보·펀더멘털) · *진입 시 1회*
- 쿼리: `market`(선택 `KR|US`)
- **200**:
  ```json
  { "symbol":"005930","name":"삼성전자","market":"KR","exchange":"KOSPI","currency":"KRW",
    "industry":null,"prevClose":71000,
    "priceLimits":{"upper":92300,"lower":49700},
    "fundamentals":{"marketCap":4.25e14,"week52High":88800,"week52Low":64500,
      "per":null,"pbr":null,"eps":null,"dividendYield":null},
    "warnings":[{"type":"OVERHEATED","label":"단기과열"}] }
  ```
  - **시가총액 = 현재가 × 상장주식수**(토스). **KR**: per/pbr/eps/dividendYield=`null`(거래경고 있을 수 있음). **US**: 펀더멘털·`industry` 채워짐(Finnhub), warnings=`[]`.
  - 상하한: KR=토스 제공 / **US=전일종가 ±10% 참고밴드(계산)**.
- 에러: **409** `NOT_CONNECTED` · **401** `UNAUTHORIZED` · **502** `TOSS_UNAVAILABLE`

### ⑥ `GET /stocks/{symbol}/quote` — 실시간 시세 · *2초 폴링*
- 쿼리: `market`(선택) · **200**: `{ "symbol","price","prevClose","change","changeRate","volume","currency","krwPrice" }` (`krwPrice`=US만, 그 외 `null`)

### ⑦ `GET /stocks/{symbol}/chart?range=1D|1W|1M|3M|1Y` — 차트 · *기본 3M*
- **200**: `{ "range":"3M","currency":"KRW","points":[{"t","close","volume"}],"periodReturn":12.83 }`
  - `1D`=분봉, 나머지=일봉(주봉/월봉 없음). `periodReturn`=기간 시작가 대비 %.

### ⑧ `GET /stocks/{symbol}/orderbook` — 10단계 호가
- **200**: `{ "asks":[{"price","volume"}],"bids":[{"price","volume"}],"currency" }` (asks=매도·bids=매수)

### ⑨ `GET /stocks/{symbol}/trades` — 최근 체결
- **200**: `{ "trades":[{"time","price","volume"}],"currency" }` — ⚠️ 토스가 매수/매도 side 미제공(방향 표시 불가).

---

## 3-B. 뉴스 엔드포인트 (news) — 1단계: 수집·정규화·중복제거·저장

> 수집은 스케줄러가 백엔드 프로세스 안에서 주기적으로 수행(보유종목 대상, US=Finnhub·KR=네이버).
> 아래는 **저장된 결과 조회** + **수동 트리거**. LLM 분석은 다음 단계. 셋업은 `docs/manual/08`.

### ⑩ `GET /news?symbol=&limit=&offset=` — 저장된 뉴스 목록 · *newest first*
- 쿼리: `symbol`(선택, 해당 종목 필터) · `limit`(1~200, 기본 50) · `offset`(기본 0)
- **200**:
  ```json
  { "items": [ {
      "id": 1, "source": "finnhub", "headline": "...", "url": "https://...",
      "snippet": "...", "publishedAt": "2026-06-27T01:00:00Z",
      "fetchedAt": "2026-06-27T01:05:00Z",
      "tickers": [ { "symbol": "AAPL", "market": "US", "matchedBy": "source_tag" } ]
  } ] }
  ```
  - `matchedBy`: `source_tag`(Finnhub 자동 태깅) | `query`(네이버 회사명 쿼리 추정).
  - ⚠️ 저작권 정책상 **본문 미저장** — 헤드라인·원문링크·소스 snippet만.

### ⑪ `POST /news/ingest/run` — 즉시 1회 수집(스케줄 무관) · *테스트/온디맨드*
- 바디: 없음
- **200**: `{ "fetched":N, "stored":M, "deduped":K, "symbols":S, "skipped":null }`
  - `skipped`: 토스 미연결 등으로 건너뛰면 `"not_connected"`(에러 아님).

---

## 4. 범위
- **오늘(키연결→홈)**: health · pairing/verify · toss/connect · auth/status · portfolio/holdings (5개)
- **종목 상세**: stocks 5개 (detail · quote · chart · orderbook · trades)
- **뉴스(1단계)**: news 2개 (목록 조회 · 수동 수집 트리거) + 백그라운드 스케줄 수집
- **나중**: stocks(검색) · market(시세·급변) · news(분석·4부구조) · analysis · alerts · reports · calendar · chat 등 도메인 엔드포인트 추가 시 이 문서에 이어 작성.

## 5. 연동 메모
- **프론트(axios)**: 인터셉터가 `X-Pairing-Key` 자동 첨부 + 응답 4xx/5xx에서 `error.code`로 분기, `error.message` 표시.
- **백엔드**: 서비스는 타입 예외(`raise NotConnected()` 등) → 전역 핸들러가 표준 에러 바디로 변환.
