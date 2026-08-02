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
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import {
  Alert,
  FlatList,
  Linking,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import MapView, { Callout, Marker } from "react-native-maps";

import { getRecommendations, getVenues } from "@/api/client";
import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { nightColors as colors } from "@/theme/night";
import type { ParticipantCost, Recommendation, Venue } from "@/types/api";

type RecommendationViability = "viable" | "partially_viable" | "not_viable";

type RecommendationSummary = {
  excesses: number[];
  maxExcess: number | null;
  minExcess: number | null;
  totalParticipants: number;
  viability: RecommendationViability;
  withinBudgetCount: number;
};

export default function RecommendationsScreen() {
  const { planId } = useLocalSearchParams<{ planId?: string }>();
  const numericPlanId = Number(planId);
  const hasPlanId = Number.isFinite(numericPlanId) && numericPlanId > 0;
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const recommendationsQuery = useQuery<Recommendation[]>({
    enabled: hasPlanId,
    queryFn: () => getRecommendations(numericPlanId),
    queryKey: ["recommendations", numericPlanId],
    retry: false,
  });

  const venuesQuery = useQuery<Venue[]>({
    enabled: !hasPlanId,
    queryFn: getVenues,
    queryKey: ["venues", "map"],
    retry: false,
  });

  const recommendations: Recommendation[] = recommendationsQuery.data ?? [];
  const venues: Venue[] = venuesQuery.data ?? [];
  const enrichedRecommendations = recommendations.map((item) => ({
    item,
    summary: summarizeRecommendation(item),
  }));
  const hasViableOptions = enrichedRecommendations.some(
    ({ summary }) => summary.viability === "viable",
  );
  const sorted = [...enrichedRecommendations].sort((a, b) =>
    compareRecommendations(a, b, hasViableOptions),
  );
  const venueMarkers = venues
    .map((venue) => ({ venue, coordinates: getVenueCoordinates(venue) }))
    .filter(
      (item): item is { venue: Venue; coordinates: { latitude: number; longitude: number } } =>
        item.coordinates !== null,
    );
  const mapRegion = buildVenuesRegion(venueMarkers.map((item) => item.coordinates));

  return (
    <Screen>
      <NightBackground />
      <View style={styles.header}>
        <View style={styles.sparkleWrap}>
          <Sparkles color={colors.primaryLight} size={28} strokeWidth={1.9} />
        </View>
        <Text style={styles.kicker}>Recomendaciones</Text>
        <Text style={styles.title}>
          {hasPlanId && !hasViableOptions && !recommendationsQuery.isLoading && sorted.length > 0
            ? "No encontramos una opción que cumpla todo"
            : hasPlanId
              ? "Lugares para tu noche"
              : "Explorar lugares"}
        </Text>
        <Text style={styles.subtitle}>
          {hasPlanId && !hasViableOptions && !recommendationsQuery.isLoading && sorted.length > 0
            ? "Estas son las alternativas más cercanas y los ajustes necesarios para hacerlas viables."
            : hasPlanId
              ? "Ordenado por compatibilidad, presupuesto y traslados."
              : "Opciones generales de demostración. Inicia una salida para recomendaciones personalizadas."}
        </Text>
      </View>
      {hasPlanId ? (
        <>
          <View style={styles.statusWrap}>
            {recommendationsQuery.isLoading ? (
              <Text style={styles.message}>Calculando ranking...</Text>
            ) : null}
            {recommendationsQuery.error ? (
              <Text style={styles.message}>No se pudo consultar la API de recomendaciones.</Text>
            ) : null}
          </View>

          <View style={styles.listViewport}>
            <FlatList
              data={sorted}
              keyExtractor={({ item }) => String(item.id)}
              style={styles.listScroll}
              contentContainerStyle={styles.list}
              ListFooterComponent={
                !hasViableOptions && !recommendationsQuery.isLoading && sorted.length > 0 ? (
                  <AdjustmentActions />
                ) : null
              }
              renderItem={({ item: { item, summary } }) => (
                <RecommendationCard
                  expanded={expandedId === item.id}
                  item={item}
                  onPress={() => setExpandedId((current) => (current === item.id ? null : item.id))}
                  summary={summary}
                />
              )}
            />
          </View>
        </>
      ) : (
        <View style={styles.mapViewport}>
          <View style={styles.statusWrap}>
            <Text style={styles.message}>Mapa general de lugares disponibles.</Text>
            {venuesQuery.isLoading ? <Text style={styles.message}>Cargando lugares...</Text> : null}
            {venuesQuery.error ? (
              <Text style={styles.message}>No se pudo consultar la API de venues.</Text>
            ) : null}
          </View>

          <View style={styles.globalMapFrame}>
            {mapRegion ? (
              <MapView initialRegion={mapRegion} mapType="mutedStandard" style={styles.globalMap}>
                {venueMarkers.map(({ venue, coordinates }) => (
                  <Marker
                    key={venue.id}
                    coordinate={coordinates}
                    title={venue.name}
                    description={priceLevel(Number(venue.entry_price))}
                  >
                    <Callout tooltip>
                      <View style={styles.tooltip}>
                        <Text style={styles.tooltipTitle}>{venue.name}</Text>
                        <Text style={styles.tooltipPrice}>
                          {priceLevel(Number(venue.entry_price))}
                        </Text>
                      </View>
                    </Callout>
                  </Marker>
                ))}
              </MapView>
            ) : (
              <View style={styles.emptyMapState}>
                <Text style={styles.message}>
                  No hay coordenadas válidas para mostrar en el mapa.
                </Text>
              </View>
            )}
          </View>
        </View>
      )}
    </Screen>
  );
}

function RecommendationCard({
  expanded,
  item,
  onPress,
  summary,
}: {
  expanded: boolean;
  item: Recommendation;
  onPress: () => void;
  summary: RecommendationSummary;
}) {
  const venue = item.venue;
  const mapsUrl = buildMapsUrl(venue);
  const siteUrl = `https://www.google.com/search?q=${encodeURIComponent(`${venue.name} ${venue.zone}`)}`;
  const participantCosts = item.participant_costs ?? [];
  const reasons = item.reasons ?? [];
  const coordinates = getVenueCoordinates(venue);
  const viabilityMeta = getViabilityMeta(summary.viability);

  return (
    <View style={[styles.card, expanded && styles.cardExpanded]}>
      <Pressable
        accessibilityLabel={`${venue.name}, ${viabilityMeta.label}`}
        accessibilityRole="button"
        style={styles.cardTop}
        onPress={onPress}
      >
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{Math.round(item.score)}%</Text>
        </View>
        <View style={styles.cardTitleWrap}>
          <Text style={styles.cardTitle}>{venue.name}</Text>
          <Text style={styles.meta}>
            {venue.zone} · {priceLevel(Number(venue.entry_price))}
          </Text>
          <View
            accessibilityLabel={`Estado de viabilidad: ${viabilityMeta.label}`}
            accessibilityRole="text"
            style={[
              styles.viabilityBadge,
              summary.viability === "viable" && styles.viabilityBadgeGood,
              summary.viability === "partially_viable" && styles.viabilityBadgePartial,
              summary.viability === "not_viable" && styles.viabilityBadgeBad,
            ]}
          >
            <Text style={styles.viabilityText}>{viabilityMeta.label}</Text>
          </View>
        </View>
        {expanded ? (
          <ChevronUp color={colors.primaryLight} size={24} strokeWidth={2.4} />
        ) : (
          <ChevronDown color={colors.primaryLight} size={24} strokeWidth={2.4} />
        )}
      </Pressable>

      {expanded ? (
        <View style={styles.detail}>
          {coordinates ? (
            <View style={styles.mapFrame}>
              <MapView
                initialRegion={{
                  latitude: coordinates.latitude,
                  latitudeDelta: 0.012,
                  longitude: coordinates.longitude,
                  longitudeDelta: 0.012,
                }}
                mapType="mutedStandard"
                showsCompass={false}
                showsPointsOfInterest
                showsUserLocation={false}
                style={styles.map}
              >
                <Marker coordinate={coordinates} title={venue.name} description={venue.zone} />
              </MapView>
            </View>
          ) : null}

          <InfoLine Icon={MapPin} text={`Lugar: ${venue.zone}`} />
          <InfoLine
            Icon={Banknote}
            text={`Precio: entrada ${money(venue.entry_price)} · consumo promedio ${money(venue.average_drink_price)}`}
          />
          <InfoLine Icon={Car} text={`Traslado promedio: ${item.average_travel_minutes} min`} />

          <View style={styles.compatibility}>
            <Text style={styles.sectionLabel}>Resumen grupal</Text>
            <Text style={styles.summaryText}>Compatibilidad grupal: {Math.round(item.score)}%</Text>
            {summary.totalParticipants > 0 ? (
              <Text style={styles.summaryText}>
                {summary.withinBudgetCount} de {summary.totalParticipants} personas dentro de
                presupuesto
              </Text>
            ) : null}
            {summary.minExcess !== null ? (
              <Text style={styles.summaryText}>Exceso mínimo: {money(summary.minExcess)}</Text>
            ) : null}
            {summary.maxExcess !== null ? (
              <Text style={styles.summaryText}>Exceso máximo: {money(summary.maxExcess)}</Text>
            ) : null}
          </View>

          <View style={styles.compatibility}>
            <Text style={styles.sectionLabel}>Compatibilidad por amigo</Text>
            {participantCosts.map((cost, index) => (
              <View key={cost.id} style={styles.friendRow}>
                <View style={styles.friendCopy}>
                  <Text style={styles.friendName}>
                    {cost.participant?.name ?? `Amigo ${index + 1}`}
                  </Text>
                  <Text style={styles.friendBudget}>Estimado: {money(cost.total_cost)}</Text>
                  <Text style={styles.friendBudget}>
                    Presupuesto: {money(cost.participant?.budget ?? "0")}
                  </Text>
                  {!cost.within_budget ? (
                    <Text style={styles.friendBudget}>Exceso: {money(getExcess(cost))}</Text>
                  ) : null}
                </View>
                <Text style={[styles.friendScore, !cost.within_budget && styles.friendScoreOver]}>
                  {cost.within_budget ? "Dentro del presupuesto" : "Sobre presupuesto"}
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
            <ActionButton
              Icon={Globe}
              label="Sitio"
              onPress={() => void openExternalUrl(siteUrl)}
            />
            <ActionButton
              Icon={Navigation}
              label="Mapa"
              onPress={() => void openExternalUrl(mapsUrl)}
            />
          </View>
        </View>
      ) : null}
    </View>
  );
}

function buildMapsUrl(venue: Recommendation["venue"]) {
  const coordinates = getVenueCoordinates(venue);

  if (coordinates) {
    const query = encodeURIComponent(venue.name);
    if (Platform.OS === "ios") {
      return `maps://?ll=${coordinates.latitude},${coordinates.longitude}&q=${query}`;
    }
    return `geo:${coordinates.latitude},${coordinates.longitude}?q=${coordinates.latitude},${coordinates.longitude}(${query})`;
  }

  const query = encodeURIComponent(`${venue.name} ${venue.zone}`);
  return Platform.OS === "ios"
    ? `maps://?q=${query}`
    : `https://www.google.com/maps/search/?api=1&query=${query}`;
}

function getVenueCoordinates(venue: Recommendation["venue"]) {
  const latitude = Number(venue.latitude);
  const longitude = Number(venue.longitude);
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    return null;
  }
  return { latitude, longitude };
}

function buildVenuesRegion(coordinates: { latitude: number; longitude: number }[]) {
  if (!coordinates.length) {
    return null;
  }

  const latitudes = coordinates.map((point) => point.latitude);
  const longitudes = coordinates.map((point) => point.longitude);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const minLng = Math.min(...longitudes);
  const maxLng = Math.max(...longitudes);

  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: Math.max((maxLat - minLat) * 1.6, 0.03),
    longitudeDelta: Math.max((maxLng - minLng) * 1.6, 0.03),
  };
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
    <Pressable
      accessibilityLabel={label}
      accessibilityRole="button"
      style={styles.actionButton}
      onPress={onPress}
    >
      <Icon color={colors.black} size={17} strokeWidth={2.4} />
      <Text style={styles.actionText}>{label}</Text>
    </Pressable>
  );
}

function AdjustmentActions() {
  return (
    <View style={styles.adjustmentPanel}>
      <Text style={styles.sectionLabel}>Ajustes sugeridos</Text>
      <Text style={styles.reason}>
        Para hacer viable la salida, conviene cambiar presupuesto o zona desde el chat.
      </Text>
      <View style={styles.actions}>
        <ActionButton
          Icon={Banknote}
          label="Modificar presupuesto"
          onPress={() => router.push("/agent/chat" as never)}
        />
        <ActionButton
          Icon={MapPin}
          label="Cambiar zona"
          onPress={() => router.push("/agent/chat" as never)}
        />
      </View>
    </View>
  );
}

function summarizeRecommendation(item: Recommendation): RecommendationSummary {
  const participantCosts = item.participant_costs ?? [];
  const totalParticipants = participantCosts.length;
  const withinBudgetCount = participantCosts.filter((cost) => cost.within_budget).length;
  const excesses = participantCosts.map(getExcess).filter((excess) => excess > 0);
  const minExcess = excesses.length ? Math.min(...excesses) : null;
  const maxExcess = excesses.length ? Math.max(...excesses) : null;
  const majorityOutside =
    totalParticipants > 0 && withinBudgetCount < Math.ceil(totalParticipants / 2);
  const maxBudget = Math.max(
    ...participantCosts.map((cost) => Number(cost.participant?.budget ?? 0)),
    1,
  );
  const mildExcess = maxExcess !== null && maxExcess <= maxBudget * 0.25;

  let viability: RecommendationViability = "not_viable";
  if (totalParticipants > 0 && withinBudgetCount === totalParticipants) {
    viability = "viable";
  } else if (totalParticipants > 0 && !majorityOutside && mildExcess) {
    viability = "partially_viable";
  }

  return {
    excesses,
    maxExcess,
    minExcess,
    totalParticipants,
    viability,
    withinBudgetCount,
  };
}

function compareRecommendations(
  a: { item: Recommendation; summary: RecommendationSummary },
  b: { item: Recommendation; summary: RecommendationSummary },
  hasViableOptions: boolean,
) {
  if (!hasViableOptions) {
    const excessDiff =
      (a.summary.minExcess ?? Number.POSITIVE_INFINITY) -
      (b.summary.minExcess ?? Number.POSITIVE_INFINITY);
    if (excessDiff !== 0) {
      return excessDiff;
    }
    const scoreDiff = b.item.score - a.item.score;
    if (scoreDiff !== 0) {
      return scoreDiff;
    }
    return a.summary.excesses.length - b.summary.excesses.length;
  }

  const viabilityOrder: Record<RecommendationViability, number> = {
    viable: 0,
    partially_viable: 1,
    not_viable: 2,
  };
  const viabilityDiff = viabilityOrder[a.summary.viability] - viabilityOrder[b.summary.viability];
  if (viabilityDiff !== 0) {
    return viabilityDiff;
  }
  return b.item.score - a.item.score;
}

function getViabilityMeta(viability: RecommendationViability) {
  if (viability === "viable") {
    return { label: "Viable" };
  }
  if (viability === "partially_viable") {
    return { label: "Requiere ajustes" };
  }
  return { label: "No cumple presupuesto" };
}

function getExcess(cost: ParticipantCost) {
  const remaining = Number(cost.remaining_budget);
  if (Number.isFinite(remaining) && remaining < 0) {
    return Math.abs(remaining);
  }
  return Math.max(Number(cost.total_cost) - Number(cost.participant?.budget ?? 0), 0);
}

function money(value: string | number) {
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
  subtitle: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 21,
    maxWidth: 330,
  },
  message: {
    color: colors.textSecondary,
    fontSize: 15,
  },
  statusWrap: {
    gap: 6,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  list: {
    gap: 13,
    paddingHorizontal: 24,
    paddingBottom: 24,
  },
  listViewport: {
    flex: 1,
    minHeight: 0,
  },
  listScroll: {
    flex: 1,
  },
  mapViewport: {
    flex: 1,
    minHeight: 0,
  },
  globalMapFrame: {
    borderColor: colors.borderHighlighted,
    borderRadius: 18,
    borderWidth: 1,
    flex: 1,
    marginHorizontal: 24,
    marginBottom: 22,
    overflow: "hidden",
  },
  globalMap: {
    height: "100%",
    width: "100%",
  },
  emptyMapState: {
    alignItems: "center",
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 18,
  },
  tooltip: {
    backgroundColor: "rgba(13, 19, 34, 0.96)",
    borderColor: colors.borderHighlighted,
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
    minWidth: 140,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  tooltipTitle: {
    color: colors.textPrimary,
    fontSize: 13,
    fontWeight: "900",
  },
  tooltipPrice: {
    color: colors.primaryLight,
    fontSize: 12,
    fontWeight: "800",
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
  viabilityBadge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  viabilityBadgeGood: {
    backgroundColor: "rgba(34, 197, 94, 0.14)",
    borderColor: "rgba(74, 222, 128, 0.42)",
  },
  viabilityBadgePartial: {
    backgroundColor: "rgba(245, 158, 11, 0.14)",
    borderColor: "rgba(253, 186, 50, 0.42)",
  },
  viabilityBadgeBad: {
    backgroundColor: "rgba(248, 113, 113, 0.14)",
    borderColor: "rgba(252, 165, 165, 0.42)",
  },
  viabilityText: {
    color: colors.textPrimary,
    fontSize: 12,
    fontWeight: "900",
  },
  mapFrame: {
    borderColor: colors.borderHighlighted,
    borderRadius: 16,
    borderWidth: 1,
    height: 178,
    overflow: "hidden",
  },
  map: {
    height: "100%",
    width: "100%",
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
  summaryText: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  friendRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: 12,
    justifyContent: "space-between",
  },
  friendCopy: {
    flex: 1,
    gap: 3,
  },
  friendName: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: "700",
  },
  friendBudget: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "700",
  },
  friendScore: {
    color: colors.primaryLight,
    fontSize: 14,
    fontWeight: "900",
    maxWidth: 104,
    textAlign: "right",
  },
  friendScoreOver: {
    color: "#FCA5A5",
  },
  reason: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
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
  adjustmentPanel: {
    backgroundColor: "rgba(17, 25, 43, 0.82)",
    borderColor: colors.borderHighlighted,
    borderRadius: 18,
    borderWidth: 1,
    gap: 10,
    padding: 16,
  },
});
