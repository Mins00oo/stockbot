import { Text, View } from "react-native";

import { colors } from "@/theme/tokens";

interface InfoBoxProps {
  emoji: string;
  text: string;
  /** background color, default ai-bg (#F1ECFF) */
  backgroundColor?: string;
}

/** Rounded hint box: emoji + body copy (e.g. 🤖 / 🔒 onboarding notices). */
export function InfoBox({
  emoji,
  text,
  backgroundColor = colors.aiBg,
}: InfoBoxProps) {
  return (
    <View
      style={{
        backgroundColor,
        borderRadius: 14,
        padding: 14,
        paddingHorizontal: 16,
        flexDirection: "row",
        gap: 10,
        alignItems: "flex-start",
      }}
    >
      <Text style={{ fontSize: 15, lineHeight: 20 }}>{emoji}</Text>
      <Text
        style={{
          flex: 1,
          fontSize: 12.5,
          color: colors.text.sub,
          lineHeight: 19.5,
          letterSpacing: -0.2,
        }}
      >
        {text}
      </Text>
    </View>
  );
}
