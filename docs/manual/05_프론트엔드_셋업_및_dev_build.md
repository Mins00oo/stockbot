# 05. 프론트엔드(앱) 셋업 및 dev build

> 표기 규칙: **[필수]** = 꼭 해야 함 / **[선택]** = 상황에 따라. 각 단계에 *용도*를 적음.
> ※ 앱 코드는 빌드 단계에서 생성됨. 이 매뉴얼대로 동작하게 맞춰 만듦.
> ※ Expo Go는 안 씀(SDK56 호환 이슈 + 한계). **development build**(내 전용 앱)로 개발.

## 전제 (PC에 1회)
- **[필수] Node.js — 22 LTS 권장** (최소 `20.19.4+` / SDK56·RN0.85가 요구). *용도*: JS 패키지·Expo 실행. ⚠️ 버전 낮으면 `npm install`은 돼도 `expo start`에서 터질 수 있음. (설치: `winget install OpenJS.NodeJS.LTS` 또는 nodejs.org)
- **[선택] Expo 계정** — *용도*: EAS(클라우드) 빌드 쓸 때 필요. (무료 가입)
- **[선택] Android Studio** — *용도*: dev build를 *로컬*에서 만들 때만(Windows에서 Android 한정).

---

## 처음 한 번 (순서대로)

### 1) 프론트 폴더 이동 — [필수]
```powershell
cd D:\work\project\workspace\Prj\stockbot\frontend
```
*용도*: 이후 명령을 이 폴더에서 실행.

### 2) 의존성 설치 — [필수]
```powershell
npm install
```
*용도*: `package.json`의 라이브러리 설치 → `node_modules` 생성. (`.npmrc`가 커밋돼 있어 peer 충돌 자동 처리 — 플래그 불필요.)

### 3) (참고) expo 패키지 버전 정렬 — [선택, 보통 불필요]
```powershell
npx expo install --fix
```
*용도*: expo 패키지가 SDK와 어긋났을 때 정렬. **현재 저장소는 이미 SDK56 정답 버전으로 맞춰 커밋돼 있어 보통 안 해도 됨.** (나중에 SDK 올리거나 버전 꼬였을 때만.)

### 4) `.env` 만들기 — [필수]
```powershell
Copy-Item .env.example .env
# .env 열어서 EXPO_PUBLIC_API_URL 설정
```
*용도*: 앱이 백엔드를 부를 주소. **실기기 = PC의 LAN IP**(`http://192.168.x.x:8000`), **시뮬레이터 = `http://localhost:8000`**.

### 5) development build 만들기 — [필수, 1회] (방법 A 또는 B 중 택1)
*용도*: Expo Go 대신 **내 프로젝트 전용 앱**을 빌드해 폰에 설치.

**방법 A — EAS 클라우드 빌드 [권장]** (PC에 네이티브 툴 불필요)
```powershell
npx eas login                                              # [필수, A] Expo 계정 로그인 (1회)
npx eas build --profile development --platform android     # 또는 --platform ios
```
→ 빌드 완료되면 받은 링크/QR로 폰에 설치.

**방법 B — 로컬 빌드 [선택]** (Android만, Android Studio 필요)
```powershell
npx expo run:android
```

### 6) 개발 서버 시작 — [필수]
```powershell
npx expo start --dev-client
```
*용도*: 코드 변경을 실시간 반영. **5에서 깐 dev build 앱**으로 이 서버에 접속.

### 7) 동작 확인 — [선택(권장)]
앱에서 온보딩(페어링 키 → 토스 키) → 홈에 보유종목 뜨는지.
*용도*: 잘 도는지 확인. (백엔드가 떠 있어야 함 — `01` 참고)

---

## 폰별 주의 (중요)
| 플랫폼 | dev build 방법 | Windows에서 |
|---|---|---|
| **Android** | EAS(APK) 또는 로컬(`expo run:android`) | ✅ 둘 다 가능 |
| **iOS** | EAS + **Apple 계정**(실기기 설치 provisioning) | ⚠️ 로컬 iOS 빌드는 **Mac 필요**(Windows 불가) → EAS 사용 |

## 이후 다시 실행할 때 (dev build 이미 설치됨)
```powershell
npx expo start --dev-client      # [필수] 개발 서버만 다시
```
- 라이브러리 추가/native 변경했을 때만 `npm install` → dev build 재생성.

## 페어링 키 / 토스 키 (앱에서 입력)
- **페어링 키**: 백엔드 `.env`의 `PAIRING_KEY`와 **같은 값**을 온보딩 1단계에 입력.
- **토스 App/Secret 키**: 온보딩 2단계에 입력 → 백엔드가 암호화해 DB 저장(앱엔 저장 안 됨).

문제 생기면 → `04_문제해결_FAQ.md`
