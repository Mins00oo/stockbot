# 04. 문제해결 FAQ

## `uv: command not found` / `uv` 인식 안 됨
- uv 설치 확인(`00_사전_준비물_설치.md`). 설치 후 **터미널 새로 열기**(PATH 갱신).

## `docker compose up` 실패 / "Cannot connect to the Docker daemon"
- **Docker Desktop이 실행 중인지** 확인(트레이 아이콘). 켜고 다시.

## 포트 충돌 (`port is already allocated` / 8000·5432 사용 중)
- 이미 그 포트 쓰는 프로세스가 있음.
  - Postgres(5432): 기존 Postgres 끄거나, docker-compose의 포트를 바꿈.
  - 서버(8000): `--port 8001` 등으로 변경.

## DB 연결 실패 (`could not connect` / `connection refused`)
1. Postgres 떠있나? → `docker ps` 에 컨테이너 보이는지.
2. `.env`의 `DATABASE_URL` 계정/DB명이 **docker-compose와 일치**하는지.
3. 컨테이너 뜬 직후면 몇 초 기다렸다 재시도(초기화 시간).

## `alembic upgrade head` 에러
- Postgres가 떠있는지 먼저 확인 → 다시 실행.
- 마이그레이션 파일 충돌 시 `uv run alembic current`로 현재 버전 확인.

## 토스 연결/조회 시 401 (인증 실패)
- 토스 키가 틀렸거나 토큰 만료. → 앱에서 **재연결**(키 다시 입력).
- 페어링 키 헤더가 맞는지(앱의 PAIRING_KEY = 백엔드 `.env`의 PAIRING_KEY).

## `.env` 값을 바꿨는데 반영 안 됨
- 서버 **재시작**(Ctrl+C 후 다시 실행). `.env`는 시작 시 로드됨.

## 라이브러리 추가했는데 import 안 됨
- `uv add <패키지>` 후 서버 재시작. (또는 `uv sync`)

## `python` 실행 시 "SRE module mismatch" / 이상한 표준라이브러리 에러
- 원인: **`PYTHONHOME` 환경변수**가 다른 버전 파이썬을 가리켜, 인터프리터(python.exe)와 표준라이브러리(Lib) 버전이 어긋남.
- 확인(PowerShell): `[Environment]::GetEnvironmentVariable("PYTHONHOME","User")`
- 해결: 삭제 → `[Environment]::SetEnvironmentVariable("PYTHONHOME", $null, "User")` → **새 터미널** 열기.
- ※ `PYTHONHOME`은 보통 설정하면 안 되는 값. 파이썬이 여러 개 깔려 있어도 각자 자기 Lib을 쓰게 두면 됨. (버전 전환은 `py -3.12` 또는 uv 사용)
