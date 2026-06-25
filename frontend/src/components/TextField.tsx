import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

import { colors } from "@/theme/tokens";

type FieldStatus = "idle" | "verifying" | "ok" | "error";

interface TextFieldProps extends Omit<TextInputProps, "style"> {
  label: string;
  value: string;
  onChangeText: (t: string) => void;
  status?: FieldStatus;
  /** Secret mode: shows 보기/숨기기 toggle and masks by default. */
  secret?: boolean;
  letterSpacing?: number;
}

/**
 * Input field per handoff: height 54, radius 14, 1.5px border.
 * Border color: error=#F04452, filled/ok=#3182F6, empty=#E5E8EB.
 * Right adornment: spinner (verifying), ✓ (ok), or 보기/숨기기 (secret).
 */
export function TextField({
  label,
  value,
  onChangeText,
  status = "idle",
  secret = false,
  letterSpacing,
  ...rest
}: TextFieldProps) {
  const [hidden, setHidden] = useState(true);

  const borderColor =
    status === "error"
      ? colors.up
      : value.length > 0 || status === "ok"
        ? colors.primary
        : colors.edge;

  return (
    <View>
      <Text
        style={{
          fontSize: 13,
          fontWeight: "700",
          color: colors.text.body,
          marginBottom: 8,
        }}
      >
        {label}
      </Text>

      <View
        style={{
          height: 54,
          borderRadius: 14,
          backgroundColor: colors.card,
          borderWidth: 1.5,
          borderColor,
          flexDirection: "row",
          alignItems: "center",
          paddingHorizontal: 16,
        }}
      >
        <TextInput
          value={value}
          onChangeText={onChangeText}
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry={secret && hidden}
          placeholderTextColor={colors.text.dimmer}
          style={{
            flex: 1,
            fontSize: 15,
            color: colors.text.strong,
            letterSpacing,
          }}
          {...rest}
        />

        {status === "verifying" ? (
          <ActivityIndicator size="small" color={colors.primary} />
        ) : null}

        {status === "ok" ? (
          <Text style={{ fontSize: 16, color: colors.success }}>✓</Text>
        ) : null}

        {secret ? (
          <Pressable onPress={() => setHidden((h) => !h)} hitSlop={8}>
            <Text
              style={{
                fontSize: 13,
                fontWeight: "600",
                color: colors.text.dim,
                paddingLeft: 8,
              }}
            >
              {hidden ? "보기" : "숨기기"}
            </Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}
