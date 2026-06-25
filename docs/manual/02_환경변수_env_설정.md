# 02. 환경변수(.env) 설정

`.env` 파일은 **비밀·환경 설정**을 담음. **git에 안 올라감**(.gitignore). `.env.example`을 복사해서 값을 채운다.

## .env 항목 (4개)

| 키 | 예시/형식 | 설명 |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://stockbot:stockbot@localhost:5432/stockbot` | DB 접속 주소. **docker-compose의 계정/DB명과 일치해야 함** |
| `PAIRING_KEY` | (긴 랜덤 문자열) | **앱 ↔ 백엔드 인증용 비밀.** 내가 정함. 앱 온보딩 1단계에도 **같은 값** 입력 |
| `TOSS_KEY_ENC_KEY` | (Fernet 키) | 토스 키를 **암호화**해 DB에 저장할 때 쓰는 키 |
| `TOSS_BASE_URL` | `https://openapi.tossinvest.com` | 토스 API 주소 |

## 값 만드는 법

### PAIRING_KEY
아무 긴 랜덤 문자열. 예: 비밀번호 생성기, 또는:
```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### TOSS_KEY_ENC_KEY (암호화 키)
```powershell
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
→ 출력값을 그대로 붙여넣기. **이 키를 잃어버리면 저장된 토스 키를 복호화 못 함** — 잘 보관.

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
