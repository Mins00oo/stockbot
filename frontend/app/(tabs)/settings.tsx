import { router } from "expo-router";
import { Alert, Pressable, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Card } from "@/components";
import { useAuthStore } from "@/stores/authStore";
import { colors } from "@/theme/tokens";

/**
 * 전체(설정) — placeholder for today. Only "계좌 다시 연동" is wired up,
 * since it clears the locally-stored pairing key (auth-store reset) and
 * sends the user back to onboarding.
 */
export default function SettingsScreen() {
  const reset = useAuthStore((s) => s.reset);

  const onRelink = () => {
    Alert.alert(
      "계좌 다시 연동",
      "저장된 페어링 키를 지우고 처음부터 다시 연동할까요?",
      [
        { text: "취소", style: "cancel" },
        {
          text: "다시 연동",
          style: "destructive",
          onPress: async () => {
            await reset();
            router.replace("/onboarding/intro");
          },
        },
      ],
    );
  };

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
          전체
        </Text>
      </View>

      {/* account card */}
      <Card
        style={{ marginHorizontal: 20, marginTop: 18 }}
        rounded={18}
        padding={18}
      >
        <View style={{ flexDirection: "row", alignItems: "center", gap: 14 }}>
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              backgroundColor: colors.primaryBg,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Text style={{ fontSize: 20 }}>🙂</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text
              style={{
                fontSize: 16,
                fontWeight: "800",
                color: colors.text.strong,
              }}
            >
              내 계좌
            </Text>
            <Text style={{ fontSize: 13, color: colors.text.dim, marginTop: 1 }}>
              토스증권 · 연동됨
            </Text>
          </View>
          <View
            style={{
              backgroundColor: colors.successBg,
              paddingVertical: 5,
              paddingHorizontal: 10,
              borderRadius: 8,
            }}
          >
            <Text
              style={{ fontSize: 12, fontWeight: "700", color: colors.success }}
            >
              연동중
            </Text>
          </View>
        </View>
      </Card>

      {/* 연동 · 기타 */}
      <Text
        style={{
          paddingHorizontal: 24,
          paddingTop: 24,
          paddingBottom: 10,
          fontSize: 13,
          fontWeight: "700",
          color: colors.text.dim,
        }}
      >
        연동 · 기타
      </Text>
      <Card
        style={{ marginHorizontal: 20 }}
        rounded={18}
        padding={0}
      >
        <View style={{ paddingHorizontal: 20 }}>
          <Pressable
            onPress={onRelink}
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
              paddingVertical: 16,
            }}
          >
            <Text style={{ fontSize: 14.5, color: colors.text.strong }}>
              계좌 다시 연동
            </Text>
            <Text style={{ color: colors.text.icon, fontSize: 16 }}>›</Text>
          </Pressable>
          <View style={{ height: 1, backgroundColor: colors.divider }} />
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
              paddingVertical: 16,
            }}
          >
            <Text style={{ fontSize: 14.5, color: colors.text.strong }}>
              버전 정보
            </Text>
            <Text style={{ fontSize: 13, color: colors.text.dim }}>1.0.0</Text>
          </View>
        </View>
      </Card>

      <View style={{ flex: 1, alignItems: "center", justifyContent: "flex-end", paddingBottom: 24 }}>
        <Text style={{ fontSize: 12, color: colors.text.dimmer }}>
          알림 · 방해 금지 등 나머지 설정은 곧 추가될 예정이에요.
        </Text>
      </View>
    </SafeAreaView>
  );
}
