/**
 * Design tokens mirrored from the handoff spec so they're usable in plain TS
 * (StyleSheet, inline color props) where Tailwind class names aren't convenient.
 * Source: docs/design/screens/design_handoff_toss_stock_assistant/README.md
 *
 * Korean market convention:
 *   상승/이익 = UP  = red  (#F04452)
 *   하락/손실 = DOWN = blue (#3182F6)
 */
export const colors = {
  primary: "#3182F6",
  primaryBg: "#EAF2FE",

  bg: "#F2F4F6",
  edge: "#E5E8EB",
  card: "#FFFFFF",
  dark: "#191F28",

  text: {
    strong: "#191F28",
    emph: "#333D4B",
    body: "#4E5968",
    sub: "#6B7684",
    dim: "#8B95A1",
    dimmer: "#B0B8C1",
    icon: "#C4CCD4",
  },

  up: "#F04452",
  upBg: "#FFEAEC",
  down: "#3182F6",

  success: "#12B886",
  successBg: "#E6F7F0",

  ai: "#7C3AED",
  ai2: "#845EF7",
  aiBg: "#F1ECFF",
  aiBg2: "#F8F4FF",

  warn: "#FF922B",
  warnBg: "#FFF4E6",

  star: "#FFB400",
  starOff: "#C4CCD4",
  toggleOff: "#D1D6DB",
  divider: "#F2F4F6",
} as const;

/** Color used for a +/- value, per Korean convention. up=red, down=blue. */
export function pnlColor(value: number): string {
  return value >= 0 ? colors.up : colors.down;
}

export const radius = {
  card: 20,
  cardSm: 18,
  input: 14,
  btn: 16,
  chip: 999,
  logo: 13,
  badge: 8,
} as const;

export const shadow = {
  // 0 2px 10px rgba(0,0,0,.04)
  card: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
} as const;
