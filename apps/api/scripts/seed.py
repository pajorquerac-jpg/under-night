from datetime import UTC, date, datetime, time
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.venue import Venue

VENUES = [
    {
        "name": "Patio Lunar",
        "zone": "Centro",
        "entry_price": Decimal("0"),
        "average_drink_price": Decimal("6500"),
        "music_tags": ["indie", "pop"],
        "ambience_tags": ["conversado", "terraza"],
        "features": {"tradeoff": "sin entrada, consumo alto"},
    },
    {
        "name": "Bajo Voltaje",
        "zone": "Centro",
        "entry_price": Decimal("12000"),
        "average_drink_price": Decimal("4000"),
        "music_tags": ["electro", "house"],
        "ambience_tags": ["baile", "intenso"],
        "features": {"tradeoff": "entrada alta, buena musica"},
    },
    {
        "name": "Club Anden",
        "zone": "Sur",
        "entry_price": Decimal("3000"),
        "average_drink_price": Decimal("3000"),
        "music_tags": ["reggaeton", "pop"],
        "ambience_tags": ["baile", "casual"],
        "features": {"tradeoff": "economico, lejano"},
    },
    {
        "name": "Azotea Cero",
        "zone": "Centro",
        "entry_price": Decimal("5000"),
        "average_drink_price": Decimal("4500"),
        "music_tags": ["funk", "soul"],
        "ambience_tags": ["conversado", "vista"],
        "features": {"tradeoff": "cercano, menos orientado a bailar"},
    },
    {
        "name": "Niebla Room",
        "zone": "Oriente",
        "entry_price": Decimal("18000"),
        "average_drink_price": Decimal("8000"),
        "music_tags": ["house", "techno"],
        "ambience_tags": ["premium", "baile"],
        "features": {"tradeoff": "premium"},
    },
    {
        "name": "Estacion Alba",
        "zone": "Norte",
        "entry_price": Decimal("4000"),
        "average_drink_price": Decimal("3500"),
        "music_tags": ["latin", "pop"],
        "ambience_tags": ["casual", "temprano"],
        "features": {"tradeoff": "cierre temprano"},
        "closing_time": time(1, 0),
    },
    {
        "name": "Clave 23",
        "zone": "Oriente",
        "entry_price": Decimal("10000"),
        "average_drink_price": Decimal("6000"),
        "music_tags": ["jazz", "funk"],
        "ambience_tags": ["adulto", "cocktail"],
        "features": {"tradeoff": "edad minima mas alta"},
        "minimum_age": 23,
    },
    {
        "name": "Ritmo Archivo",
        "zone": "Centro",
        "entry_price": Decimal("6000"),
        "average_drink_price": Decimal("3800"),
        "music_tags": ["rock", "indie"],
        "ambience_tags": ["bar", "casual"],
        "features": {"tradeoff": "datos menos recientes", "data_quality": "stale"},
        "data_updated_at": datetime(2025, 11, 12, tzinfo=UTC),
    },
    {
        "name": "Terraza Modo",
        "zone": "Norte",
        "entry_price": Decimal("7000"),
        "average_drink_price": Decimal("4200"),
        "music_tags": ["pop", "latin"],
        "ambience_tags": ["terraza", "baile"],
        "features": {"tradeoff": "balanceado"},
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        if not db.query(Venue).first():
            for index, data in enumerate(VENUES):
                db.add(
                    Venue(
                        latitude=-33.45 + index / 100,
                        longitude=-70.66 - index / 100,
                        opening_time=data.get("opening_time", time(20, 0)),
                        closing_time=data.get("closing_time", time(4, 0)),
                        minimum_age=data.get("minimum_age", 18),
                        data_updated_at=data.get(
                            "data_updated_at",
                            datetime.now(UTC),
                        ),
                        ambience_tags=data["ambience_tags"],
                        average_drink_price=data["average_drink_price"],
                        entry_price=data["entry_price"],
                        features=data["features"],
                        music_tags=data["music_tags"],
                        name=data["name"],
                        zone=data["zone"],
                    )
                )

        if not db.query(Plan).filter(Plan.name == "Cumple de demo").first():
            plan = Plan(
                name="Cumple de demo",
                event_date=date.today(),
                start_time=time(22, 0),
                decision_deadline=datetime.now(UTC),
                preferred_zone="Centro",
                plan_type="bar y baile",
                status="draft",
            )
            db.add(plan)
            db.flush()
            participants = [
                ("Antonia", "Centro", "walking", "medium", "28000", "7000", ["pop", "indie"]),
                ("Benjamin", "Norte", "public_transport", "low", "18000", "5000", ["latin", "pop"]),
                (
                    "Camila",
                    "Sur",
                    "public_transport",
                    "medium",
                    "22000",
                    "8000",
                    ["reggaeton", "house"],
                ),
                ("Diego", "Oriente", "rideshare", "high", "40000", "15000", ["house", "techno"]),
            ]
            for name, zone, transport, level, budget, max_entry, music in participants:
                db.add(
                    Participant(
                        plan_id=plan.id,
                        name=name,
                        budget=Decimal(budget),
                        max_entry_price=Decimal(max_entry),
                        origin_zone=zone,
                        transport_type=transport,
                        consumption_level=level,
                        max_return_time=time(3, 0),
                        preferences={"music_tags": music, "ambience_tags": ["baile"]},
                        restrictions={},
                    )
                )
        db.commit()
        print("Seed data loaded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
