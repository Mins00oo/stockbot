import { router } from "expo-router";
import { Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { PrimaryButton } from "@/components";
import { colors } from "@/theme/tokens";

interface Feature {
  emoji: string;
  bg: string;
  title: string;
  sub: string;
}

const FEATURES: Feature[] = [
  {
    emoji: "📈",
    bg: colors.primaryBg,
    title: "실시간 보유 현황",
    sub: "계좌 연동만으로 종목·평가손익 자동 동기화",
  },
  {
    emoji: "🤖",
    bg: colors.aiBg,
    title: "AI 포트폴리오 분석",
    sub: "집중도·리스크를 진단하고 리밸런싱 제안",
  },
  {
    emoji: "🔔",
    bg: colors.successBg,
    title: "디스코드 알림",
    sub: "가격 급변·AI 인사이트를 원하는 채널로",
  },
];

export default function IntroScreen() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }}>
      <View
        style={{
          flex: 1,
          paddingHorizontal: 28,
          paddingTop: 32,
          paddingBottom: 32,
        }}
      >
        {/* logo */}
        <View
          style={{
            marginTop: 16,
            width: 64,
            height: 64,
            borderRadius: 20,
            backgroundColor: colors.primary,
            alignItems: "center",
            justifyContent: "center",
            shadowColor: colors.primary,
            shadowOffset: { width: 0, height: 10 },
            shadowOpacity: 0.3,
            shadowRadius: 24,
            elevation: 8,
          }}
        >
          <View
            style={{
              width: 26,
              height: 26,
              borderWidth: 4,
              borderColor: "#fff",
              borderTopColor: "transparent",
              borderRadius: 8,
              transform: [{ rotate: "45deg" }],
            }}
          />
        </View>

        <Text
          style={{
            marginTop: 28,
            fontSize: 28,
            fontWeight: "800",
            color: colors.text.strong,
            lineHeight: 37,
            letterSpacing: -0.7,
          }}
        >
          {"토스증권 계좌를\n연동하고\n내 주식 비서를 만들어요"}
        </Text>

        <Text
          style={{
            marginTop: 16,
            fontSize: 16,
            color: colors.text.sub,
            lineHeight: 25,
            letterSpacing: -0.3,
          }}
        >
          {"보유 종목을 한눈에 보고, AI가 포트폴리오를\n분석해 디스코드로 알려드려요."}
        </Text>

        {/* features */}
        <View style={{ marginTop: 36, gap: 14 }}>
          {FEATURES.map((f) => (
            <View
              key={f.title}
              style={{ flexDirection: "row", gap: 14, alignItems: "flex-start" }}
            >
              <View
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 12,
                  backgroundColor: f.bg,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Text style={{ fontSize: 18 }}>{f.emoji}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text
                  style={{
                    fontSize: 15,
                    fontWeight: "700",
                    color: colors.text.strong,
                  }}
                >
                  {f.title}
                </Text>
                <Text
                  style={{ fontSize: 13, color: colors.text.dim, marginTop: 2 }}
                >
                  {f.sub}
                </Text>
              </View>
            </View>
          ))}
        </View>

        <View style={{ flex: 1 }} />

        <PrimaryButton
          label="연결 시작하기"
          onPress={() => router.push("/onboarding/pairing")}
        />
        <Text
          style={{
            marginTop: 12,
            textAlign: "center",
            fontSize: 12,
            color: colors.text.dimmer,
          }}
        >
          앱 페어링 키와 토스증권 오픈 API 키가 필요해요
        </Text>
      </View>
    </SafeAreaView>
  );
}
