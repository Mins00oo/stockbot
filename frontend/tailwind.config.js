/**
 * Tailwind config — handoff design tokens mapped to utility names.
 * Source: docs/design/screens/design_handoff_toss_stock_assistant/README.md (Design Tokens).
 * Korean convention: 상승/이익 = up (#F04452 red), 하락/손실 = down (#3182F6 blue).
 */
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // brand
        primary: "#3182F6",
        "primary-bg": "#EAF2FE",
        // surfaces
        bg: "#F2F4F6",
        edge: "#E5E8EB",
        card: "#FFFFFF",
        dark: "#191F28",
        // text scale
        text: {
          strong: "#191F28",
          emph: "#333D4B",
          body: "#4E5968",
          sub: "#6B7684",
          dim: "#8B95A1",
          dimmer: "#B0B8C1",
          icon: "#C4CCD4",
        },
        // Korean market semantic colors
        up: "#F04452", // 상승/이익 (red)
        "up-bg": "#FFEAEC",
        down: "#3182F6", // 하락/손실 (blue)
        // status
        success: "#12B886",
        "success-bg": "#E6F7F0",
        // ai / purple
        ai: "#7C3AED",
        "ai-2": "#845EF7",
        "ai-bg": "#F1ECFF",
        "ai-bg-2": "#F8F4FF",
        // warning / orange
        warn: "#FF922B",
        "warn-bg": "#FFF4E6",
        // misc
        star: "#FFB400",
        "star-off": "#C4CCD4",
        "toggle-off": "#D1D6DB",
        divider: "#F2F4F6",
        // sector palette
        "sector-semicon": "#3182F6",
        "sector-bigtech": "#845EF7",
        "sector-auto": "#12B886",
        "sector-internet": "#FF922B",
        "sector-battery": "#F783AC",
        "sector-bio": "#22B8CF",
        "sector-finance": "#FAB005",
      },
      borderRadius: {
        chip: "999px",
        badge: "8px",
        logo: "13px",
        card: "20px",
        "card-sm": "18px",
        input: "14px",
        btn: "16px",
      },
      fontFamily: {
        // Pretendard — bundle the font or load via expo-font.
        // See README "Pretendard font setup".
        sans: ["Pretendard", "System"],
      },
    },
  },
  plugins: [],
};
