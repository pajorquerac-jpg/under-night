from decimal import Decimal


def score_venue(
    participant_count: int,
    within_budget_count: int,
    average_cost: Decimal,
    average_budget: Decimal,
    music_matches: int,
    ambience_matches: int,
) -> float:
    if participant_count == 0:
        return 0
    budget_ratio = within_budget_count / participant_count
    affordability = max(0.0, 1.0 - float(average_cost / max(average_budget, Decimal("1"))))
    preference_bonus = min((music_matches * 4) + (ambience_matches * 2), 16)
    return round(min(100, (budget_ratio * 65) + (affordability * 19) + preference_bonus), 2)
