import { useQuery } from "@tanstack/react-query";

import {
  getChart,
  getOrderbook,
  getQuote,
  getStockDetail,
  getTrades,
  type ChartRange,
} from "@/api/stocks";
import { POLL_INTERVAL_MS } from "@/lib/polling";

/**
 * Stock-detail data hooks.
 * - detail: semi-static (identity·52w·fundamentals) → long staleTime, no poll.
 * - quote / orderbook / trades: live snapshots → poll at POLL_INTERVAL_MS
 *   (foreground only; shared with home so cadence stays in one place).
 * - chart: refetched on range change (range is in the key); short staleTime.
 *
 * orderbook/trades are gated by `enabled` so only the visible 호가/체결 탭 polls.
 */

const LIVE = {
  refetchInterval: POLL_INTERVAL_MS,
  refetchIntervalInBackground: false,
  staleTime: 0,
} as const;

export function useStockDetail(symbol: string, market?: string) {
  return useQuery({
    queryKey: ["stock", "detail", symbol, market ?? null],
    queryFn: () => getStockDetail(symbol, market),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  });
}

export function useQuote(symbol: string, market?: string) {
  return useQuery({
    queryKey: ["stock", "quote", symbol, market ?? null],
    queryFn: () => getQuote(symbol, market),
    enabled: !!symbol,
    ...LIVE,
  });
}

export function useChart(symbol: string, range: ChartRange) {
  return useQuery({
    queryKey: ["stock", "chart", symbol, range],
    queryFn: () => getChart(symbol, range),
    enabled: !!symbol,
    staleTime: 30_000,
  });
}

export function useOrderbook(symbol: string, enabled: boolean) {
  return useQuery({
    queryKey: ["stock", "orderbook", symbol],
    queryFn: () => getOrderbook(symbol),
    enabled: enabled && !!symbol,
    ...LIVE,
  });
}

export function useTrades(symbol: string, enabled: boolean) {
  return useQuery({
    queryKey: ["stock", "trades", symbol],
    queryFn: () => getTrades(symbol),
    enabled: enabled && !!symbol,
    ...LIVE,
  });
}
