import { Text, View } from "react-native";

import { initial, logoBgFor } from "@/lib/format";

interface LogoChipProps {
  symbol: string;
  name: string;
  size?: number;
  radiusPx?: number;
  fontSize?: number;
}

/**
 * Brand-color square with white initial — stands in for a real stock logo.
 * (Backend doesn't send logos yet; color derived deterministically from symbol.)
 */
export function LogoChip({
  symbol,
  name,
  size = 42,
  radiusPx = 13,
  fontSize = 16,
}: LogoChipProps) {
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: radiusPx,
        backgroundColor: logoBgFor(symbol),
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Text style={{ color: "#fff", fontSize, fontWeight: "800" }}>
        {initial(name)}
      </Text>
    </View>
  );
}
