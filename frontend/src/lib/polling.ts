/**
 * Foreground polling interval (ms) for live market data.
 * Used by: home holdings (`useHoldings`) and the stock-detail screen
 * (quote/orderbook/trades/chart) once built. Single source so home & detail stay
 * in sync — bump this one value (e.g. 1500) if requests get too frequent.
 */
export const POLL_INTERVAL_MS = 1000;
