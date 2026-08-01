import { BadgePercent, Sparkles } from "lucide-react-native";
import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { nightColors as colors } from "@/theme/night";

export default function RecommendationDetailScreen() {
  const { recommendationId } = useLocalSearchParams<{ recommendationId: string }>();

  return (
    <Screen>
      <NightBackground />
      <View style={styles.header}>
        <View style={styles.sparkleWrap}>
          <Sparkles color={colors.primaryLight} size={28} strokeWidth={1.9} />
        </View>
        <Text style={styles.kicker}>Recomendación</Text>
        <Text style={styles.title}>Lugar #{recommendationId}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.iconBox}>
          <BadgePercent color={colors.primary} size={34} strokeWidth={2.1} />
        </View>
        <Text style={styles.cardTitle}>Detalle de compatibilidad</Text>
        <Text style={styles.cardText}>
          Vista preparada para mostrar razones, costos por amigo, trade-offs y links de reserva o
          traslado.
        </Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: 8,
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
  card: {
    backgroundColor: "rgba(17, 25, 43, 0.82)",
    borderColor: colors.borderHighlighted,
    borderRadius: 20,
    borderWidth: 1,
    gap: 14,
    padding: 18,
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
  cardTitle: {
    color: colors.textPrimary,
    fontSize: 21,
    fontWeight: "900",
    lineHeight: 27,
  },
  cardText: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 22,
  },
});
