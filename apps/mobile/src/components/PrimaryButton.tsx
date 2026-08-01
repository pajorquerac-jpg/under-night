import { Pressable, StyleSheet, Text } from "react-native";

import { nightColors as colors } from "@/theme/night";

type PrimaryButtonProps = {
  label: string;
  onPress: () => void;
};

export function PrimaryButton({ label, onPress }: PrimaryButtonProps) {
  return (
    <Pressable
      style={({ pressed }) => [styles.button, pressed && styles.pressed]}
      onPress={onPress}
    >
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    backgroundColor: colors.primaryLight,
    borderColor: "rgba(255, 255, 255, 0.42)",
    borderRadius: 17,
    borderWidth: 1,
    paddingHorizontal: 18,
    paddingVertical: 15,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.34,
    shadowRadius: 24,
  },
  label: {
    color: colors.black,
    fontSize: 16,
    fontWeight: "900",
  },
  pressed: {
    opacity: 0.82,
    transform: [{ scale: 0.99 }],
  },
});
