import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { ArrowUp, Bot, ChevronLeft, RotateCcw, Sparkles } from "lucide-react-native";

import { submitNightQuestionnaire } from "@/api/client";
import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { useAgentChat } from "@/hooks/useAgentChat";
import { nightColors as colors } from "@/theme/night";
import type {
  AgentConversationState,
  ChatMessage,
  NightQuestionnaire,
  SuggestedAction,
} from "@/types/api";

const ALLOWED_AGENT_ROUTES = ["/plans/create", "/recommendations"] as const;

const FIELD_LABELS: Record<string, string> = {
  people_count: "cantidad de personas",
  budget_per_person: "presupuesto",
  event_date: "fecha",
  origin_zones: "comunas de origen",
  meeting_point: "punto de encuentro",
  outing_type: "tipo de salida",
  music_preferences: "preferencias musicales",
  restrictions: "restricciones",
};
const BASE_FIELD_KEYS = [
  "people_count",
  "budget_per_person",
  "event_date",
  "origin_zones",
  "outing_type",
  "music_preferences",
  "restrictions",
] as const;
const TOTAL_BASE_FIELDS = BASE_FIELD_KEYS.length;

export default function AgentChatScreen() {
  const listRef = useRef<FlatList<ChatMessage>>(null);
  const [draft, setDraft] = useState("");
  const chat = useAgentChat();
  const scrollToLatest = useCallback((animated = true) => {
    requestAnimationFrame(() => {
      listRef.current?.scrollToEnd({ animated });
    });
  }, []);

  useEffect(() => {
    scrollToLatest(true);
  }, [chat.messages.length, chat.isSending, chat.suggestedActions.length, scrollToLatest]);

  const recommendationsMutation = useMutation({
    mutationFn: submitNightQuestionnaire,
    onError: () => {
      Alert.alert(
        "No se pudo calcular",
        "Revisa que la API este corriendo y que exista data seed de lugares.",
      );
    },
    onSuccess: (recommendations) => {
      const planId = recommendations[0]?.plan_id;
      router.push(planId ? `/recommendations?planId=${planId}` : "/recommendations");
    },
  });

  const progress = useMemo(() => {
    if (!chat.state) {
      return {
        completed: 0,
        isReady: false,
        missing: [] as string[],
        subtitle: "Cuéntame qué panorama están buscando",
        title: `Datos base · 0 de ${TOTAL_BASE_FIELDS} datos`,
        total: TOTAL_BASE_FIELDS,
      };
    }
    const missing = chat.state.missing_fields ?? [];
    const total = TOTAL_BASE_FIELDS;
    const completed = Math.max(total - missing.length, 0);
    const isReady = isRecommendationReady(chat.state);
    return {
      completed,
      isReady,
      missing,
      subtitle: isReady ? "Ya podemos comparar alternativas" : missingText(missing),
      title: isReady
        ? `Todo listo · ${total} de ${total} datos`
        : completed >= total - 1
          ? `Casi listo · ${completed} de ${total} datos`
          : `Datos base · ${completed} de ${total} datos`,
      total,
    };
  }, [chat.state]);

  const visibleSuggestedActions = useMemo(
    () =>
      chat.suggestedActions.filter(
        (action) => action.label.trim().toLowerCase() !== "iniciar salida",
      ),
    [chat.suggestedActions],
  );
  const hasRecommendationsAction = visibleSuggestedActions.some(
    (action) => action.label.trim().toLowerCase() === "ver recomendaciones",
  );
  const showReadyAction = progress.isReady && !hasRecommendationsAction;

  const sendDraft = async () => {
    const message = draft.trim();
    if (!message || chat.isSending) {
      return;
    }
    setDraft("");
    scrollToLatest(true);
    await chat.sendMessage(message);
  };

  const confirmReset = () => {
    Alert.alert("Reiniciar conversación", "Se borrará esta conversación local.", [
      { style: "cancel", text: "Cancelar" },
      { onPress: chat.resetConversation, style: "destructive", text: "Reiniciar" },
    ]);
  };

  const runRecommendationsAction = () => {
    if (!chat.state || chat.state.missing_fields.length > 0) {
      Alert.alert("Faltan datos", "Completa los datos base antes de calcular recomendaciones.");
      return;
    }

    recommendationsMutation.mutate(questionnaireFromState(chat.state));
  };

  const handleSuggestedAction = (action: SuggestedAction) => {
    if (action.type === "submit") {
      runRecommendationsAction();
      return;
    }

    if (action.type !== "navigate") {
      Alert.alert("Acción pendiente", "Esta acción estará disponible en una próxima versión.");
      return;
    }

    const route = action.payload.route;
    if (typeof route !== "string" || !isAllowedRoute(route)) {
      Alert.alert("Ruta no disponible", "Esta acción no está habilitada en la app móvil.");
      return;
    }

    if (route === "/recommendations" && progress.isReady) {
      runRecommendationsAction();
      return;
    }

    router.push(route as never);
  };

  const renderMessage = ({ index, item }: { index: number; item: ChatMessage }) => {
    const isUser = item.role === "user";
    const isLastAssistant =
      item.role === "assistant" &&
      index === chat.messages.length - 1 &&
      visibleSuggestedActions.length > 0;

    return (
      <View style={[styles.messageRow, isUser && styles.userMessageRow]}>
        {!isUser && (
          <View style={styles.botIcon}>
            <Bot color={colors.primaryLight} size={17} strokeWidth={2.2} />
          </View>
        )}

        <View style={styles.messageStack}>
          <Pressable
            disabled={item.status !== "error"}
            onPress={() => chat.retryMessage(item.id)}
            style={[
              styles.bubble,
              isUser ? styles.userBubble : styles.assistantBubble,
              item.status === "error" && styles.errorBubble,
            ]}
          >
            <Text style={[styles.messageText, isUser && styles.userMessageText]}>
              {item.content}
            </Text>
            {item.status === "error" && <Text style={styles.errorHint}>Toca para reintentar</Text>}
          </Pressable>

          {isLastAssistant && (
            <View style={styles.actionRow}>
              {visibleSuggestedActions.map((action) => (
                <Pressable
                  accessibilityLabel={action.label}
                  accessibilityRole="button"
                  key={`${action.type}-${action.label}`}
                  disabled={recommendationsMutation.isPending}
                  onPress={() => handleSuggestedAction(action)}
                  style={({ pressed }) => [
                    styles.actionChip,
                    recommendationsMutation.isPending && styles.actionChipDisabled,
                    pressed && styles.pressed,
                  ]}
                >
                  <Text style={styles.actionText}>
                    {action.type === "submit" && recommendationsMutation.isPending
                      ? "Calculando..."
                      : action.label}
                  </Text>
                </Pressable>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <Screen>
      <NightBackground />

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={Platform.OS === "ios" ? 8 : 0}
        style={styles.container}
      >
        <View style={styles.header}>
          <Pressable
            accessibilityLabel="Volver"
            accessibilityRole="button"
            onPress={() => router.back()}
            style={({ pressed }) => [styles.iconButton, pressed && styles.pressed]}
          >
            <ChevronLeft color={colors.textPrimary} size={22} strokeWidth={2.4} />
          </Pressable>

          <View style={styles.headerCopy}>
            <Text style={styles.title}>Planear salida</Text>
            <Text style={styles.subtitle}>Asistente de planificación</Text>
          </View>

          <Pressable
            accessibilityLabel="Reiniciar conversación"
            accessibilityRole="button"
            onPress={confirmReset}
            style={({ pressed }) => [styles.iconButton, pressed && styles.pressed]}
          >
            <RotateCcw color={colors.primaryLight} size={20} strokeWidth={2.3} />
          </Pressable>
        </View>
        <View style={styles.progressPanel}>
          <View style={styles.progressMeta}>
            <Text style={styles.progressTitle}>{progress.title}</Text>
            <Text style={styles.progressMissing} numberOfLines={2}>
              {progress.subtitle}
            </Text>
          </View>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressFill,
                { width: `${Math.min((progress.completed / progress.total) * 100, 100)}%` },
              ]}
            />
          </View>
          {showReadyAction ? (
            <Pressable
              accessibilityLabel="Ver recomendaciones"
              accessibilityRole="button"
              disabled={recommendationsMutation.isPending}
              onPress={runRecommendationsAction}
              style={({ pressed }) => [
                styles.readyAction,
                recommendationsMutation.isPending && styles.actionChipDisabled,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.readyActionText}>
                {recommendationsMutation.isPending ? "Calculando..." : "Ver recomendaciones"}
              </Text>
            </Pressable>
          ) : null}
        </View>
        <FlatList
          ref={listRef}
          contentContainerStyle={styles.messageList}
          data={chat.messages}
          keyExtractor={(item) => item.id}
          ListFooterComponent={
            chat.isSending ? (
              <View style={styles.messageRow}>
                <View style={styles.botIcon}>
                  <Sparkles color={colors.primaryLight} size={17} strokeWidth={2.2} />
                </View>
                <View style={[styles.bubble, styles.assistantBubble, styles.loadingBubble]}>
                  <Text style={styles.messageText}>Pensando...</Text>
                </View>
              </View>
            ) : null
          }
          onContentSizeChange={() => scrollToLatest(false)}
          renderItem={renderMessage}
          showsVerticalScrollIndicator={false}
        />

        {chat.error && <Text style={styles.globalError}>{chat.error}</Text>}

        <View style={styles.composer}>
          <TextInput
            editable={!chat.isSending}
            multiline
            onChangeText={setDraft}
            onFocus={() => scrollToLatest(true)}
            placeholder="Cuéntame qué quieren hacer..."
            placeholderTextColor={colors.textMuted}
            returnKeyType="send"
            style={styles.input}
            value={draft}
          />
          <Pressable
            accessibilityLabel="Enviar mensaje"
            accessibilityRole="button"
            disabled={!draft.trim() || chat.isSending}
            onPress={sendDraft}
            style={({ pressed }) => [
              styles.sendButton,
              (!draft.trim() || chat.isSending) && styles.sendButtonDisabled,
              pressed && styles.pressed,
            ]}
          >
            <ArrowUp color={colors.black} size={21} strokeWidth={2.7} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

function isRecommendationReady(state: AgentConversationState) {
  return (
    state.missing_fields.length === 0 ||
    state.stage === "ready_to_recommend" ||
    state.stage === "ready_for_recommendations"
  );
}

function missingText(missing: string[]) {
  if (!missing.length) {
    return "Ya podemos comparar alternativas";
  }
  const labels = missing.map((field) => FIELD_LABELS[field] ?? field);
  if (labels.length === 1) {
    return labels[0] === FIELD_LABELS.restrictions
      ? "Falta confirmar si tienen restricciones"
      : `Falta: ${labels[0]}`;
  }
  return `Faltan: ${joinWithAnd(labels)}`;
}

function joinWithAnd(values: string[]) {
  if (values.length <= 1) {
    return values[0] ?? "";
  }
  return `${values.slice(0, -1).join(", ")} y ${values[values.length - 1]}`;
}

function isAllowedRoute(route: string): route is (typeof ALLOWED_AGENT_ROUTES)[number] {
  return ALLOWED_AGENT_ROUTES.includes(route as (typeof ALLOWED_AGENT_ROUTES)[number]);
}

function questionnaireFromState(state: AgentConversationState): NightQuestionnaire {
  const participants = state.participants ?? [];
  const friendCount = Math.min(Math.max(state.people_count ?? 1, participants.length, 1), 8);
  const preferredZone = preferredZoneFromState(state);
  const originZones = state.origin_zones.length > 0 ? state.origin_zones : [preferredZone];
  const outingType = [state.outing_type, ...state.music_preferences].filter(Boolean).join(", ");

  return {
    friendCount,
    friends: Array.from({ length: friendCount }, (_, index) => {
      const participant = participants[index];
      const budget = String(participant?.budget ?? state.budget_per_person ?? 25000);

      return {
        budget,
        consumptionLevel: "medium",
        maxEntryPrice: String(Math.min(Number(budget) || 25000, 10000)),
        name: participant?.name ?? `Amigo ${index + 1}`,
        originZone:
          participant?.origin_zone ?? originZones[index % originZones.length] ?? preferredZone,
        outingType: outingType || "bar",
        transportType: "rideshare",
      };
    }),
    groupMode:
      participants.some((participant) => participant.origin_zone) || originZones.length > 1
        ? "individual"
        : "together",
    planName: "Salida UnderNight",
    preferredZone,
  };
}

function preferredZoneFromState(state: AgentConversationState) {
  const restrictionText = state.restrictions.join(" ").toLowerCase();
  const restrictedZone = ["oriente", "centro", "norte", "sur"].find((zone) =>
    restrictionText.includes(zone),
  );
  if (restrictedZone) {
    return capitalize(restrictedZone);
  }
  return state.origin_zones[0] ?? "Centro";
}

function capitalize(value: string) {
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 18,
    paddingTop: 4,
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12,
    paddingBottom: 14,
  },
  iconButton: {
    alignItems: "center",
    backgroundColor: "rgba(17, 25, 43, 0.76)",
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    height: 46,
    justifyContent: "center",
    width: 46,
  },
  headerCopy: {
    flex: 1,
    gap: 3,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 22,
    fontWeight: "900",
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 13,
  },
  messageList: {
    gap: 14,
    paddingBottom: 18,
    paddingTop: 8,
  },
  messageRow: {
    alignItems: "flex-end",
    flexDirection: "row",
    gap: 10,
  },
  userMessageRow: {
    justifyContent: "flex-end",
  },
  botIcon: {
    alignItems: "center",
    backgroundColor: "rgba(245, 158, 11, 0.1)",
    borderColor: "rgba(253, 186, 50, 0.22)",
    borderRadius: 13,
    borderWidth: 1,
    height: 34,
    justifyContent: "center",
    width: 34,
  },
  messageStack: {
    maxWidth: "82%",
  },
  bubble: {
    borderRadius: 18,
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  assistantBubble: {
    backgroundColor: "rgba(17, 25, 43, 0.86)",
    borderColor: colors.borderHighlighted,
    borderWidth: 1,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: colors.primaryLight,
  },
  loadingBubble: {
    minWidth: 118,
  },
  errorBubble: {
    borderColor: "#EF4444",
    borderWidth: 1,
  },
  messageText: {
    color: colors.textPrimary,
    fontSize: 15,
    lineHeight: 21,
  },
  userMessageText: {
    color: colors.black,
    fontWeight: "700",
  },
  errorHint: {
    color: "#FCA5A5",
    fontSize: 12,
    fontWeight: "700",
    marginTop: 6,
  },
  actionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8,
  },
  actionChip: {
    backgroundColor: "rgba(245, 158, 11, 0.12)",
    borderColor: "rgba(253, 186, 50, 0.38)",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  actionChipDisabled: {
    opacity: 0.62,
  },
  actionText: {
    color: colors.primaryLight,
    fontSize: 13,
    fontWeight: "800",
  },
  readyAction: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: colors.primaryLight,
    borderRadius: 14,
    minHeight: 42,
    justifyContent: "center",
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  readyActionText: {
    color: colors.black,
    fontSize: 13,
    fontWeight: "900",
  },
  globalError: {
    color: "#FCA5A5",
    fontSize: 13,
    lineHeight: 18,
    paddingBottom: 8,
    paddingHorizontal: 4,
  },
  progressPanel: {
    backgroundColor: "rgba(13, 19, 34, 0.84)",
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    gap: 10,
    marginBottom: 10,
    padding: 12,
  },
  progressMeta: {
    gap: 3,
  },
  progressTitle: {
    color: colors.textPrimary,
    fontSize: 13,
    fontWeight: "900",
  },
  progressMissing: {
    color: colors.textMuted,
    fontSize: 12,
  },
  progressTrack: {
    backgroundColor: "rgba(124, 132, 151, 0.24)",
    borderRadius: 999,
    height: 6,
    overflow: "hidden",
  },
  progressFill: {
    backgroundColor: colors.primaryLight,
    borderRadius: 999,
    height: "100%",
  },
  composer: {
    alignItems: "flex-end",
    backgroundColor: "rgba(17, 25, 43, 0.92)",
    borderColor: colors.borderHighlighted,
    borderRadius: 22,
    borderWidth: 1,
    flexDirection: "row",
    gap: 10,
    marginBottom: 8,
    padding: 10,
  },
  input: {
    color: colors.textPrimary,
    flex: 1,
    fontSize: 15,
    lineHeight: 21,
    maxHeight: 112,
    minHeight: 42,
    paddingHorizontal: 4,
    paddingVertical: 10,
  },
  sendButton: {
    alignItems: "center",
    backgroundColor: colors.primaryLight,
    borderRadius: 16,
    height: 46,
    justifyContent: "center",
    width: 46,
  },
  sendButtonDisabled: {
    opacity: 0.42,
  },
  pressed: {
    opacity: 0.78,
    transform: [{ scale: 0.98 }],
  },
});
