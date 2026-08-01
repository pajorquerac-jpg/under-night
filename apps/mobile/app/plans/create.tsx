import { Minus, Plus, Sparkles, UsersRound } from "lucide-react-native";
import { useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { type ReactNode, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { submitNightQuestionnaire } from "@/api/client";
import { NightBackground } from "@/components/NightBackground";
import { Screen } from "@/components/Screen";
import { nightColors as colors } from "@/theme/night";
import type { FriendQuestionnaire, NightQuestionnaire } from "@/types/api";

const outingTypes = ["bar", "bailar", "stand up", "terraza", "house", "reggaeton"];
const zones = ["Centro", "Norte", "Sur", "Oriente"];

const defaultFriend = (index: number): FriendQuestionnaire => ({
  budget: "",
  consumptionLevel: "medium",
  maxEntryPrice: "",
  name: `Amigo ${index + 1}`,
  originZone: "Centro",
  outingType: "bar",
  transportType: "rideshare",
});

export default function CreatePlanScreen() {
  const [planName, setPlanName] = useState("Noche UnderNight");
  const [friendCount, setFriendCount] = useState(3);
  const [groupMode, setGroupMode] = useState<NightQuestionnaire["groupMode"]>("together");
  const [preferredZone, setPreferredZone] = useState("Centro");
  const [friends, setFriends] = useState<FriendQuestionnaire[]>([
    defaultFriend(0),
    defaultFriend(1),
    defaultFriend(2),
  ]);

  const mutation = useMutation({
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

  const changeFriendCount = (nextCount: number) => {
    const safeCount = Math.min(Math.max(nextCount, 1), 8);
    setFriendCount(safeCount);
    setFriends((current) =>
      Array.from({ length: safeCount }, (_, index) => current[index] ?? defaultFriend(index)),
    );
  };

  const updateFriend = (index: number, patch: Partial<FriendQuestionnaire>) => {
    setFriends((current) =>
      current.map((friend, friendIndex) =>
        friendIndex === index ? { ...friend, ...patch } : friend,
      ),
    );
  };

  const submit = () => {
    const missingMoney = friends.some((friend) => !friend.budget || !friend.maxEntryPrice);
    if (missingMoney) {
      Alert.alert("Falta presupuesto", "Agrega presupuesto y entrada maxima para cada amigo.");
      return;
    }

    mutation.mutate({
      friendCount,
      friends,
      groupMode,
      planName,
      preferredZone,
    });
  };

  return (
    <Screen>
      <NightBackground />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.sparkleWrap}>
            <Sparkles color={colors.primaryLight} size={28} strokeWidth={1.9} />
          </View>
          <Text style={styles.kicker}>Iniciar salida</Text>
          <Text style={styles.title}>Cuestionario rápido para recomendar la noche.</Text>
        </View>

        <GlassPanel>
          <Field
            label="Nombre del plan"
            value={planName}
            onChangeText={setPlanName}
            placeholder="Cumple, after, cita grupal"
          />
          <Text style={styles.label}>Cuantos amigos son</Text>
          <View style={styles.stepper}>
            <Pressable style={styles.iconButton} onPress={() => changeFriendCount(friendCount - 1)}>
              <Minus color={colors.textPrimary} size={20} strokeWidth={2.5} />
            </Pressable>
            <View style={styles.countBox}>
              <UsersRound color={colors.primaryLight} size={18} strokeWidth={2.1} />
              <Text style={styles.count}>{friendCount}</Text>
            </View>
            <Pressable style={styles.iconButton} onPress={() => changeFriendCount(friendCount + 1)}>
              <Plus color={colors.textPrimary} size={20} strokeWidth={2.5} />
            </Pressable>
          </View>

          <Text style={styles.label}>Zonas</Text>
          <View style={styles.segment}>
            <Chip
              active={groupMode === "together"}
              label="Todos juntos"
              onPress={() => setGroupMode("together")}
            />
            <Chip
              active={groupMode === "individual"}
              label="Individuales"
              onPress={() => setGroupMode("individual")}
            />
          </View>

          {groupMode === "together" ? (
            <>
              <Text style={styles.label}>Zona de salida grupal</Text>
              <View style={styles.chips}>
                {zones.map((zone) => (
                  <Chip
                    key={zone}
                    active={preferredZone === zone}
                    label={zone}
                    onPress={() => setPreferredZone(zone)}
                  />
                ))}
              </View>
            </>
          ) : null}
        </GlassPanel>

        {friends.map((friend, index) => (
          <GlassPanel key={index}>
            <Text style={styles.friendTitle}>Amigo {index + 1}</Text>
            <Field
              label="Nombre"
              value={friend.name}
              onChangeText={(value) => updateFriend(index, { name: value })}
              placeholder="Nombre"
            />
            <View style={styles.row}>
              <Field
                keyboardType="numeric"
                label="Presupuesto"
                value={friend.budget}
                onChangeText={(value) => updateFriend(index, { budget: value })}
                placeholder="25000"
              />
              <Field
                keyboardType="numeric"
                label="Entrada max."
                value={friend.maxEntryPrice}
                onChangeText={(value) => updateFriend(index, { maxEntryPrice: value })}
                placeholder="10000"
              />
            </View>

            <Text style={styles.label}>Tipo de salida</Text>
            <View style={styles.chips}>
              {outingTypes.map((type) => (
                <Chip
                  key={type}
                  active={friend.outingType === type}
                  label={type}
                  onPress={() => updateFriend(index, { outingType: type })}
                />
              ))}
            </View>

            {groupMode === "individual" ? (
              <>
                <Text style={styles.label}>Zona donde sale</Text>
                <View style={styles.chips}>
                  {zones.map((zone) => (
                    <Chip
                      key={zone}
                      active={friend.originZone === zone}
                      label={zone}
                      onPress={() => updateFriend(index, { originZone: zone })}
                    />
                  ))}
                </View>
              </>
            ) : null}
          </GlassPanel>
        ))}

        <Pressable
          style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}
          onPress={submit}
        >
          <Text style={styles.primaryLabel}>
            {mutation.isPending ? "Calculando..." : "Calcular recomendaciones"}
          </Text>
          <Sparkles color={colors.black} size={19} strokeWidth={2.4} />
        </Pressable>
      </ScrollView>
    </Screen>
  );
}

function GlassPanel({ children }: { children: ReactNode }) {
  return <View style={styles.panel}>{children}</View>;
}

function Field({
  keyboardType,
  label,
  onChangeText,
  placeholder,
  value,
}: {
  keyboardType?: "default" | "numeric";
  label: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  value: string;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        keyboardType={keyboardType}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="rgba(229, 229, 229, 0.46)"
        style={styles.input}
        value={value}
      />
    </View>
  );
}

function Chip({ active, label, onPress }: { active: boolean; label: string; onPress: () => void }) {
  return (
    <Pressable style={[styles.chip, active && styles.chipActive]} onPress={onPress}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: 18,
    paddingBottom: 28,
    paddingTop: 10,
    paddingHorizontal: 24,
  },
  header: {
    gap: 10,
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
  panel: {
    backgroundColor: "rgba(17, 25, 43, 0.82)",
    borderColor: colors.borderHighlighted,
    borderRadius: 20,
    borderWidth: 1,
    gap: 14,
    padding: 18,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.08,
    shadowRadius: 28,
  },
  label: {
    color: colors.textSecondary,
    fontSize: 13,
    fontWeight: "800",
  },
  field: {
    flex: 1,
    gap: 7,
  },
  input: {
    backgroundColor: "rgba(13, 19, 34, 0.94)",
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.textPrimary,
    fontSize: 16,
    paddingHorizontal: 13,
    paddingVertical: 12,
  },
  stepper: {
    alignItems: "center",
    flexDirection: "row",
    gap: 16,
  },
  iconButton: {
    alignItems: "center",
    backgroundColor: "rgba(13, 19, 34, 0.94)",
    borderColor: "rgba(93, 110, 156, 0.78)",
    borderRadius: 14,
    borderWidth: 1,
    height: 42,
    justifyContent: "center",
    width: 42,
  },
  countBox: {
    alignItems: "center",
    backgroundColor: "rgba(245, 158, 11, 0.1)",
    borderColor: "rgba(253, 186, 50, 0.24)",
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: "row",
    gap: 8,
    minWidth: 74,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  count: {
    color: colors.textPrimary,
    fontSize: 26,
    fontWeight: "900",
    textAlign: "center",
  },
  segment: {
    flexDirection: "row",
    gap: 10,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 9,
  },
  chip: {
    backgroundColor: "rgba(13, 19, 34, 0.92)",
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  chipActive: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primaryLight,
  },
  chipText: {
    color: colors.textSecondary,
    fontSize: 13,
    fontWeight: "800",
  },
  chipTextActive: {
    color: colors.black,
  },
  friendTitle: {
    color: colors.textPrimary,
    fontSize: 21,
    fontWeight: "900",
  },
  row: {
    flexDirection: "row",
    gap: 10,
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
    minHeight: 64,
    shadowColor: colors.primary,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.34,
    shadowRadius: 24,
  },
  primaryLabel: {
    color: colors.black,
    fontSize: 17,
    fontWeight: "900",
  },
  pressed: {
    opacity: 0.86,
    transform: [{ scale: 0.99 }],
  },
});
