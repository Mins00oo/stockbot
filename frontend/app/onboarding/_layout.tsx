import { Stack } from "expo-router";

import { colors } from "@/theme/tokens";

/** Onboarding flow: no tab bar, stack navigation, gesture-back disabled
 *  on the locked steps (connecting/done) so users can't skip back. */
export default function OnboardingLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bg },
        animation: "slide_from_right",
      }}
    >
      <Stack.Screen name="intro" />
      <Stack.Screen name="pairing" />
      <Stack.Screen name="toss-key" />
      <Stack.Screen
        name="connecting"
        options={{ gestureEnabled: false, animation: "fade" }}
      />
      <Stack.Screen
        name="done"
        options={{ gestureEnabled: false, animation: "fade" }}
      />
    </Stack>
  );
}
