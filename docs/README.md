# Stock Bot — 문서 (docs)

개인 AI 주식 비서 **Stock Bot** 의 설계 문서 모음.

## 구조

```
docs/
├─ overview/      제품 전체 설계 (큰 그림)
│  └─ product-spec.md      제품 설계 스펙 v1 — 목적·원칙·범위·구조·feasibility·기능·데이터모델·로드맵
├─ design/        서브시스템별 상세 설계 (플로우)
│  └─ news-pipeline.md     뉴스 수집→중복제거→종목매칭→처리구조 상세 플로우
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
