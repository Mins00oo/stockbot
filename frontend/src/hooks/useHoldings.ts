import { useQuery } from "@tanstack/react-query";

import { getHoldings } from "@/api/portfolio";
import type { HoldingsResponse } from "@/types/api";

export const holdingsQueryKey = ["portfolio", "holdings"] as const;

export function useHoldings() {
  return useQuery<HoldingsResponse>({
    queryKey: holdingsQueryKey,
    queryFn: getHoldings,
    // 홈을 보는 동안 3초마다 /holdings 재조회 (가격·평가·손익·총합 전부 토스 raw).
    // 가드: 포그라운드일 때만 폴링(refetchIntervalInBackground=false), 화면 포커스 복귀 시 갱신.
    // TODO(가드): 장 시간대에만 폴링하도록 market-calendar 연동 (마감/주말엔 멈춤).
    refetchInterval: 3_000,
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
}
