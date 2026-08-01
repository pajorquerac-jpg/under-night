import { StyleSheet, View } from "react-native";

import { nightColors as colors } from "@/theme/night";

export function NightBackground() {
  return (
    <View pointerEvents="none" style={styles.background}>
      <View style={styles.navyGlow} />
      <View style={styles.amberTrail} />
      <View style={styles.bottomGlow} />
    </View>
  );
}

const styles = StyleSheet.create({
  background: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.background,
    overflow: "hidden",
  },
  navyGlow: {
    backgroundColor: "rgba(17, 35, 72, 0.78)",
    borderRadius: 220,
    height: 360,
    position: "absolute",
    right: -170,
    top: -130,
    width: 360,
  },
  amberTrail: {
    backgroundColor: "rgba(245, 158, 11, 0.18)",
    borderRadius: 999,
    height: 3,
    left: -60,
    position: "absolute",
    right: -40,
    top: 128,
    transform: [{ rotate: "-18deg" }],
  },
  bottomGlow: {
    backgroundColor: "rgba(245, 158, 11, 0.12)",
    borderRadius: 190,
    bottom: -150,
    height: 260,
    left: 40,
    position: "absolute",
    right: 40,
  },
});
