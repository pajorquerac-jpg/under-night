import { ArrowLeft, Construction, Sparkles } from "lucide-react-native";
import { router, useLocalSearchParams } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { nightColors as colors } from "@/theme/night";

const labels: Record<string, string> = {
  "grupos-de-amigos": "Grupos de amigos",
  "recomendaciones-lugares": "Recomendaciones lugares",
  "ultima-salida": "Última salida",
};

export default function DummyScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const title = labels[slug ?? ""] ?? "Módulo";

  return (
    <Screen>
      <NightBackground />
      <View style={styles.content}>
        <View style={styles.headerIcon}>
          <Sparkles color={colors.primaryLight} size={28} strokeWidth={1.9} />
        </View>

        <View style={styles.card}>
          <View style={styles.iconBox}>
            <Construction color={colors.primary} size={34} strokeWidth={2.1} />
          </View>
          <Text style={styles.kicker}>Próximamente</Text>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.text}>
            Dummy para la demo del MVP. La navegación queda lista para conectar este flujo cuando
            exista su ruta real.
          </Text>
          <Pressable
            style={({ pressed }) => [styles.button, pressed && styles.pressed]}
            onPress={() => router.back()}
          >
            <ArrowLeft color={colors.black} size={18} strokeWidth={2.5} />
            <Text style={styles.buttonText}>Volver</Text>
          </Pressable>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    flex: 1,
    gap: 24,
    justifyContent: "flex-start",
    paddingHorizontal: 24,
  },
  headerIcon: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: "rgba(245, 158, 11, 0.08)",
    borderColor: "rgba(253, 186, 50, 0.22)",
    borderRadius: 18,
    borderWidth: 1,
    height: 48,
    justifyContent: "center",
    width: 48,
  },
  card: {
    backgroundColor: "rgba(17, 25, 43, 0.84)",
    borderColor: colors.borderHighlighted,
    borderRadius: 20,
    borderWidth: 1,
    gap: 14,
    padding: 22,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.1,
    shadowRadius: 28,
  },
  iconBox: {
    alignItems: "center",
    backgroundColor: "rgba(13, 19, 34, 0.94)",
    borderColor: "rgba(93, 110, 156, 0.78)",
    borderRadius: 18,
    borderWidth: 1,
    height: 70,
    justifyContent: "center",
    width: 70,
  },
  kicker: {
    color: colors.primaryLight,
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  title: {
    color: colors.textPrimary,
    fontSize: 34,
    fontWeight: "900",
    lineHeight: 39,
  },
  text: {
    color: colors.textSecondary,
    fontSize: 16,
    lineHeight: 23,
  },
  button: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: colors.primaryLight,
    borderColor: "rgba(255, 255, 255, 0.42)",
    borderRadius: 15,
    borderWidth: 1,
    flexDirection: "row",
    gap: 8,
    marginTop: 8,
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  buttonText: {
    color: colors.black,
    fontSize: 15,
    fontWeight: "900",
  },
  pressed: {
    opacity: 0.86,
    transform: [{ scale: 0.99 }],
  },
});
