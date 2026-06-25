import { Pressable, Text, View } from "react-native";

import { LogoChip } from "./LogoChip";

import { fmtInt, marketLabel, money, signedPct } from "@/lib/format";
import { colors, pnlColor } from "@/theme/tokens";
import type { Holding } from "@/types/api";

interface HoldingRowProps {
  holding: Holding;
  onPress?: () => void;
}

/**
 * One holding row (home list).
 * Left: logo + name + "시장 · N주". Right: eval amount + pnlRate (red/blue).
 * Color follows pnl sign (Korean convention): up=red, down=blue.
 */
export function HoldingRow({ holding, onPress }: HoldingRowProps) {
  const sub = `${marketLabel(holding.market)} · ${fmtInt(holding.quantity)}주`;
  const valueStr = money(holding.currency, holding.evalAmount);
  const changeColor = pnlColor(holding.pnl);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => ({
        flexDirection: "row",
        alignItems: "center",
        gap: 14,
        paddingVertical: 14,
        paddingHorizontal: 12,
        borderRadius: 14,
        backgroundColor: pressed ? "#F7F8FA" : "transparent",
      })}
    >
      <LogoChip symbol={holding.symbol} name={holding.name} />

      <View style={{ flex: 1, minWidth: 0 }}>
        <Text
          numberOfLines={1}
          style={{
            fontSize: 15,
            fontWeight: "700",
            color: colors.text.strong,
            letterSpacing: -0.3,
          }}
        >
          {holding.name}
        </Text>
        <Text style={{ fontSize: 12.5, color: colors.text.dim, marginTop: 2 }}>
          {sub}
        </Text>
      </View>

      <View style={{ alignItems: "flex-end" }}>
        <Text
          style={{ fontSize: 15, fontWeight: "700", color: colors.text.strong }}
        >
          {valueStr}
        </Text>
        <Text
          style={{
            marginTop: 2,
            fontSize: 14,
            fontWeight: "700",
            color: changeColor,
          }}
        >
          {signedPct(holding.pnlRate)}
        </Text>
      </View>
    </Pressable>
  );
}
