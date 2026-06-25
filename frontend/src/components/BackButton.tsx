import { router } from "expo-router";
import { Pressable, Text } from "react-native";

import { colors } from "@/theme/tokens";

interface BackButtonProps {
  onPress?: () => void;
}

/** Top-left ‹ back chevron. */
export function BackButton({ onPress }: BackButtonProps) {
  return (
    <Pressable
      hitSlop={10}
      onPress={onPress ?? (() => router.back())}
      style={{
        width: 32,
        height: 32,
        justifyContent: "center",
        marginLeft: -6,
      }}
    >
      <Text style={{ fontSize: 26, color: colors.text.strong }}>‹</Text>
    </Pressable>
  );
}
