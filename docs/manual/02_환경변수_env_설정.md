# 02. 환경변수(.env) 설정

`.env` 파일은 **비밀·환경 설정**을 담음. **git에 안 올라감**(.gitignore). `.env.example`을 복사해서 값을 채운다.

## .env 항목 (4개)

| 키 | 예시/형식 | 설명 |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://stockbot:stockbot@localhost:5432/stockbot` | DB 접속 주소. **docker-compose의 계정/DB명과 일치해야 함** |
| `PAIRING_KEY` | (긴 랜덤 문자열) | **앱 ↔ 백엔드 인증용 비밀.** 내가 정함. 앱 온보딩 1단계에도 **같은 값** 입력 |
| `TOSS_KEY_ENC_KEY` | (Fernet 키) | 토스 키를 **암호화**해 DB에 저장할 때 쓰는 키 |
| `TOSS_BASE_URL` | `https://openapi.tossinvest.com` | 토스 API 주소 |

## 값 만드는 법 (둘 다 *직접 타이핑하지 말고 명령으로 생성*)

### PAIRING_KEY — 안전한 랜덤이면 OK (형식 자유)
손으로 치면 약하니 명령으로 생성:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
→ 나온 값을 `.env`의 `PAIRING_KEY` + 앱 온보딩 1단계에 **같은 값** 붙여넣기.

### TOSS_KEY_ENC_KEY — 아무 문자열 ❌, **반드시 Fernet 형식**(32바이트 base64)
막 지은 문자열을 넣으면 앱이 에러남. 무조건 생성기로:
```powershell
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
(`cryptography` 필요 → `uv sync` 후 `uv run`으로. 안 깔렸으면 `pip install cryptography` 먼저)
→ 출력값 그대로 붙여넣기. ⚠️ **이 키를 잃어버리거나 바꾸면** DB에 저장된 토스 키를 **복호화 못 함** → 토스 재연결 필요. 잘 보관.

> 🔒 이 명령들은 *네 PC에서 직접* 실행 — 비밀이 채팅/로그에 안 남게.

---

## ⚠️ 중요: 토스 App/Secret 키는 .env에 넣지 않음
- 토스 **App Key / Secret Key**는 `.env`에 **안 들어가.**
- → **앱 온보딩 2단계에서 입력** → 백엔드가 받아서 **암호화 후 DB에 저장**.
- `.env`엔 위 **4개만**.

## .env.example (커밋되는 템플릿) 예시
```
DATABASE_URL=postgresql+psycopg://stockbot:stockbot@localhost:5432/stockbot
PAIRING_KEY=
TOSS_KEY_ENC_KEY=
TOSS_BASE_URL=https://openapi.tossinvest.com
```
