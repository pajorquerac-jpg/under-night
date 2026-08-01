from dataclasses import dataclass
from decimal import Decimal

from app.core.config import settings
from app.models.participant import Participant
from app.models.venue import Venue
from app.recommendation.rules import transport_cost, travel_minutes
from app.recommendation.scoring import score_venue


@dataclass(frozen=True)
class ParticipantCostEstimate:
    participant_id: int
    entry_cost: Decimal
    consumption_cost: Decimal
    transport_cost: Decimal
    total_cost: Decimal
    remaining_budget: Decimal
    within_budget: bool


@dataclass(frozen=True)
class RecommendationEstimate:
    venue: Venue
    score: float
    category: str
    estimated_average_cost: Decimal
    all_within_budget: bool
    average_travel_minutes: int
    reasons: list[str]
    tradeoffs: list[str]
    participant_costs: list[ParticipantCostEstimate]


def estimate_consumption(level: str, average_drink_price: Decimal) -> Decimal:
    if level == "custom":
        return average_drink_price * Decimal(settings.consumption_units["medium"])
    return average_drink_price * Decimal(settings.consumption_units.get(level, 2))


def rank_venues(
    participants: list[Participant],
    venues: list[Venue],
) -> list[RecommendationEstimate]:
    estimates = [_estimate_venue(participants, venue) for venue in venues]
    return sorted(estimates, key=lambda item: item.score, reverse=True)


def _estimate_venue(participants: list[Participant], venue: Venue) -> RecommendationEstimate:
    costs: list[ParticipantCostEstimate] = []
    music_matches = 0
    ambience_matches = 0
    travel_values: list[int] = []

    for participant in participants:
        consumption_cost = estimate_consumption(
            participant.consumption_level,
            venue.average_drink_price,
        )
        travel_cost = transport_cost(
            participant.origin_zone,
            venue.zone,
            participant.transport_type,
        )
        total = venue.entry_price + consumption_cost + travel_cost
        remaining = participant.budget - total
        within_budget = (
            total <= participant.budget and venue.entry_price <= participant.max_entry_price
        )
        costs.append(
            ParticipantCostEstimate(
                participant_id=participant.id,
                entry_cost=venue.entry_price,
                consumption_cost=consumption_cost,
                transport_cost=travel_cost,
                total_cost=total,
                remaining_budget=remaining,
                within_budget=within_budget,
            )
        )
        desired_music = set(participant.preferences.get("music_tags", []))
        desired_ambience = set(participant.preferences.get("ambience_tags", []))
        music_matches += len(desired_music.intersection(venue.music_tags))
        ambience_matches += len(desired_ambience.intersection(venue.ambience_tags))
        travel_values.append(travel_minutes(participant.origin_zone, venue.zone))

    participant_count = len(participants)
    within_budget_count = sum(1 for cost in costs if cost.within_budget)
    total_cost = sum((cost.total_cost for cost in costs), Decimal("0"))
    total_budget = sum((participant.budget for participant in participants), Decimal("0"))
    average_cost = total_cost / max(participant_count, 1)
    average_budget = total_budget / max(participant_count, 1)
    all_within_budget = within_budget_count == participant_count and participant_count > 0
    score = score_venue(
        participant_count,
        within_budget_count,
        average_cost,
        average_budget,
        music_matches,
        ambience_matches,
    )
    reasons = [
        f"{within_budget_count} de {participant_count} participantes quedan dentro de presupuesto.",
        f"Costo promedio estimado: {average_cost:.0f}.",
    ]
    if music_matches:
        reasons.append("Hay coincidencias musicales con el grupo.")

    tradeoffs: list[str] = []
    if not all_within_budget:
        tradeoffs.append("Al menos una persona supera su presupuesto o entrada maxima.")
    if venue.minimum_age > 18:
        tradeoffs.append(f"Edad minima de {venue.minimum_age} anos.")
    if venue.features.get("data_quality") == "stale":
        tradeoffs.append("Los datos del lugar necesitan actualizacion.")

    category = "best_fit" if score >= 80 else "balanced" if score >= 60 else "tradeoff"
    average_travel = round(sum(travel_values) / max(participant_count, 1))
    return RecommendationEstimate(
        venue=venue,
        score=score,
        category=category,
        estimated_average_cost=average_cost,
        all_within_budget=all_within_budget,
        average_travel_minutes=average_travel,
        reasons=reasons,
        tradeoffs=tradeoffs,
        participant_costs=costs,
    )
