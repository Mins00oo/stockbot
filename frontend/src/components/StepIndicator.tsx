import { Text, View } from "react-native";

import { colors } from "@/theme/tokens";

interface StepIndicatorProps {
  /** which step is current: 1 = pairing, 2 = toss key */
  current: 1 | 2;
}

/**
 * Onboarding step indicator.
 * Step 1 view: [1단계 (blue pill)]  2단계 · 토스증권 API (dim)
 * Step 2 view: ✓ 1단계 완료 (green)  [2단계 (blue pill)]
 */
export function StepIndicator({ current }: StepIndicatorProps) {
  const Pill = ({ label }: { label: string }) => (
    <View
      style={{
        backgroundColor: colors.primary,
        paddingVertical: 4,
        paddingHorizontal: 10,
        borderRadius: 8,
      }}
    >
      <Text style={{ fontSize: 12, fontWeight: "800", color: "#fff" }}>
        {label}
      </Text>
    </View>
  );

  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
      {current === 1 ? (
        <>
          <Pill label="1단계" />
          <Text
            style={{ fontSize: 12, fontWeight: "700", color: colors.text.dimmer }}
          >
            2단계 · 토스증권 API
          </Text>
        </>
      ) : (
        <>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 5 }}>
            <Text style={{ fontSize: 13, color: colors.success }}>✓</Text>
            <Text
              style={{ fontSize: 12, fontWeight: "700", color: colors.success }}
            >
              1단계 완료
            </Text>
          </View>
          <Pill label="2단계" />
        </>
      )}
    </View>
  );
}
