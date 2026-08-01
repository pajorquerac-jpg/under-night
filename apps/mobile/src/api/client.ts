import Constants from "expo-constants";

import type {
  HealthResponse,
  NightQuestionnaire,
  Participant,
  Plan,
  Recommendation,
  Venue,
} from "@/types/api";

const extraApiUrl = Constants.expoConfig?.extra?.apiUrl as string | undefined;
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? extraApiUrl ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: "Unexpected API error" }));
    throw new ApiError(errorBody.detail ?? "Unexpected API error", response.status);
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getVenues(): Promise<Venue[]> {
  return request<Venue[]>("/api/v1/venues");
}

export function createPlan(payload: {
  name: string;
  event_date: string;
  start_time: string;
  decision_deadline: string;
  preferred_zone: string;
  plan_type: string;
}): Promise<Plan> {
  return request<Plan>("/api/v1/plans", {
    body: JSON.stringify(payload),
    method: "POST",
  });
}

export function createParticipant(
  planId: number,
  payload: {
    name: string;
    budget: string;
    max_entry_price: string;
    origin_zone: string;
    transport_type: string;
    consumption_level: string;
    max_return_time: string;
    preferences: Record<string, unknown>;
    restrictions: Record<string, unknown>;
  },
): Promise<Participant> {
  return request<Participant>(`/api/v1/plans/${planId}/participants`, {
    body: JSON.stringify(payload),
    method: "POST",
  });
}

export function createRecommendations(planId: number): Promise<Recommendation[]> {
  return request<Recommendation[]>(`/api/v1/plans/${planId}/recommendations`, {
    method: "POST",
  });
}

export function getRecommendations(planId: number): Promise<Recommendation[]> {
  return request<Recommendation[]>(`/api/v1/plans/${planId}/recommendations`);
}

export async function submitNightQuestionnaire(
  payload: NightQuestionnaire,
): Promise<Recommendation[]> {
  return request<Recommendation[]>("/api/v1/night-out/recommendations", {
    body: JSON.stringify({
      friend_count: payload.friendCount,
      friends: payload.friends.map((friend) => ({
        budget: friend.budget || "25000",
        consumption_level: friend.consumptionLevel,
        max_entry_price: friend.maxEntryPrice || "10000",
        name: friend.name,
        origin_zone: friend.originZone,
        outing_type: friend.outingType,
        transport_type: friend.transportType,
      })),
      group_mode: payload.groupMode,
      plan_name: payload.planName || "Salida UnderNight",
      preferred_zone: payload.preferredZone || payload.friends[0]?.originZone || "Centro",
    }),
    method: "POST",
  });
}
