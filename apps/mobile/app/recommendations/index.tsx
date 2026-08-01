import {
  Banknote,
  Car,
  ChevronDown,
  ChevronUp,
  Globe,
  MapPin,
  Navigation,
  Sparkles,
} from "lucide-react-native";
import { useQuery } from "@tanstack/react-query";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Alert, FlatList, Linking, Pressable, StyleSheet, Text, View } from "react-native";

import { getRecommendations } from "@/api/client";
import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { nightColors as colors } from "@/theme/night";
import type { Recommendation } from "@/types/api";

export default function RecommendationsScreen() {
  const { planId } = useLocalSearchParams<{ planId?: string }>();
  const numericPlanId = Number(planId);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const {
    data = [],
    isLoading,
    error,
  } = useQuery({
    enabled: Number.isFinite(numericPlanId) && numericPlanId > 0,
    queryFn: () => getRecommendations(numericPlanId),
    queryKey: ["recommendations", numericPlanId],
    retry: false,
  });

  const sorted = [...data].sort((a, b) => b.score - a.score);

  return (
    <Screen>
      <NightBackground />
      <View style={styles.header}>
        <View style={styles.sparkleWrap}>
          <Sparkles color={colors.primaryLight} size={28} strokeWidth={1.9} />
        </View>
        <Text style={styles.kicker}>Recomendaciones</Text>
        <Text style={styles.title}>Lugares para tu noche</Text>
      </View>

      {!planId ? (
        <Text style={styles.message}>Inicia una salida para calcular lugares con el backend.</Text>
      ) : null}
      {isLoading ? <Text style={styles.message}>Calculando ranking...</Text> : null}
      {error ? (
        <Text style={styles.message}>No se pudo consultar la API de recomendaciones.</Text>
      ) : null}

      <FlatList
        data={sorted}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <RecommendationCard
            expanded={expandedId === item.id}
            item={item}
            onPress={() => setExpandedId((current) => (current === item.id ? null : item.id))}
          />
        )}
      />
    </Screen>
  );
}

function RecommendationCard({
  expanded,
  item,
  onPress,
}: {
  expanded: boolean;
  item: Recommendation;
  onPress: () => void;
}) {
  const venue = item.venue;
  const mapsUrl = buildMapsUrl(venue);
  const siteUrl = `https://www.google.com/search?q=${encodeURIComponent(`${venue.name} ${venue.zone}`)}`;
  const participantCosts = item.participant_costs ?? [];
  const reasons = item.reasons ?? [];

  return (
    <Pressable style={[styles.card, expanded && styles.cardExpanded]} onPress={onPress}>
      <View style={styles.cardTop}>
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{Math.round(item.score)}%</Text>
        </View>
        <View style={styles.cardTitleWrap}>
          <Text style={styles.cardTitle}>{venue.name}</Text>
          <Text style={styles.meta}>
            {venue.zone} · {priceLevel(Number(venue.entry_price))}
          </Text>
        </View>
        {expanded ? (
          <ChevronUp color={colors.primaryLight} size={24} strokeWidth={2.4} />
        ) : (
          <ChevronDown color={colors.primaryLight} size={24} strokeWidth={2.4} />
        )}
      </View>

      {expanded ? (
        <View style={styles.detail}>
          <InfoLine Icon={MapPin} text={`Lugar: ${venue.zone}`} />
          <InfoLine
            Icon={Banknote}
            text={`Precio: entrada ${money(venue.entry_price)} · consumo promedio ${money(venue.average_drink_price)}`}
          />
          <InfoLine Icon={Car} text={`Traslado promedio: ${item.average_travel_minutes} min`} />

          <View style={styles.compatibility}>
            <Text style={styles.sectionLabel}>Compatibilidad por amigo</Text>
            {participantCosts.map((cost, index) => (
              <View key={cost.id} style={styles.friendRow}>
                <Text style={styles.friendName}>Amigo {index + 1}</Text>
                <Text style={styles.friendScore}>
                  {cost.within_budget
                    ? Math.round(item.score)
                    : Math.max(Math.round(item.score - 18), 0)}
                  %
                </Text>
              </View>
            ))}
          </View>

          {reasons.map((reason) => (
            <Text key={reason} style={styles.reason}>
              {reason}
            </Text>
          ))}

          <View style={styles.actions}>
            <ActionButton Icon={Globe} label="Sitio" onPress={() => void openExternalUrl(siteUrl)} />
            <ActionButton Icon={Navigation} label="Mapa" onPress={() => void openExternalUrl(mapsUrl)} />
          </View>
        </View>
      ) : null}
    </Pressable>
  );
}

function buildMapsUrl(venue: Recommendation["venue"]) {
  const hasCoordinates = Number.isFinite(venue.latitude) && Number.isFinite(venue.longitude);

  if (hasCoordinates) {
    return `https://www.google.com/maps/search/?api=1&query=${venue.latitude},${venue.longitude}`;
  }

  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${venue.name} ${venue.zone}`)}`;
}

async function openExternalUrl(url: string) {
  try {
    const supported = await Linking.canOpenURL(url);
    if (!supported) {
      Alert.alert("No se pudo abrir el enlace", "Tu dispositivo no puede abrir esta URL.");
      return;
    }

    await Linking.openURL(url);
  } catch {
    Alert.alert("Error", "No se pudo abrir el enlace externo.");
  }
}

function InfoLine({ Icon, text }: { Icon: typeof MapPin; text: string }) {
  return (
    <View style={styles.infoLine}>
      <Icon color={colors.primaryLight} size={17} strokeWidth={2.2} />
      <Text style={styles.infoText}>{text}</Text>
    </View>
  );
}

function ActionButton({
  Icon,
  label,
  onPress,
}: {
  Icon: typeof Globe;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable style={styles.actionButton} onPress={onPress}>
      <Icon color={colors.black} size={17} strokeWidth={2.4} />
      <Text style={styles.actionText}>{label}</Text>
    </Pressable>
  );
}

function money(value: string) {
  return `$${Number(value).toLocaleString("es-CL")}`;
}

function priceLevel(value: number) {
  if (value <= 4000) return "$";
  if (value <= 10000) return "$$";
  if (value <= 16000) return "$$$";
  return "$$$$";
}

const styles = StyleSheet.create({
  header: {
    gap: 8,
    paddingHorizontal: 24,
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
  message: {
    color: colors.textSecondary,
    fontSize: 15,
  },
  list: {
    gap: 13,
    paddingBottom: 24,
  },
  card: {
    backgroundColor: "rgba(17, 25, 43, 0.82)",
    borderColor: colors.borderHighlighted,
    borderRadius: 20,
    borderWidth: 1,
    padding: 16,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.08,
    shadowRadius: 28,
  },
  cardExpanded: {
    backgroundColor: "rgba(17, 25, 43, 0.9)",
  },
  cardTop: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12,
  },
  scoreBadge: {
    alignItems: "center",
    backgroundColor: colors.primaryLight,
    borderRadius: 16,
    height: 54,
    justifyContent: "center",
    width: 54,
  },
  scoreText: {
    color: colors.black,
    fontSize: 16,
    fontWeight: "900",
  },
  cardTitleWrap: {
    flex: 1,
    gap: 3,
  },
  cardTitle: {
    color: colors.textPrimary,
    fontSize: 19,
    fontWeight: "900",
  },
  meta: {
    color: colors.textSecondary,
    fontSize: 13,
    fontWeight: "700",
  },
  detail: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: 11,
    marginTop: 14,
    paddingTop: 14,
  },
  infoLine: {
    alignItems: "center",
    flexDirection: "row",
    gap: 8,
  },
  infoText: {
    color: colors.textPrimary,
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  compatibility: {
    gap: 8,
  },
  sectionLabel: {
    color: colors.primaryLight,
    fontSize: 13,
    fontWeight: "900",
  },
  friendRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  friendName: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: "700",
  },
  friendScore: {
    color: colors.textPrimary,
    fontSize: 14,
    fontWeight: "900",
  },
  reason: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  actions: {
    flexDirection: "row",
    gap: 10,
  },
  actionButton: {
    alignItems: "center",
    backgroundColor: colors.primaryLight,
    borderRadius: 14,
    flexDirection: "row",
    gap: 7,
    paddingHorizontal: 13,
    paddingVertical: 10,
  },
  actionText: {
    color: colors.black,
    fontSize: 13,
    fontWeight: "900",
  },
});
