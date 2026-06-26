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

/** "+₩30,000" / "-₩2,800" — signed KRW amount (per-holding pnl in KRW). */
export function signedKrw(amount: number): string {
  return (amount >= 0 ? "+" : "-") + "₩" + fmtInt(Math.abs(amount));
}

/**
 * Share quantity. Integers stay clean ("5"); fractional shares (US) keep up to
 * 6 decimals with trailing zeros trimmed ("0.128308", "1.25").
 */
export function qty(n: number): string {
  return n.toLocaleString("en-US", { maximumFractionDigits: 6 });
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

/** Narrow a raw Toss currency string to our union (anything non-USD -> KRW). */
export function asCurrency(c: string | null | undefined): Currency {
  return c === "USD" ? "USD" : "KRW";
}

/** "+$1.23" / "-₩1,000" — signed money in the value's own currency. */
export function signedMoney(currency: Currency, n: number): string {
  return (n >= 0 ? "+" : "-") + money(currency, Math.abs(n));
}

/**
 * Compact market-cap string.
 *   KRW -> "412조 3,456억" (조=1e12, 억=1e8)
 *   USD -> "$3.42T" / "$1.20B" / "$5.30M"
 */
export function marketCapStr(currency: Currency, n: number): string {
  if (currency === "KRW") {
    const jo = Math.floor(n / 1e12);
    const eok = Math.round((n - jo * 1e12) / 1e8);
    if (jo > 0) return `${fmtInt(jo)}조${eok > 0 ? " " + fmtInt(eok) + "억" : ""}`;
    if (eok > 0) return `${fmtInt(eok)}억`;
    return krw(n);
  }
  if (n >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9) return "$" + (n / 1e9).toFixed(2) + "B";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(2) + "M";
  return money("USD", n);
}

/** "오후 1:23:45" style HH:MM:SS from an ISO/parseable timestamp (체결 시각). */
export function timeOfDay(ts: string): string {
  const d = new Date(ts);
  if (isNaN(d.getTime())) return ts;
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}
