/**
 * API contract types + zod schemas, matching docs/design/API_정의서.md.
 * Zod schemas are reused to validate runtime responses (defensive parsing).
 */
import { z } from "zod";

/* ---------- Standard error body ---------- */
// { "error": { "code": "...", "message": "..." } }
export const ApiErrorBodySchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
  }),
});
export type ApiErrorBody = z.infer<typeof ApiErrorBodySchema>;

/** Known error codes from the catalog. */
export type ApiErrorCode =
  | "UNAUTHORIZED"
  | "VALIDATION_ERROR"
  | "TOSS_AUTH_FAILED"
  | "NOT_CONNECTED"
  | "TOSS_UNAVAILABLE"
  | "INTERNAL"
  | "NETWORK"
  | "UNKNOWN";

/* ---------- ② POST /auth/pairing/verify ---------- */
export const PairingVerifyResponseSchema = z.object({
  valid: z.boolean(),
});
export type PairingVerifyResponse = z.infer<typeof PairingVerifyResponseSchema>;

/* ---------- ③ POST /auth/toss/connect ---------- */
export const TossConnectRequestSchema = z.object({
  appKey: z.string().min(4, "App Key를 입력해 주세요"),
  secretKey: z.string().min(4, "Secret Key를 입력해 주세요"),
});
export type TossConnectRequest = z.infer<typeof TossConnectRequestSchema>;

export const TossConnectResponseSchema = z.object({
  connected: z.boolean(),
  account: z.object({
    seq: z.string(),
    name: z.string(),
  }),
});
export type TossConnectResponse = z.infer<typeof TossConnectResponseSchema>;

/* ---------- GET /auth/status (launch gate) ---------- */
export const AuthStatusResponseSchema = z.object({
  connected: z.boolean(),
});
export type AuthStatusResponse = z.infer<typeof AuthStatusResponseSchema>;

/* ---------- ④ GET /portfolio/holdings ---------- */
export const MarketSchema = z.enum(["KR", "US"]);
export type Market = z.infer<typeof MarketSchema>;

export const CurrencySchema = z.enum(["KRW", "USD"]);
export type Currency = z.infer<typeof CurrencySchema>;

export const HoldingSchema = z.object({
  symbol: z.string(),
  name: z.string(),
  market: MarketSchema,
  quantity: z.number(),
  avgPrice: z.number(),
  currentPrice: z.number(),
  evalAmount: z.number(),
  evalAmountKrw: z.number(),
  pnl: z.number(),
  pnlKrw: z.number(),
  pnlRate: z.number(),
  currency: CurrencySchema,
});
export type Holding = z.infer<typeof HoldingSchema>;

export const HoldingsResponseSchema = z.object({
  totalValueKrw: z.number(),
  totalPnlKrw: z.number(),
  totalPnlRate: z.number(),
  totalPurchaseKrw: z.number(),
  holdings: z.array(HoldingSchema),
});
export type HoldingsResponse = z.infer<typeof HoldingsResponseSchema>;

/* ---------- 3-A. GET /stocks/{symbol}* (종목 상세) ---------- */
// Backend types `currency` as a free string on these (Toss raw) — keep it loose
// here so an unexpected value never fails the whole parse; narrow via asCurrency.

export const PriceLimitsSchema = z.object({
  upper: z.number().nullable(),
  lower: z.number().nullable(),
});

export const FundamentalsSchema = z.object({
  marketCap: z.number().nullable(),
  week52High: z.number().nullable(),
  week52Low: z.number().nullable(),
  per: z.number().nullable(),
  pbr: z.number().nullable(),
  eps: z.number().nullable(),
  dividendYield: z.number().nullable(), // percent (1.9 = 1.9%)
});

export const TradingWarningSchema = z.object({
  type: z.string(),
  label: z.string(),
});

export const StockDetailSchema = z.object({
  symbol: z.string(),
  name: z.string(),
  market: MarketSchema,
  exchange: z.string().nullable(),
  currency: z.string(),
  industry: z.string().nullable(),
  prevClose: z.number().nullable(),
  priceLimits: PriceLimitsSchema,
  fundamentals: FundamentalsSchema,
  warnings: z.array(TradingWarningSchema),
});
export type StockDetail = z.infer<typeof StockDetailSchema>;
export type Fundamentals = z.infer<typeof FundamentalsSchema>;
export type TradingWarning = z.infer<typeof TradingWarningSchema>;

export const QuoteSchema = z.object({
  symbol: z.string(),
  price: z.number(),
  prevClose: z.number().nullable(),
  change: z.number().nullable(),
  changeRate: z.number().nullable(),
  volume: z.number().nullable(),
  currency: z.string(),
  krwPrice: z.number().nullable(), // US only
});
export type Quote = z.infer<typeof QuoteSchema>;

export const ChartPointSchema = z.object({
  t: z.string(),
  close: z.number(),
  volume: z.number(),
});
export const ChartResponseSchema = z.object({
  range: z.string(),
  currency: z.string(),
  points: z.array(ChartPointSchema),
  periodReturn: z.number().nullable(),
});
export type ChartResponse = z.infer<typeof ChartResponseSchema>;

export const OrderbookLevelSchema = z.object({
  price: z.number(),
  volume: z.number(),
});
export const OrderbookSchema = z.object({
  asks: z.array(OrderbookLevelSchema),
  bids: z.array(OrderbookLevelSchema),
  currency: z.string().nullable(),
});
export type Orderbook = z.infer<typeof OrderbookSchema>;
export type OrderbookLevel = z.infer<typeof OrderbookLevelSchema>;

export const TradeSchema = z.object({
  time: z.string(),
  price: z.number(),
  volume: z.number(),
});
export const TradesResponseSchema = z.object({
  trades: z.array(TradeSchema),
  currency: z.string().nullable(),
});
export type TradesResponse = z.infer<typeof TradesResponseSchema>;
export type Trade = z.infer<typeof TradeSchema>;
