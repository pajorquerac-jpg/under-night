import Constants from "expo-constants";

import type {
  AgentChatRequest,
  AgentChatResponse,
  HealthResponse,
  NightQuestionnaire,
  Participant,
  Plan,
  Recommendation,
  Venue,
} from "@/types/api";

const extraApiUrl = Constants.expoConfig?.extra?.apiUrl as string | undefined;

function inferApiUrlFromExpoHost(): string | undefined {
  const hostUri =
    (Constants.expoConfig?.hostUri as string | undefined) ??
    (Constants.manifest2?.extra?.expoGo?.debuggerHost as string | undefined);

  if (!hostUri) {
    return undefined;
  }

  const host = hostUri.split(":")[0];
  if (!host) {
    return undefined;
  }

  return `http://${host}:8000`;
}

const inferredApiUrl = inferApiUrlFromExpoHost();
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? extraApiUrl ?? inferredApiUrl ?? "http://localhost:8000";

const AGENT_TIMEOUT_MS = 120_000;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class ApiTimeoutError extends Error {
  constructor(message = "La API tardó demasiado en responder.") {
    super(message);
    this.name = "ApiTimeoutError";
  }
}

export class ApiNetworkError extends Error {
  constructor(message = "No se pudo conectar con el backend.") {
    super(message);
    this.name = "ApiNetworkError";
  }
}

export class ApiInvalidResponseError extends Error {
  constructor(message = "La API devolvió una respuesta inválida.") {
    super(message);
    this.name = "ApiInvalidResponseError";
  }
}

function isAbortError(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "name" in error &&
    String(error.name) === "AbortError"
  );
}

if (__DEV__ && !process.env.EXPO_PUBLIC_API_URL && !extraApiUrl) {
  console.warn(
    `EXPO_PUBLIC_API_URL no está definida. Usando ${API_BASE_URL}. ` +
      "Configúrala para evitar problemas entre simulador y dispositivo físico.",
  );
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new ApiInvalidResponseError("La API no devolvió JSON válido.");
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      ...init,
    });
  } catch {
    throw new ApiNetworkError();
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: "Unexpected API error" }));
    const detail =
      typeof errorBody === "object" && errorBody !== null && "detail" in errorBody
        ? String(errorBody.detail)
        : "Unexpected API error";
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

async function requestWithTimeout<T>(
  path: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...init.headers,
        },
        ...init,
        signal: controller.signal,
      });
    } catch (error) {
      if (isAbortError(error)) {
        throw new ApiTimeoutError();
      }
      throw new ApiNetworkError();
    }

    const body = await readJson(response);
    if (!response.ok) {
      const detail =
        typeof body === "object" && body !== null && "detail" in body
          ? String(body.detail)
          : "Unexpected API error";
      throw new ApiError(detail, response.status);
    }

    return body as T;
  } finally {
    clearTimeout(timeoutId);
  }
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

export function sendAgentMessage(payload: AgentChatRequest): Promise<AgentChatResponse> {
  return requestWithTimeout<AgentChatResponse>(
    "/api/v1/agent/chat",
    {
      body: JSON.stringify(payload),
      method: "POST",
    },
    AGENT_TIMEOUT_MS,
  );
}
