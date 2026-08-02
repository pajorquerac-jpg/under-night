export type HealthResponse = {
  status: string;
  service: string;
};

export type Venue = {
  id: number;
  name: string;
  zone: string;
  latitude: number;
  longitude: number;
  entry_price: string;
  average_drink_price: string;
  opening_time: string;
  closing_time: string;
  minimum_age: number;
  music_tags: string[];
  ambience_tags: string[];
  features: Record<string, unknown>;
  data_updated_at: string;
  created_at: string;
  updated_at: string;
};

export type Plan = {
  id: number;
  name: string;
  event_date: string;
  start_time: string;
  decision_deadline: string;
  preferred_zone: string;
  plan_type: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Participant = {
  id: number;
  plan_id: number;
  name: string;
  budget: string;
  max_entry_price: string;
  origin_zone: string;
  transport_type: string;
  consumption_level: string;
  max_return_time: string | null;
  preferences: Record<string, unknown>;
  restrictions: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ParticipantCost = {
  id: number;
  recommendation_id: number;
  participant_id: number;
  entry_cost: string;
  consumption_cost: string;
  transport_cost: string;
  total_cost: string;
  remaining_budget: string;
  within_budget: boolean;
  participant: Participant;
};

export type Recommendation = {
  id: number;
  plan_id: number;
  venue_id: number;
  created_at: string;
  score: number;
  category: string;
  estimated_average_cost: string;
  all_within_budget: boolean;
  average_travel_minutes: number;
  reasons: string[];
  tradeoffs: string[];
  venue: Venue;
  participant_costs: ParticipantCost[];
};

export type FriendQuestionnaire = {
  name: string;
  budget: string;
  maxEntryPrice: string;
  outingType: string;
  originZone: string;
  transportType: "walking" | "public_transport" | "rideshare" | "car";
  consumptionLevel: "low" | "medium" | "high" | "custom";
};

export type NightQuestionnaire = {
  friendCount: number;
  groupMode: "together" | "individual";
  planName: string;
  preferredZone: string;
  friends: FriendQuestionnaire[];
};

export type PlanDraft = {
  name: string;
  eventDate: string;
  startTime: string;
  planType: string;
  preferredZone: string;
  decisionDeadline: string;
};

export type AgentParticipant = {
  name: string | null;
  budget: number | null;
  origin_zone: string | null;
};

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  status?: "sending" | "sent" | "error";
};

export type AgentConversationState = {
  people_count: number | null;
  budget_per_person: number | null;
  participants: AgentParticipant[];
  event_date: string | null;
  event_date_text: string | null;
  event_date_needs_confirmation: boolean;
  origin_zones: string[];
  meeting_point: string | null;
  outing_type: string | null;
  music_preferences: string[];
  restrictions: string[];
  restrictions_confirmed: boolean;
  missing_fields: string[];
  stage: string;
};

export type SuggestedAction = {
  label: string;
  type: string;
  payload: Record<string, unknown>;
};

export type AgentChatRequest = {
  message: string;
  conversation_id?: string;
};

export type AgentChatResponse = {
  conversation_id: string;
  reply: string;
  provider: string;
  model: string | null;
  state: AgentConversationState;
  used_fallback: boolean;
  suggested_actions: SuggestedAction[];
};
