import { zodResolver } from "@hookform/resolvers/zod";
import { router } from "expo-router";
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

import {
  BackButton,
  InfoBox,
  PrimaryButton,
  StepIndicator,
  TextField,
} from "@/components";
import { colors } from "@/theme/tokens";
import { TossConnectRequestSchema, type TossConnectRequest } from "@/types/api";

const DEMO_APP_KEY = "tskey_live_8f3a91c20d";
const DEMO_SECRET_KEY = "sk_2b7e4f9a1c6d8e0fa3b5";

export default function TossKeyScreen() {
  const { control, handleSubmit, setValue, watch } = useForm<TossConnectRequest>(
    {
      resolver: zodResolver(TossConnectRequestSchema),
      defaultValues: { appKey: "", secretKey: "" },
      mode: "onChange",
    },
  );

  const appKey = watch("appKey");
  const secretKey = watch("secretKey");
  const canSubmit = appKey.trim().length >= 4 && secretKey.trim().length >= 4;

  // The actual connect call happens on the "connecting" screen so the
  // loading/progress UI can own the request lifecycle. We pass keys as params.
  const onSubmit = handleSubmit((values) => {
    router.push({
      pathname: "/onboarding/connecting",
      params: { appKey: values.appKey.trim(), secretKey: values.secretKey.trim() },
    });
  });

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
            <StepIndicator current={2} />
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
            {"토스증권 오픈 API\n키를 입력해 주세요"}
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
            {"토스증권 개발자센터에서 발급받은 App Key와\nSecret Key를 입력하면 계좌가 연결돼요."}
          </Text>

          <View style={{ marginTop: 30 }}>
            <Controller
              control={control}
              name="appKey"
              render={({ field: { value, onChange } }) => (
                <TextField
                  label="App Key"
                  value={value}
                  onChangeText={onChange}
                  placeholder="발급받은 App Key 입력"
                  status={value.trim().length >= 4 ? "ok" : "idle"}
                  letterSpacing={-0.2}
                />
              )}
            />
          </View>

          <View style={{ marginTop: 18 }}>
            <Controller
              control={control}
              name="secretKey"
              render={({ field: { value, onChange } }) => (
                <TextField
                  label="Secret Key"
                  value={value}
                  onChangeText={onChange}
                  placeholder="발급받은 Secret Key 입력"
                  secret
                />
              )}
            />
          </View>

          <View style={{ marginTop: 18 }}>
            {/* tech-stack security copy fix:
                "기기에만 저장" -> "암호화되어 안전하게 저장",
                "주문 권한 요청 안 함" -> "주문 기능 미사용" */}
            <InfoBox
              emoji="🔒"
              backgroundColor="#F1F4F8"
              text="키는 암호화되어 안전하게 저장되며, 시세·잔고 조회에만 사용돼요. 주문 기능은 사용하지 않아요."
            />
          </View>

          <View style={{ flex: 1, minHeight: 20 }} />

          <View style={{ marginTop: 24 }}>
            <PrimaryButton
              label="연결하기"
              onPress={onSubmit}
              disabled={!canSubmit}
            />
          </View>

          <Pressable
            onPress={() => {
              setValue("appKey", DEMO_APP_KEY);
              setValue("secretKey", DEMO_SECRET_KEY);
            }}
            style={{ marginTop: 12 }}
          >
            <Text
              style={{
                textAlign: "center",
                fontSize: 12.5,
                color: colors.primary,
                fontWeight: "600",
              }}
            >
              데모 키로 채우기
            </Text>
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
