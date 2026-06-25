import { api } from "./client";

import { HoldingsResponseSchema, type HoldingsResponse } from "@/types/api";

/**
 * ④ GET /portfolio/holdings
 * Returns total value/pnl + per-holding rows.
 * Sort the rows by evalAmountKrw desc (정렬·합계용 원화환산 기준).
 */
export async function getHoldings(): Promise<HoldingsResponse> {
  const res = await api.get("/portfolio/holdings");
  const data = HoldingsResponseSchema.parse(res.data);
  return {
    ...data,
    holdings: [...data.holdings].sort(
      (a, b) => b.evalAmountKrw - a.evalAmountKrw,
    ),
  };
}
