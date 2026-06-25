import {
  ActivityIndicator,
  Pressable,
  Text,
  type ViewStyle,
} from "react-native";

import { colors } from "@/theme/tokens";

interface PrimaryButtonProps {
  label: string;
  onPress?: () => void;
  disabled?: boolean;
  loading?: boolean;
  /** override background (e.g. success green on "확인 완료") */
  backgroundColor?: string;
  textColor?: string;
  style?: ViewStyle;
}

/**
 * CTA button — height 56, radius 16, primary blue.
 * Disabled = #E5E8EB bg / #B0B8C1 text (per handoff onb step buttons).
 */
export function PrimaryButton({
  label,
  onPress,
  disabled = false,
  loading = false,
  backgroundColor,
  textColor,
  style,
}: PrimaryButtonProps) {
  const isInactive = disabled || loading;
  // Disabled => grey track + dim text. Otherwise use override or primary blue.
  const bg = disabled ? colors.edge : (backgroundColor ?? colors.primary);
  const fg = disabled ? colors.text.dimmer : (textColor ?? "#FFFFFF");

  return (
    <Pressable
      accessibilityRole="button"
      disabled={isInactive}
      onPress={onPress}
      style={({ pressed }) => [
        {
          height: 56,
          borderRadius: 16,
          backgroundColor: bg,
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "row",
          gap: 8,
          opacity: pressed && !isInactive ? 0.92 : 1,
        },
        style,
      ]}
    >
      {loading ? <ActivityIndicator color={fg} size="small" /> : null}
      <Text style={{ color: fg, fontSize: 17, fontWeight: "700" }}>
        {label}
      </Text>
    </Pressable>
  );
}
