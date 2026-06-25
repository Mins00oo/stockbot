import { router } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { BackButton, InfoBox, PrimaryButton, StepIndicator, TextField } from "@/components";
import { usePairingVerify } from "@/hooks/usePairingVerify";
import { colors } from "@/theme/tokens";

const DEMO_PAIRING_KEY = "TOSS-AI-7K2F-9XQD";

interface FormValues {
  pairKey: string;
}

export default function PairingScreen() {
  const { control, handleSubmit, setValue, watch } = useForm<FormValues>({
    defaultValues: { pairKey: "" },
    mode: "onChange",
  });
  const pairKey = watch("pairKey");

  const verify = usePairingVerify();
  const [verified, setVerified] = useState(false);
  const advanceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Go to step 2. Cancels any pending auto-advance so a manual tap and the
  // post-verify timer can't both fire (no double push).
  const goToTossKey = () => {
    if (advanceTimer.current) clearTimeout(advanceTimer.current);
    router.push("/onboarding/toss-key");
  };

  // Clear the auto-advance timer if we leave before it fires.
  useEffect(() => {
    return () => {
      if (advanceTimer.current) clearTimeout(advanceTimer.current);
    };
  }, []);

  const tooShort = pairKey.trim().length < 4;
  const errorMsg =
    verify.isError && !verify.isPending
      ? verify.error instanceof ApiError
        ? verify.error.message
        : "페어링 키가 올바르지 않아요."
      : null;

  const status: "idle" | "verifying" | "ok" | "error" = verify.isPending
    ? "verifying"
    : verified
      ? "ok"
      : errorMsg
        ? "error"
        : "idle";

  const onSubmit = handleSubmit(({ pairKey }) => {
    if (pairKey.trim().length < 4) return;
    verify.mutate(pairKey.trim(), {
      onSuccess: () => {
        setVerified(true);
        // brief success state, then auto-advance to step 2 (first time through).
        advanceTimer.current = setTimeout(goToTossKey, 650);
      },
    });
  });

  const btnLabel = verify.isPending
    ? "확인 중…"
    : verified
      ? "다음"
      : "페어링 확인";
  const btnBg = verified ? colors.success : undefined;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={{
            flexGrow: 1,
            paddingHorizontal: 28,
            paddingTop: 8,
            paddingBottom: 32,
          }}
          keyboardShouldPersistTaps="handled"
        >
          <BackButton onPress={() => router.back()} />

          <View style={{ marginTop: 14 }}>
            <StepIndicator current={1} />
          </View>

          <Text
            style={{
              marginTop: 16,
              fontSize: 26,
              fontWeight: "800",
              color: colors.text.strong,
              lineHeight: 35,
              letterSpacing: -0.6,
            }}
          >
            {"앱 페어링 키를\n입력해 주세요"}
          </Text>

          <Text
            style={{
              marginTop: 14,
              fontSize: 14.5,
              color: colors.text.sub,
              lineHeight: 22.5,
              letterSpacing: -0.3,
            }}
          >
            내 주식 비서(AI)와 앱을 연결하는 키예요.
          </Text>

          <View style={{ marginTop: 30 }}>
            <Controller
              control={control}
              name="pairKey"
              render={({ field: { value, onChange } }) => (
                <TextField
                  label="페어링 키"
                  value={value}
                  onChangeText={(t) => {
                    onChange(t);
                    if (verified) setVerified(false);
                    if (advanceTimer.current) clearTimeout(advanceTimer.current);
                    verify.reset();
                  }}
                  placeholder="예: TOSS-AI-XXXX-XXXX"
                  status={status}
                  letterSpacing={0.5}
                  editable={!verify.isPending}
                />
              )}
            />
            {errorMsg ? (
              <Text
                style={{
                  marginTop: 8,
                  fontSize: 12.5,
                  color: colors.up,
                  fontWeight: "600",
                }}
              >
                {errorMsg}
              </Text>
            ) : null}
          </View>

          <View style={{ marginTop: 18 }}>
            <InfoBox
              emoji="🤖"
              text="페어링이 완료되면 AI 분석 결과와 알림이 연결된 디스코드 채널로 전달돼요."
            />
          </View>

          <View style={{ flex: 1, minHeight: 20 }} />

          <View style={{ marginTop: 24 }}>
            <PrimaryButton
              label={btnLabel}
              onPress={verified ? goToTossKey : onSubmit}
              disabled={verified ? false : tooShort}
              loading={verify.isPending}
              backgroundColor={btnBg}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
