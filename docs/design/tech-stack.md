# Stock Bot — 기술 스택 (Tech Stack)

- **작성일**: 2026-06-25
- **상태**: 백엔드 **확정** / 프론트엔드 진행 중
- **버전 원칙**: 아래 버전은 **2026-06-25 공식 소스 실시간 확인값.** 실제 설치 시 그 시점 최신 안정판으로 깔고 **lockfile(백엔드 uv / 프론트 package-lock)에 박제.**
- **선정 원칙**: 목적 기반 선택, 통제권은 사용자, 1인 사용.

---

## 백엔드 (확정)

### 언어 · 런타임 · 도구
| 항목 | 버전 | 비고 |
|---|---|---|
| Python | **3.12.13** | ML/데이터 라이브러리 호환 최고·안정. 3.14는 wheel 보수성 위해 보류 |
| uv | 0.11.24 | 의존성 설치 + 버전 잠금 |
| Docker (+ compose) | 최신 | 배포·24h 유지 |

### 웹 · API
| 항목 | 버전 | 역할 |
|---|---|---|
| FastAPI | 0.138.0 | 웹 프레임워크 (Spring 대응) |
| Uvicorn | 0.49.0 | ASGI 서버 = 앱 실행기 (WAS, **Tomcat 역할**) |
| Pydantic | 2.13.4 | 데이터 검증·모델 (런타임 입력 검증) |
| pydantic-settings | 2.14.2 | 설정·시크릿 로딩(외부 파일/env) |

### DB
| 항목 | 버전 | 역할 |
|---|---|---|
| PostgreSQL | **18** | DB 엔진 (FTS 내장 + 나중 pgvector 가능) |
| SQLAlchemy | 2.0.51 | ORM |
| Alembic | 1.18.4 | DB 마이그레이션 |
| psycopg | 3.3.4 (v3) | Postgres 드라이버 (비동기 지원) |

### 운영 라이브러리
| 항목 | 버전 | 역할 |
|---|---|---|
| APScheduler | **3.11.2** | 스케줄러 (3.x 안정판, 4.x alpha 회피) |
| loguru | 0.7.3 | 로깅 (파일·회전, logback 대응) |
| httpx | 0.28.1 | HTTP 클라이언트 (토스·뉴스·Claude 호출, 비동기) |
| cryptography | 49.0.0 | 토스 키 암호화 저장 |

### AI
| 항목 | 버전 | 비고 |
|---|---|---|
| anthropic | 0.112.0 | Claude SDK. **Haiku 4.5**(대량 분류) / **Opus 4.8**(깊은 분석·리포트·채팅·포트폴리오) |

### 테스트 · 코드 품질
| 항목 | 버전 | 비고 |
|---|---|---|
| pytest | 9.1.1 | 테스트 |
| pytest-asyncio | 1.4.0 | 비동기 테스트 |
| Ruff | 0.15.19 | 린터 + 포매터 (한 도구) |
| pre-commit | 4.6.0 | 커밋 전 자동 검사(ruff 등) |
| (타입힌트) | — | 코드 전반 사용 (Pydantic 필수). **mypy는 보류** — 외부 입력은 Pydantic 런타임 검증이 막고, 솔로 초기 마찰 회피. 나중에 None 버그/규모 커지면 추가 |

### 아키텍처 결정
- **비동기(async/await) 기반** — I/O fan-out(뉴스 다수 fetch + Claude 다수 호출)이 핵심 동작이라 비동기가 자연스럽고 빠름. 막는(blocking) 라이브러리(추후 sentence-transformers 등)는 스레드로 분리.
- **스케줄러 위치 = API 서버 프로세스 내 (옵션 A)** — APScheduler를 FastAPI 앱과 같은 프로세스에서 구동. 단 **나중에 별도 워커로 분리 가능하도록 스케줄러를 독립 모듈로** 작성. (분리 시: 별도 워커 프로세스, **Postgres로 소통**, docker-compose로 둘 다 유지, worker heartbeat로 중단 감지)
- **인증**: 페어링 키(공유 비밀, 백엔드 **외부 파일**에 보관, git 제외) + 매 요청 헤더 검사 + HTTPS. 최초 1회 앱에서 **[페어링 키 → 통과 → 토스 키]** 입력. 페어링 키는 앱 **안전보관함(expo-secure-store)** 저장. **토스 키는 백엔드에 암호화 저장**(앱엔 안 남김). **`TRADING_ENABLED=false`** 하드 플래그(키 scope 없어 코드가 막음).

### 배포 · 운영 (방향만 결정, 실제 셋업은 배포 단계)
- **클라우드 VM**(AWS/Oracle/GCP 등) 24h 상시 가동.
- **nginx + Certbot**로 HTTPS(앞단 리버스 프록시 = nginx 역할). **도메인 필요**(연 ~1만원).
- **운영 알림**: 백엔드 에러·엔진 중단 → 디스코드. Docker `restart: unless-stopped` 자동 재시작 + (워커 분리 시) heartbeat 감지.
- ※ 이 항목은 *앱 코드에 영향 없음* — 개발이 아니라 운영 결정.

### 뉴스 파이프라인 단계 라이브러리 (나중 설치 — 그 단계에서 uv로 버전 확정)
> 설치가 한참 뒤라 지금 버전 핀 안 박음(드리프트 + 일부는 무거움).
- `feedparser`(RSS), `trafilatura`+`readability-lxml`+`newspaper4k`(본문 추출 폴백체인), `beautifulsoup4`+`lxml`(HTML)
- `datasketch`(MinHash/LSH) 또는 `simhash`(중복제거), `sentence-transformers`(임베딩·무거움, Phase 3)
- `konlpy`/`mecab-ko`(한국어 형태소, 필요 시), DART/EDGAR는 `httpx` 직접 호출

---

## 프론트엔드 (확정 — UI 라이브러리만 디자인 보고 결정)

| 항목 | 선택 | 버전 |
|---|---|---|
| 프레임워크 | **Expo (React Native)** | SDK **56** (RN 0.85 / React 19.2 — SDK가 고정) |
| 언어 | TypeScript | (SDK 포함) |
| 개발 방식 | **development build** (Expo Go 미사용) | `expo-dev-client` — SDK56 Expo Go 호환이슈 + 한계 회피, 운영에 근접 |
| 네비게이션 | **Expo Router** | 56.2.11 (파일기반, React Navigation 위) |
| 서버 데이터 | **TanStack Query** | 5.101.1 |
| 전역 상태 | **Zustand** (최소 사용) | 5.0.14 |
| HTTP | **axios** | 1.18.1 (인터셉터로 페어링 키 헤더 자동첨부) |
| 폼 | **react-hook-form** | 7.80.0 |
| 폼 검증 | **Zod** + **@hookform/resolvers** | 4.4.3 / 5.4.0 (스키마 정의, API 응답 검증에도 재사용) |
| 보안 저장 | **expo-secure-store** | SDK56 호환판 (페어링 키) |
| 기기 잠금 | **expo-local-authentication** | SDK56 호환판 (지문/Face/PIN) |
| 코드 품질 | **ESLint + Prettier** | Expo 기본 (`expo lint`) |
| UI/스타일 | **NativeWind (Tailwind)** | 핸드오프 디자인 토큰(색·spacing·radius 등)을 tailwind 설정에 매핑. 컴포넌트 킷(Paper/Tamagui)은 회피. 정확한 버전(nativewind/tailwindcss)은 프론트 스캐폴드 시 실시간 확정 |
| 보류 | async-storage / 차트(victory-native 등) | 필요 시 추가 |
| 제외 | expo-notifications | 푸시는 디스코드가 담당 → 불필요 |

**상태 관리 원칙**: 서버 데이터 → TanStack Query / 한 화면 전용 → 로컬 `useState` / 여러 화면 공유 + 서버 아님 → Zustand(소수, 주로 인증·세션).
**화면 디자인**: 별도 Claude design 세션 산출물 → `docs/design/screens/design_handoff_toss_stock_assistant/` (토스 스타일, 14화면, hifi). *기존 디자인을 그대로 유지*하는 것이 UI 구현 원칙. 핸드오프의 더미데이터(`master()`·`reportData()`·`calEvents()`·`responses()`·`pfReports`)는 API/DB 스키마 설계 참고자료.
**온보딩 보안 문구 수정(구현 시 적용)**: "기기에만 저장"→"암호화되어 안전하게 저장"(토스 키는 백엔드 암호화 저장), "주문 권한 요청 안 함"→"주문 기능 미사용".
**개발 워크플로우**: Expo Go 대신 development build(`eas build --profile development` 또는 로컬 `expo run`)로 폰에 설치해 개발. (배포·빌드 셋업은 운영 단계)

---

## 버전 확정 방식
- 위 버전 = 2026-06-25 실측. 설치 시 최신 안정판 설치 후 **uv(백엔드) / package-lock(프론트)** 로 잠금.
- 시점 민감 정보(버전·가격)는 항상 실시간 확인 후 기록.
