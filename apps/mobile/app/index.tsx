import { ChevronRight, Clock3, MapPinned, ShieldCheck, Sparkles } from "lucide-react-native";
import { router } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { nightColors as colors } from "@/theme/night";

const cards = [
  // {
  //   Icon: Clock3,
  //   description: "Recupera los detalles de tu última noche.",
  //   onPress: () => {
  //     // TODO: conectar a la ruta real de última salida cuando exista.
  //     router.push("/dummy/ultima-salida" as never);
  //   },
  //   title: "Última salida",
  // },
  // {
  //   Icon: UsersRound,
  //   description: "Organiza las preferencias de todos en un solo lugar.",
  //   onPress: () => {
  //     // TODO: conectar al flujo real de grupos/participantes cuando exista.
  //     router.push("/dummy/grupos-de-amigos" as never);
  //   },
  //   title: "Grupo de amigos",
  // },
  {
    Icon: MapPinned,
    description: "Explora opciones generales de demostración.",
    onPress: () => router.push("/recommendations"),
    title: "Recomendaciones de lugares",
  },
] as const;

export default function HomeScreen() {
  return (
    <Screen>
      <NightBackground />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.mainLayout}>
          <View style={styles.topBlock}>
            <View style={styles.header}>
              <View style={styles.sparkleWrap}>
                <Sparkles color={colors.primaryLight} size={32} strokeWidth={1.8} />
              </View>
              <Text style={styles.title}>UnderNight</Text>
              <Text style={styles.subtitle}>Tu noche, ordenada por compatibilidad.</Text>
            </View>

            <Pressable
              accessibilityLabel="Iniciar salida en UnderNight"
              accessibilityRole="button"
              style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}
              onPress={() => router.push("/agent/chat" as never)}
            >
              <Text style={styles.primaryLabel}>Iniciar salida</Text>
              <Sparkles color={colors.black} size={19} strokeWidth={2.4} />
            </Pressable>

            <Text style={styles.sectionTitle}>Explorar lugares</Text>
            <View style={styles.cardList}>
              {cards.map((item) => (
                <HomeCard
                  key={item.title}
                  Icon={item.Icon}
                  description={item.description}
                  onPress={item.onPress}
                  title={item.title}
                />
              ))}
            </View>
          </View>

          <View style={styles.bottomBlock}>
            <View style={styles.assistRow}>
              <View style={styles.assistIcon}>
                <ShieldCheck color={colors.primaryLight} size={20} strokeWidth={2.2} />
              </View>
              <Text style={styles.assistText}>
                Calcula presupuesto, gustos y zonas antes de elegir dónde salir.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </Screen>
  );
}

function HomeCard({
  description,
  Icon,
  onPress,
  title,
}: {
  description: string;
  Icon: typeof Clock3;
  onPress: () => void;
  title: string;
}) {
  return (
    <Pressable
      accessibilityLabel={`${title}. ${description}`}
      accessibilityRole="button"
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      onPress={onPress}
    >
      <View style={styles.iconBox}>
        <Icon color={colors.primary} size={34} strokeWidth={2.1} />
      </View>
      <View style={styles.cardCopy}>
        <Text style={styles.cardTitle}>{title}</Text>
        <Text style={styles.cardDescription}>{description}</Text>
      </View>
      <ChevronRight color={colors.primaryLight} size={24} strokeWidth={2.4} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingBottom: 14,
    paddingTop: 8,
  },
  mainLayout: {
    flex: 1,
    justifyContent: "space-between",
  },
  topBlock: {
    gap: 22,
  },
  bottomBlock: {
    paddingTop: 14,
  },
  header: {
    gap: 10,
    paddingTop: 10,
  },
  sparkleWrap: {
    alignItems: "center",
    backgroundColor: "rgba(245, 158, 11, 0.08)",
    borderColor: "rgba(253, 186, 50, 0.22)",
    borderRadius: 18,
    borderWidth: 1,
    height: 48,
    justifyContent: "center",
    width: 48,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 44,
    fontWeight: "900",
    lineHeight: 50,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 17,
    lineHeight: 24,
  },
  cardList: {
    gap: 14,
  },
  sectionTitle: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
  card: {
    alignItems: "center",
    backgroundColor: "rgba(17, 25, 43, 0.82)",
    borderColor: colors.borderHighlighted,
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: "row",
    gap: 16,
    minHeight: 126,
    paddingHorizontal: 18,
    paddingVertical: 18,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.08,
    shadowRadius: 28,
  },
  cardPressed: {
    borderColor: "rgba(253, 186, 50, 0.56)",
    opacity: 0.88,
    transform: [{ scale: 0.992 }],
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
  cardCopy: {
    flex: 1,
    gap: 6,
  },
  cardTitle: {
    color: colors.textPrimary,
    fontSize: 18,
    fontWeight: "900",
  },
  cardDescription: {
    color: colors.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
  assistRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12,
    paddingHorizontal: 2,
  },
  assistIcon: {
    alignItems: "center",
    backgroundColor: "rgba(245, 158, 11, 0.12)",
    borderRadius: 12,
    height: 42,
    justifyContent: "center",
    width: 42,
  },
  assistText: {
    color: colors.textSecondary,
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primaryLight,
    borderColor: "rgba(255, 255, 255, 0.42)",
    borderRadius: 17,
    borderWidth: 1,
    flexDirection: "row",
    gap: 10,
    justifyContent: "center",
    minHeight: 68,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.42,
    shadowRadius: 26,
  },
  primaryLabel: {
    color: colors.black,
    fontSize: 18,
    fontWeight: "900",
  },
  pressed: {
    opacity: 0.86,
    transform: [{ scale: 0.99 }],
  },
});
