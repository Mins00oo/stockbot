import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { useConnectToss } from "@/hooks/useConnectToss";
import { colors } from "@/theme/tokens";

type StepState = "done" | "active" | "pending";

interface ProgressStep {
  label: string;
  state: StepState;
}

function Marker({ state }: { state: StepState }) {
  const bg =
    state === "done"
      ? colors.success
      : state === "active"
        ? colors.primary
        : colors.edge;
  return (
    <View
      style={{
        width: 20,
        height: 20,
        borderRadius: 10,
        backgroundColor: bg,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Text style={{ fontSize: 11, color: "#fff" }}>
        {state === "done" ? "✓" : ""}
      </Text>
    </View>
  );
}

export default function ConnectingScreen() {
  const { appKey, secretKey } = useLocalSearchParams<{
    appKey: string;
    secretKey: string;
  }>();

  const connect = useConnectToss();
  const startedRef = useRef(false);

  // Visual progress: API auth -> balance -> holdings sync.
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    // animate the visible progress markers
    const t1 = setTimeout(() => setStepIdx(1), 700);
    const t2 = setTimeout(() => setStepIdx(2), 1500);

    connect.mutate(
      { appKey: String(appKey ?? ""), secretKey: String(secretKey ?? "") },
      {
        onSuccess: () => {
          // ensure the progress UI shows briefly even on a fast response
          setStepIdx(2);
          setTimeout(() => router.replace("/onboarding/done"), 600);
        },
        onError: (err) => {
          const msg =
            err instanceof ApiError
              ? err.message
              : "토스 키가 올바르지 않아요";
          Alert.alert("연결 실패", msg, [
            { text: "다시 입력", onPress: () => router.back() },
          ]);
        },
      },
    );

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const steps: ProgressStep[] = [
    { label: "API 키 인증", state: stepIdx > 0 ? "done" : "active" },
    {
      label: "계좌 잔고 조회",
      state: stepIdx > 1 ? "done" : stepIdx === 1 ? "active" : "pending",
    },
    { label: "보유 종목 동기화", state: stepIdx >= 2 ? "active" : "pending" },
  ];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }}>
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          paddingHorizontal: 28,
        }}
      >
        {/* 72px spinner */}
        <View
          style={{
            width: 72,
            height: 72,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <ActivityIndicator size="large" color={colors.primary} />
        </View>

        <Text
          style={{
            marginTop: 28,
            fontSize: 20,
            fontWeight: "800",
            color: colors.text.strong,
            letterSpacing: -0.4,
          }}
        >
          토스증권에 연결 중이에요
        </Text>
        <Text style={{ marginTop: 10, fontSize: 14, color: colors.text.dim }}>
          API 키를 인증하고 잔고를 불러오고 있어요
        </Text>

        <View style={{ marginTop: 32, width: 200, gap: 12 }}>
          {steps.map((s) => (
            <View
              key={s.label}
              style={{ flexDirection: "row", alignItems: "center", gap: 10 }}
            >
              <Marker state={s.state} />
              <Text
                style={{
                  fontSize: 13.5,
                  color:
                    s.state === "active"
                      ? colors.primary
                      : s.state === "done"
                        ? colors.text.body
                        : colors.text.dim,
                  fontWeight: s.state === "active" ? "700" : "400",
                }}
              >
                {s.label}
              </Text>
            </View>
          ))}
        </View>
      </View>
    </SafeAreaView>
  );
}
