import { Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors } from "@/theme/tokens";

interface PlaceholderProps {
  title: string;
  emoji: string;
  message: string;
}

/** Simple "coming soon" placeholder for not-yet-implemented tabs. */
export function Placeholder({ title, emoji, message }: PlaceholderProps) {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={["top"]}>
      <View style={{ paddingHorizontal: 20, paddingTop: 14 }}>
        <Text
          style={{
            fontSize: 22,
            fontWeight: "800",
            color: colors.text.strong,
            letterSpacing: -0.5,
          }}
        >
          {title}
        </Text>
      </View>
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          paddingHorizontal: 40,
        }}
      >
        <Text style={{ fontSize: 40 }}>{emoji}</Text>
        <Text
          style={{
            marginTop: 16,
            fontSize: 15,
            color: colors.text.dim,
            textAlign: "center",
            lineHeight: 22,
          }}
        >
          {message}
        </Text>
      </View>
    </SafeAreaView>
  );
}
