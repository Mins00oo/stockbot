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
