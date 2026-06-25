import { router } from "expo-router";
import { Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Card, PrimaryButton } from "@/components";
import { useHoldings } from "@/hooks/useHoldings";
import { krw, signedKrwWithPct } from "@/lib/format";
import { colors, pnlColor } from "@/theme/tokens";

export default function DoneScreen() {
  // Fetch the freshly-synced holdings summary to show on the success card.
  const { data } = useHoldings();

  const count = data?.holdings.length ?? 7;
  const totalValue = data ? krw(data.totalValueKrw) : "—";
  const totalPnl = data
    ? signedKrwWithPct(data.totalPnlKrw, data.totalPnlRate)
    : "—";
  const pnlValue = data?.totalPnlKrw ?? 0;

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
        <View
          style={{
            flex: 1,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {/* 88px circular check */}
          <View
            style={{
              width: 88,
              height: 88,
              borderRadius: 44,
              backgroundColor: colors.primary,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <View
              style={{
                width: 34,
                height: 18,
                borderLeftWidth: 5,
                borderBottomWidth: 5,
                borderColor: "#fff",
                transform: [{ rotate: "-45deg" }],
                marginTop: -6,
              }}
            />
          </View>

          <Text
            style={{
              marginTop: 26,
              fontSize: 24,
              fontWeight: "800",
              color: colors.text.strong,
              letterSpacing: -0.5,
            }}
          >
            연동이 완료됐어요
          </Text>
          <Text
            style={{
              marginTop: 10,
              fontSize: 15,
              color: colors.text.sub,
              textAlign: "center",
              lineHeight: 22.5,
            }}
          >
            {`토스증권 계좌의 보유 종목 ${count}개를\n불러왔어요.`}
          </Text>

          <Card
            style={{ marginTop: 24, width: "100%" }}
            rounded={16}
            padding={18}
          >
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
                paddingHorizontal: 2,
              }}
            >
              <View>
                <Text style={{ fontSize: 13, color: colors.text.dim }}>
                  총 평가금액
                </Text>
                <Text
                  style={{
                    fontSize: 22,
                    fontWeight: "800",
                    color: colors.text.strong,
                    marginTop: 2,
                  }}
                >
                  {totalValue}
                </Text>
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Text style={{ fontSize: 13, color: colors.text.dim }}>
                  평가손익
                </Text>
                <Text
                  style={{
                    marginTop: 2,
                    fontSize: 15,
                    fontWeight: "700",
                    color: pnlColor(pnlValue),
                  }}
                >
                  {totalPnl}
                </Text>
              </View>
            </View>
          </Card>
        </View>

        <PrimaryButton
          label="시작하기"
          onPress={() => router.replace("/(tabs)/home")}
        />
      </View>
    </SafeAreaView>
  );
}
