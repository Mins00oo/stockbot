# Stock Bot — Frontend (Expo / React Native)

토스 스타일 주식 비서 앱. Expo SDK 56 + Expo Router (파일 기반) + TypeScript.

오늘 슬라이스 범위: **온보딩(인트로 → 페어링 → 토스 키 → 연결 → 완료) + 홈(보유 종목)**.
나머지 탭(탐색/관심/전체)은 플레이스홀더예요.

## 설치 & 실행

> 이 프로젝트는 **development build** 기반이에요 (Expo Go 미사용 — tech-stack 결정).

```bash
# 1) 의존성 설치
npm install

# 2) expo-* 패키지 버전을 설치된 SDK(56)에 정확히 맞추기 (중요!)
#    package.json의 expo-* / react / react-native 버전은 "근사치"예요.
#    아래 명령이 SDK 56과 호환되는 정확한 버전으로 정렬해 줍니다.
npx expo install --fix

# 3) 환경변수
cp .env.example .env
#    실기기로 개발 시 EXPO_PUBLIC_API_URL을 PC의 LAN IP로 바꾸세요.
#    예: EXPO_PUBLIC_API_URL=http://192.168.0.10:8000

# 4) 네이티브 빌드 실행 (dev client)
npx expo run:ios       # 또는
npx expo run:android
#    이후엔: npm start  (= expo start --dev-client)
```

## 구조

```
app/                         # Expo Router (파일 기반 라우팅)
  _layout.tsx                # QueryClientProvider + SafeArea + 인증 게이트 부트스트랩
  index.tsx                  # 페어링 키 유무로 onboarding ↔ tabs 리다이렉트
  onboarding/
    _layout.tsx              # 탭바 없는 스택 (connecting/done은 뒤로가기 잠금)
    intro.tsx                # 앱 소개 + 연결 시작
    pairing.tsx              # 페어링 키 입력 (RHF) → POST /auth/pairing/verify → SecureStore 저장
    toss-key.tsx             # App/Secret Key 입력 (RHF+zod, secret 마스킹 토글)
    connecting.tsx           # POST /auth/toss/connect 진행 + 단계 표시
    done.tsx                 # 성공 + 보유 요약(useHoldings) → 홈
  (tabs)/
    _layout.tsx              # 하단 탭바 (홈/탐색/관심/전체)
    home.tsx                 # 자산 히어로 카드 + 보유 종목 리스트 (useHoldings)
    explore.tsx / watchlist.tsx / settings.tsx   # 플레이스홀더

src/
  api/        client.ts(axios+인터셉터), auth.ts, portfolio.ts
  hooks/      useHoldings, usePairingVerify, useConnectToss
  stores/     authStore.ts (zustand: paired/connected/hydrated)
  lib/        secureStore.ts(페어링 키), format.ts(₩/$ 포맷)
  theme/      tokens.ts (디자인 토큰)
  types/      api.ts (zod 스키마 + 추론 타입 — API 정의서와 동일 계약)
  components/  PrimaryButton, Card, LogoChip, HoldingRow, TextField, InfoBox,
               StepIndicator, BackButton, Placeholder
```

## 디자인 토큰

핸드오프 토큰을 `tailwind.config.js`(NativeWind 클래스)와 `src/theme/tokens.ts`(인라인
스타일)에 양쪽으로 매핑했어요.

**한국식 색상 컨벤션**: 상승/이익 = 빨강 `#F04452`, 하락/손실 = 파랑 `#3182F6`.
`pnlColor(value)` 헬퍼가 부호로 색을 결정해요.

## 폰트 (Pretendard) — TODO

핸드오프는 **Pretendard**를 사용해요. 현재 `fontFamily: ["Pretendard", "System"]`로
매핑되어 있지만 폰트 파일은 아직 번들되지 않았어요 (시스템 폰트로 폴백).

권장 셋업 (둘 중 하나):
- **번들**: Pretendard `.otf`/`.ttf`를 `assets/fonts/`에 넣고 `expo-font`의
  `useFonts` 또는 config plugin으로 로드. (네이티브 빌드 필요)
- CDN(웹 전용)은 RN 네이티브에선 동작하지 않으니 번들 방식을 사용하세요.

폰트 출처: https://github.com/orioncactus/pretendard

## 백엔드 계약

`src/types/api.ts`의 zod 스키마가 `docs/design/API_정의서.md`와 1:1로 대응해요.
axios 인터셉터가 `X-Pairing-Key`를 자동 첨부하고, 에러 응답
`{error:{code,message}}`를 `ApiError(code, message, status)`로 정규화해요.

오늘 사용하는 엔드포인트:
- `POST /auth/pairing/verify` (헤더로 키)
- `POST /auth/toss/connect` (appKey/secretKey)
- `GET  /portfolio/holdings`

## 보안 메모

- **페어링 키만** 기기에 저장돼요 (`expo-secure-store`).
- **토스 API 키는 기기에 저장하지 않아요** — 백엔드가 암호화 저장.
- 온보딩 보안 문구는 tech-stack 수정안을 적용했어요:
  "암호화되어 안전하게 저장" / "주문 기능은 사용하지 않아요".

## 아이콘

앱 아이콘은 `assets/icon.png` (= `docs/.../app_icon/icon-insight-1024.png` 복사본).
`splash.png` / `adaptive-icon.png`도 임시로 같은 마스터를 사용 중 —
필요 시 전용 스플래시/어댑티브 전경·배경 레이어로 교체하세요.
