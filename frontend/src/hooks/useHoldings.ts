import { useQuery } from "@tanstack/react-query";

import { getHoldings } from "@/api/portfolio";
import { POLL_INTERVAL_MS } from "@/lib/polling";
import type { HoldingsResponse } from "@/types/api";

export const holdingsQueryKey = ["portfolio", "holdings"] as const;

export function useHoldings() {
  return useQuery<HoldingsResponse>({
    queryKey: holdingsQueryKey,
    queryFn: getHoldings,
    // 홈을 보는 동안 주기적으로 /holdings 재조회 (가격·평가·손익·총합 전부 토스 raw).
    // 주기는 POLL_INTERVAL_MS 한 곳에서 관리(홈·상세 공통) — 너무 잦으면 거기서 1.5초 등으로.
    // 가드: 포그라운드일 때만 폴링(refetchIntervalInBackground=false), 화면 포커스 복귀 시 갱신.
    // TODO(가드): 장 시간대에만 폴링하도록 market-calendar 연동 (마감/주말엔 멈춤).
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
}
