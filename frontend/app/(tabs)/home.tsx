import { router } from "expo-router";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { Card, HoldingRow, PrimaryButton } from "@/components";
import { useHoldings } from "@/hooks/useHoldings";
import { krw, signedKrwWithPct } from "@/lib/format";
import { colors, pnlColor, shadow } from "@/theme/tokens";

interface QuickAction {
  emoji: string;
  bg: string;
  label: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  { emoji: "📄", bg: colors.aiBg, label: "AI 리포트" },
  { emoji: "📅", bg: colors.successBg, label: "실적·배당" },
  { emoji: "🧭", bg: colors.warnBg, label: "탐색" },
];

/** Magnifier icon (drawn, matching the prototype's inline SVG look). */
function SearchIcon() {
  return (
    <View style={{ width: 26, height: 26 }}>
      <View
        style={{
          width: 17,
          height: 17,
          borderWidth: 2.4,
          borderColor: colors.text.body,
          borderRadius: 9,
        }}
      />
      <View
        style={{
          position: "absolute",
          width: 8,
          height: 2.4,
          backgroundColor: colors.text.body,
          borderRadius: 2,
          bottom: 2,
          right: 0,
          transform: [{ rotate: "45deg" }],
        }}
      />
    </View>
  );
}

export default function HomeScreen() {
  const { data, isLoading, isError, error, refetch, isRefetching } =
    useHoldings();

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={["top"]}>
      <ScrollView
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 28 }}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
        }
      >
        {/* header */}
        <View
          style={{
            paddingHorizontal: 20,
            paddingTop: 6,
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Text
            style={{
              fontSize: 22,
              fontWeight: "800",
              color: colors.text.strong,
              letterSpacing: -0.5,
            }}
          >
            내 투자
          </Text>
          <Pressable onPress={() => router.push("/(tabs)/explore")} hitSlop={8}>
            <SearchIcon />
          </Pressable>
        </View>

        {isLoading ? (
          <View style={{ paddingVertical: 80, alignItems: "center" }}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data ? (
          <>
            {/* asset hero card */}
            <Card
              style={{ marginHorizontal: 20, marginTop: 16 }}
              padding={0}
            >
              <View style={{ padding: 24, paddingHorizontal: 22 }}>
                <Text
                  style={{
                    fontSize: 14,
                    color: colors.text.dim,
                    fontWeight: "600",
                  }}
                >
                  총 평가금액
                </Text>
                <Text
                  style={{
                    fontSize: 32,
                    fontWeight: "800",
                    color: colors.text.strong,
                    marginTop: 6,
                    letterSpacing: -1,
                  }}
                >
                  {krw(data.totalValueKrw)}
                </Text>
                <View
                  style={{
                    marginTop: 8,
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <Text
                    style={{
                      fontSize: 15,
                      fontWeight: "700",
                      color: pnlColor(data.totalPnlKrw),
                    }}
                  >
                    {signedKrwWithPct(data.totalPnlKrw, data.totalPnlRate)}
                  </Text>
                  <Text style={{ fontSize: 13, color: colors.text.dimmer }}>
                    투자원금 {krw(data.totalPurchaseKrw)}
                  </Text>
                </View>

                <Pressable
                  onPress={() => {}}
                  style={{
                    marginTop: 18,
                    height: 48,
                    borderRadius: 14,
                    backgroundColor: colors.primaryBg,
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                  }}
                >
                  <Text style={{ fontSize: 16 }}>🤖</Text>
                  <Text
                    style={{
                      fontSize: 15,
                      fontWeight: "700",
                      color: colors.primary,
                    }}
                  >
                    AI 포트폴리오 분석 받기
                  </Text>
                </Pressable>
              </View>
            </Card>

            {/* quick actions */}
            <View
              style={{
                marginHorizontal: 20,
                marginTop: 12,
                flexDirection: "row",
                gap: 10,
              }}
            >
              {QUICK_ACTIONS.map((q) => (
                <Pressable
                  key={q.label}
                  onPress={() => {
                    if (q.label === "탐색") router.push("/(tabs)/explore");
                  }}
                  style={{
                    flex: 1,
                    backgroundColor: colors.card,
                    borderRadius: 16,
                    paddingVertical: 16,
                    paddingHorizontal: 12,
                    alignItems: "center",
                    gap: 8,
                    ...shadow.card,
                  }}
                >
                  <View
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 13,
                      backgroundColor: q.bg,
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ fontSize: 19 }}>{q.emoji}</Text>
                  </View>
                  <Text
                    style={{
                      fontSize: 13,
                      fontWeight: "700",
                      color: colors.text.strong,
                    }}
                  >
                    {q.label}
                  </Text>
                </Pressable>
              ))}
            </View>

            {/* holdings section header */}
            <View
              style={{
                paddingHorizontal: 20,
                paddingTop: 26,
                paddingBottom: 10,
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Text
                style={{
                  fontSize: 17,
                  fontWeight: "800",
                  color: colors.text.strong,
                }}
              >
                보유 종목 {data.holdings.length}
              </Text>
              <Text
                style={{ fontSize: 13, color: colors.text.dim, fontWeight: "600" }}
              >
                평가금액순
              </Text>
            </View>

            {/* holdings list */}
            <Card
              style={{ marginHorizontal: 12 }}
              rounded={18}
              padding={6}
            >
              {data.holdings.map((h) => (
                <HoldingRow key={h.symbol} holding={h} onPress={() => {}} />
              ))}
              {data.holdings.length === 0 ? (
                <View style={{ padding: 40, alignItems: "center" }}>
                  <Text
                    style={{
                      fontSize: 14,
                      color: colors.text.dim,
                    }}
                  >
                    보유 중인 종목이 없어요
                  </Text>
                </View>
              ) : null}
            </Card>
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function ErrorState({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry: () => void;
}) {
  const notConnected =
    error instanceof ApiError && error.code === "NOT_CONNECTED";
  const message =
    error instanceof ApiError
      ? error.message
      : "보유 종목을 불러오지 못했어요";

  return (
    <View style={{ paddingHorizontal: 20, paddingVertical: 64, alignItems: "center" }}>
      <Text style={{ fontSize: 32 }}>{notConnected ? "🔌" : "⚠️"}</Text>
      <Text
        style={{
          marginTop: 14,
          fontSize: 15,
          fontWeight: "700",
          color: colors.text.body,
          textAlign: "center",
        }}
      >
        {message}
      </Text>
      <View style={{ marginTop: 20, width: 200 }}>
        {notConnected ? (
          <PrimaryButton
            label="계좌 연결하기"
            onPress={() => router.replace("/onboarding/toss-key")}
          />
        ) : (
          <PrimaryButton label="다시 시도" onPress={onRetry} />
        )}
      </View>
    </View>
  );
}
