from decimal import Decimal

BASE_TRANSPORT_COSTS: dict[tuple[str, str, str], Decimal] = {
    ("Centro", "Centro", "walking"): Decimal("0"),
    ("Centro", "Centro", "public_transport"): Decimal("900"),
    ("Centro", "Norte", "public_transport"): Decimal("1200"),
    ("Centro", "Sur", "public_transport"): Decimal("1400"),
    ("Centro", "Oriente", "rideshare"): Decimal("6500"),
    ("Norte", "Centro", "public_transport"): Decimal("1200"),
    ("Norte", "Oriente", "rideshare"): Decimal("8000"),
    ("Sur", "Centro", "public_transport"): Decimal("1400"),
    ("Sur", "Oriente", "rideshare"): Decimal("9000"),
    ("Oriente", "Oriente", "car"): Decimal("2500"),
}

BASE_TRAVEL_MINUTES: dict[tuple[str, str], int] = {
    ("Centro", "Centro"): 12,
    ("Centro", "Norte"): 24,
    ("Centro", "Sur"): 28,
    ("Centro", "Oriente"): 30,
    ("Norte", "Centro"): 24,
    ("Norte", "Oriente"): 35,
    ("Sur", "Centro"): 28,
    ("Sur", "Oriente"): 40,
    ("Oriente", "Oriente"): 15,
}


def transport_cost(origin_zone: str, venue_zone: str, transport_type: str) -> Decimal:
    key = (origin_zone, venue_zone, transport_type)
    if key in BASE_TRANSPORT_COSTS:
        return BASE_TRANSPORT_COSTS[key]
    if transport_type == "walking" and origin_zone == venue_zone:
        return Decimal("0")
    if transport_type == "public_transport":
        return Decimal("1800")
    if transport_type == "car":
        return Decimal("3500")
    if transport_type == "rideshare":
        return Decimal("7500")
    return Decimal("2500")


def travel_minutes(origin_zone: str, venue_zone: str) -> int:
    return BASE_TRAVEL_MINUTES.get((origin_zone, venue_zone), 32)
