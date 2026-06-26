import { useState } from "react";
import { Text, View } from "react-native";
import { Gesture, GestureDetector } from "react-native-gesture-handler";

import { colors } from "@/theme/tokens";

interface PriceChartProps {
  closes: number[];
  volumes: number[];
  times: string[];
  /** overall direction of the period — colors the price line (up=red, down=blue). */
  up: boolean;
  width: number;
  /** format a price value for the scrub tooltip (currency-aware). */
  formatPrice: (n: number) => string;
  /** format a point's timestamp for the scrub tooltip (date or intraday time). */
  formatStamp: (t: string) => string;
  lineHeight?: number;
  volHeight?: number;
}

const LINE_THICKNESS = 2;
const VOL_UP = "#FAD4D8"; // 상승 거래량 (red tint)
const VOL_DOWN = "#CFE0FB"; // 하락 거래량 (blue tint)
const PILL_W = 116;
const TIP_BAND = 40; // reserved row above the line for the scrub tooltip

/**
 * Price line + volume histogram drawn with plain Views (no SVG dependency).
 * Drag horizontally over the line to scrub: a crosshair + dot follow the finger
 * and a tooltip shows that point's price/date. The Pan only claims horizontal
 * moves (activeOffsetX) and yields vertical ones to the page scroll
 * (failOffsetY); it's inset from the screen edge so it never fights the
 * stack's swipe-back. Release clears the scrub.
 */
export function PriceChart({
  closes,
  volumes,
  times,
  up,
  width,
  formatPrice,
  formatStamp,
  lineHeight = 128,
  volHeight = 38,
}: PriceChartProps) {
  const n = closes.length;
  const lineColor = up ? colors.up : colors.down;
  const [active, setActive] = useState<number | null>(null);

  // --- price line geometry ---
  const min = n ? Math.min(...closes) : 0;
  const max = n ? Math.max(...closes) : 0;
  const span = max - min || 1;
  const x = (i: number) => (n > 1 ? (i / (n - 1)) * width : width / 2);
  const y = (v: number) => lineHeight - ((v - min) / span) * lineHeight;

  const segments = [] as { left: number; top: number; len: number; rad: number }[];
  for (let i = 0; i < n - 1; i++) {
    const ax = x(i);
    const ay = y(closes[i]);
    const bx = x(i + 1);
    const by = y(closes[i + 1]);
    const dx = bx - ax;
    const dy = by - ay;
    const len = Math.hypot(dx, dy) || 1;
    segments.push({
      left: (ax + bx) / 2 - len / 2,
      top: (ay + by) / 2 - LINE_THICKNESS / 2,
      len,
      rad: Math.atan2(dy, dx),
    });
  }

  // --- scrubbing ---
  const xToIndex = (px: number) => {
    if (n <= 1) return 0;
    return Math.max(0, Math.min(n - 1, Math.round((px / width) * (n - 1))));
  };
  // runOnJS(true): run callbacks on the JS thread so we can setState directly
  // (no reanimated worklet needed).
  const pan = Gesture.Pan()
    .runOnJS(true)
    .activeOffsetX([-8, 8])
    .failOffsetY([-12, 12])
    .onStart((e) => setActive(xToIndex(e.x)))
    .onUpdate((e) => setActive(xToIndex(e.x)))
    .onFinalize(() => setActive(null));

  const cx = active != null ? x(active) : 0;
  const cy = active != null ? y(closes[active]) : 0;
  const pillLeft = Math.max(0, Math.min(width - PILL_W, cx - PILL_W / 2));

  // --- volume histogram ---
  const maxVol = volumes.length ? Math.max(...volumes, 0) : 0;
  const barW = n ? width / n : 0;

  return (
    <View>
      {/* tooltip band — sits above the line so the pill never covers the chart */}
      <View style={{ height: TIP_BAND }}>
        {active != null ? (
          <View
            style={{
              position: "absolute",
              left: pillLeft,
              top: 0,
              width: PILL_W,
              backgroundColor: colors.dark,
              borderRadius: 8,
              paddingVertical: 4,
              paddingHorizontal: 8,
            }}
          >
            <Text
              style={{ color: "#fff", fontSize: 13, fontWeight: "700", textAlign: "center" }}
            >
              {formatPrice(closes[active])}
            </Text>
            <Text
              style={{ color: "#C4CCD4", fontSize: 10.5, textAlign: "center", marginTop: 1 }}
            >
              {formatStamp(times[active] ?? "")}
            </Text>
          </View>
        ) : null}
      </View>

      <GestureDetector gesture={pan}>
        <View style={{ width, height: lineHeight }} collapsable={false}>
          {n === 1 ? (
            <View
              style={{
                position: "absolute",
                left: width / 2 - 2,
                top: lineHeight / 2 - 2,
                width: 4,
                height: 4,
                borderRadius: 2,
                backgroundColor: lineColor,
              }}
            />
          ) : (
            segments.map((s, i) => (
              <View
                key={i}
                style={{
                  position: "absolute",
                  left: s.left,
                  top: s.top,
                  width: s.len,
                  height: LINE_THICKNESS,
                  borderRadius: LINE_THICKNESS / 2,
                  backgroundColor: lineColor,
                  transform: [{ rotate: `${s.rad}rad` }],
                }}
              />
            ))
          )}

          {active != null ? (
            <>
              {/* crosshair */}
              <View
                style={{
                  position: "absolute",
                  left: cx,
                  top: 0,
                  width: 1,
                  height: lineHeight,
                  backgroundColor: colors.text.icon,
                }}
              />
              {/* point dot */}
              <View
                style={{
                  position: "absolute",
                  left: cx - 4,
                  top: cy - 4,
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: lineColor,
                  borderWidth: 2,
                  borderColor: "#fff",
                }}
              />
            </>
          ) : null}
        </View>
      </GestureDetector>

      {maxVol > 0 ? (
        <View
          style={{
            width,
            height: volHeight,
            marginTop: 8,
            flexDirection: "row",
            alignItems: "flex-end",
          }}
        >
          {volumes.map((v, i) => {
            const barUp = i === 0 ? up : closes[i] >= closes[i - 1];
            const h = Math.max(maxVol ? (v / maxVol) * volHeight : 0, v > 0 ? 1 : 0);
            return (
              <View
                key={i}
                style={{
                  width: Math.max(barW - 0.5, 0.5),
                  height: h,
                  marginRight: 0.5,
                  backgroundColor: barUp ? VOL_UP : VOL_DOWN,
                  borderRadius: 1,
                }}
              />
            );
          })}
        </View>
      ) : null}
    </View>
  );
}
