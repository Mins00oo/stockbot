# Stock Bot — 문서 (docs)

개인 AI 주식 비서 **Stock Bot** 의 설계 문서 모음.

## 구조

```
docs/
├─ overview/      제품 전체 설계 (큰 그림)
│  └─ product-spec.md      제품 설계 스펙 v1 — 목적·원칙·범위·구조·feasibility·기능·데이터모델·로드맵
├─ design/        설계 (기술스택·API·플로우·화면)
│  ├─ tech-stack.md        기술 스택 (백엔드·프론트 확정)
│  ├─ API_정의서.md        API 계약 (엔드포인트·요청/응답·에러)
│  ├─ news-pipeline.md     뉴스 수집→중복제거→종목매칭→처리구조 상세 플로우
│  └─ screens/             앱 화면 디자인(핸드오프) + 앱 아이콘
├─ manual/        실행·셋업 매뉴얼 (한글, 00~04)
└─ research/      조사·근거 자료 (의사결정의 근거)
   └─ news-sources.md      뉴스/공시 소스 feasibility 정리 (2026-06)
```

## 읽는 순서

1. **`overview/product-spec.md`** — 무엇을 왜 만드는가, 전체 그림부터.
2. **`design/news-pipeline.md`** — 가장 복잡한 뉴스 서브시스템의 동작 플로우.
3. **`research/news-sources.md`** — 위 설계가 근거하는 소스 조사 결과.

## 상태

- 2026-06-24: 제품 설계 v1 완료(`overview/product-spec.md`). 구현 전(기획 단계).
- 2026-06-24: 뉴스 서브시스템 상세 설계 완료(`design/news-pipeline.md` + `research/news-sources.md`).
- 2026-06-25: 기술 스택(백엔드·프론트)·디렉토리 구조 확정(`design/tech-stack.md`). API 정의서 작성(`design/API_정의서.md`). 실행 매뉴얼(`manual/`).
- 2026-06-25: 오늘 빌드 범위 = [키 연결 → 홈 보유목록]. 백엔드(core·auth·portfolio최소) + 프론트(온보딩·홈) 병렬 빌드 준비 완료.
