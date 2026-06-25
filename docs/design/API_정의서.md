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

## 3. 엔드포인트 (오늘 범위 4개)

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

## 4. 범위
- **오늘**: 위 4개 (health · pairing/verify · toss/connect · portfolio/holdings)
- **나중**: stocks(검색) · market(시세·급변) · news · analysis · alerts · reports · calendar · chat 등 도메인 엔드포인트 추가 시 이 문서에 이어 작성.

## 5. 연동 메모
- **프론트(axios)**: 인터셉터가 `X-Pairing-Key` 자동 첨부 + 응답 4xx/5xx에서 `error.code`로 분기, `error.message` 표시.
- **백엔드**: 서비스는 타입 예외(`raise NotConnected()` 등) → 전역 핸들러가 표준 에러 바디로 변환.
