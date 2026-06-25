import { Tabs } from "expo-router";
import { Text } from "react-native";

import { colors } from "@/theme/tokens";

/**
 * Bottom tab bar: 홈 / 탐색 / 관심 / 전체.
 * Only 홈 is functional today; the rest are placeholders.
 * Emoji icons stand in for the prototype's emoji glyphs.
 */
function TabIcon({ emoji }: { emoji: string }) {
  return <Text style={{ fontSize: 21 }}>{emoji}</Text>;
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.text.strong,
        tabBarInactiveTintColor: colors.text.dim,
        tabBarStyle: {
          backgroundColor: colors.card,
          borderTopColor: colors.divider,
          borderTopWidth: 1,
          height: 64,
          paddingTop: 8,
          paddingBottom: 8,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "700" },
        sceneStyle: { backgroundColor: colors.bg },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: "홈",
          tabBarIcon: () => <TabIcon emoji="🏠" />,
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: "탐색",
          tabBarIcon: () => <TabIcon emoji="🔍" />,
        }}
      />
      <Tabs.Screen
        name="watchlist"
        options={{
          title: "관심",
          tabBarIcon: () => <TabIcon emoji="⭐" />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "전체",
          tabBarIcon: () => <TabIcon emoji="☰" />,
        }}
      />
    </Tabs>
  );
}
