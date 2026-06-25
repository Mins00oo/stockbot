import type { PropsWithChildren } from "react";
import { View, type ViewStyle } from "react-native";

import { colors, radius, shadow } from "@/theme/tokens";

interface CardProps {
  style?: ViewStyle;
  /** card radius, default 20 */
  rounded?: number;
  padding?: number;
}

/** White rounded card with the standard soft shadow. */
export function Card({
  children,
  style,
  rounded = radius.card,
  padding,
}: PropsWithChildren<CardProps>) {
  return (
    <View
      style={[
        {
          backgroundColor: colors.card,
          borderRadius: rounded,
          ...shadow.card,
        },
        padding != null ? { padding } : null,
        style,
      ]}
    >
      {children}
    </View>
  );
}
