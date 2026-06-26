import { api } from "./client";

import {
  ChartResponseSchema,
  OrderbookSchema,
  QuoteSchema,
  StockDetailSchema,
  TradesResponseSchema,
  type ChartResponse,
  type Orderbook,
  type Quote,
  type StockDetail,
  type TradesResponse,
} from "@/types/api";

export type ChartRange = "1D" | "1W" | "1M" | "3M" | "1Y";

/** UI 기간 라벨 <-> API range. 기본 3달(3M). */
export const CHART_RANGES: { key: ChartRange; label: string }[] = [
  { key: "1D", label: "1일" },
  { key: "1W", label: "1주" },
  { key: "1M", label: "1달" },
  { key: "3M", label: "3달" },
  { key: "1Y", label: "1년" },
];

function path(symbol: string, suffix = ""): string {
  return `/stocks/${encodeURIComponent(symbol)}${suffix}`;
}

/** 3-A① GET /stocks/{symbol} — 개장 시점 상세(정체성·펀더멘털·52주·상하한가·KR 경고). */
export async function getStockDetail(
  symbol: string,
  market?: string,
): Promise<StockDetail> {
  const res = await api.get(path(symbol), {
    params: market ? { market } : undefined,
  });
  return StockDetailSchema.parse(res.data);
}

/** 3-A② GET /stocks/{symbol}/quote — 실시간 시세(폴링 대상). */
export async function getQuote(symbol: string, market?: string): Promise<Quote> {
  const res = await api.get(path(symbol, "/quote"), {
    params: market ? { market } : undefined,
  });
  return QuoteSchema.parse(res.data);
}

/** 3-A③ GET /stocks/{symbol}/chart?range= — 기간별 캔들 + 기간수익률. */
export async function getChart(
  symbol: string,
  range: ChartRange,
): Promise<ChartResponse> {
  const res = await api.get(path(symbol, "/chart"), { params: { range } });
  return ChartResponseSchema.parse(res.data);
}

/** 3-A④ GET /stocks/{symbol}/orderbook — 10단계 호가 스냅샷. */
export async function getOrderbook(symbol: string): Promise<Orderbook> {
  const res = await api.get(path(symbol, "/orderbook"));
  return OrderbookSchema.parse(res.data);
}

/** 3-A⑤ GET /stocks/{symbol}/trades — 최근 체결 스냅샷. */
export async function getTrades(symbol: string): Promise<TradesResponse> {
  const res = await api.get(path(symbol, "/trades"));
  return TradesResponseSchema.parse(res.data);
}
