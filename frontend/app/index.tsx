import { Redirect } from "expo-router";
import { ActivityIndicator, Text, View } from "react-native";

import { PrimaryButton } from "@/components";
import { useAuthStatus } from "@/hooks/useAuthStatus";
import { useAuthStore } from "@/stores/authStore";
import { colors } from "@/theme/tokens";

/**
 * Auth-gate entry. After hydration (SecureStore read in _layout):
 *  - not paired                -> onboarding intro
 *  - paired + Toss connected    -> tabs (home)
 *  - paired + NOT connected     -> onboarding step 2 (toss-key) to finish setup
 *
 * "connected" is the backend's truth (it holds the encrypted Toss keys), so we
 * ask GET /auth/status on launch rather than trusting a local flag that resets
 * on relaunch. Home is only reachable once the account is fully connected.
 */
export default function Index() {
  const paired = useAuthStore((s) => s.paired);
  const status = useAuthStatus(paired);

  if (!paired) {
    return <Redirect href="/onboarding/intro" />;
  }

  if (status.isSuccess) {
    return status.data.connected ? (
      <Redirect href="/(tabs)/home" />
    ) : (
      <Redirect href="/onboarding/toss-key" />
    );
  }

  // Paired but the status check is still loading or failed (e.g. backend off /
  // wrong Wi-Fi). Don't misroute — show a spinner, or a retry on error.
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: colors.bg,
        alignItems: "center",
        justifyContent: "center",
        paddingHorizontal: 40,
      }}
    >
      {status.isError ? (
        <>
          <Text style={{ fontSize: 32 }}>📡</Text>
          <Text
            style={{
              marginTop: 14,
              fontSize: 15,
              fontWeight: "700",
              color: colors.text.body,
              textAlign: "center",
            }}
          >
            백엔드에 연결하지 못했어요
          </Text>
          <Text
            style={{
              marginTop: 6,
              fontSize: 13,
              color: colors.text.dim,
              textAlign: "center",
              lineHeight: 19,
            }}
          >
            서버가 켜져 있고 폰과 같은 와이파이인지 확인해 주세요
          </Text>
          <View style={{ marginTop: 20, width: 200 }}>
            <PrimaryButton
              label="다시 시도"
              onPress={() => status.refetch()}
              loading={status.isFetching}
            />
          </View>
        </>
      ) : (
        <ActivityIndicator color={colors.primary} />
      )}
    </View>
  );
}
