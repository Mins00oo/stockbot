/**
 * Number/money formatting mirrored from the handoff prototype's
 * `fmt()` / `money()` so the look matches exactly.
 *
 *   KRW  -> "₩71,200"            (rounded integer)
 *   USD  -> "$214.30"            (2 decimals)
 *   pct  -> "+1.2%" / "-2.1%"
 */
import type { Currency } from "@/types/api";

export function fmtInt(n: number): string {
  return Math.round(n).toLocaleString("en-US");
}

export function money(currency: Currency, n: number): string {
  if (currency === "KRW") return "₩" + fmtInt(n);
  return (
    "$" +
    n.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  );
}

/** Always-KRW formatter for totals (totalValueKrw / totalPnlKrw). */
export function krw(n: number): string {
  return "₩" + fmtInt(n);
}

/** "+1.2%" / "-2.1%" with sign. */
export function signedPct(rate: number): string {
  const sign = rate >= 0 ? "+" : "-";
  return sign + Math.abs(rate).toFixed(1) + "%";
}

/** "+₩320,000 (+2.6%)" style summary for totals. */
export function signedKrwWithPct(amount: number, rate: number): string {
  const up = amount >= 0;
  return (
    (up ? "+" : "-") +
    "₩" +
    fmtInt(Math.abs(amount)) +
    " (" +
    (rate >= 0 ? "+" : "-") +
    Math.abs(rate).toFixed(1) +
    "%)"
  );
}

/** First grapheme of a name, used as logo initial fallback. */
export function initial(name: string): string {
  return name ? Array.from(name)[0] : "?";
}

/**
 * Deterministic brand-ish background color for a symbol's logo chip.
 * (Backend doesn't send a brand color, so we derive a stable one.)
 */
const LOGO_PALETTE = [
  "#1428A0",
  "#E60012",
  "#76B900",
  "#0078D4",
  "#03C75A",
  "#E82127",
  "#845EF7",
  "#12B886",
  "#FF922B",
  "#0866FF",
  "#1D1D1F",
  "#A50034",
];

export function logoBgFor(symbol: string): string {
  let h = 0;
  for (let i = 0; i < symbol.length; i++) {
    h = (h * 31 + symbol.charCodeAt(i)) >>> 0;
  }
  return LOGO_PALETTE[h % LOGO_PALETTE.length];
}

/** Market label for display; backend gives "KR"|"US". */
export function marketLabel(market: "KR" | "US"): string {
  return market === "KR" ? "국내" : "미국";
}
