from datetime import UTC, date, datetime, time

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession
from app.repositories.participants import create_participant
from app.repositories.plans import create_plan
from app.schemas.night_out import FriendQuestionnaire, NightOutQuestionnaire
from app.schemas.participant import ParticipantCreate
from app.schemas.plan import PlanCreate
from app.schemas.recommendation import RecommendationRead
from app.services.recommendations import generate_recommendations

router = APIRouter()


@router.post(
    "/recommendations",
    response_model=list[RecommendationRead],
    status_code=status.HTTP_201_CREATED,
)
def create_from_questionnaire(
    payload: NightOutQuestionnaire,
    db: DbSession,
) -> list[RecommendationRead]:
    if payload.friend_count != len(payload.friends):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="friend_count must match friends length",
        )

    plan = create_plan(
        db,
        PlanCreate(
            decision_deadline=datetime.now(UTC),
            event_date=date.today(),
            name=payload.plan_name,
            plan_type=", ".join(friend.outing_type for friend in payload.friends),
            preferred_zone=payload.preferred_zone,
            start_time=time(22, 0),
        ),
    )

    for friend in payload.friends:
        create_participant(db, plan.id, _participant_from_friend(friend, payload))

    return generate_recommendations(db, plan.id)


def _participant_from_friend(
    friend: FriendQuestionnaire,
    payload: NightOutQuestionnaire,
) -> ParticipantCreate:
    origin_zone = (
        payload.preferred_zone if payload.group_mode == "together" else friend.origin_zone
    )
    return ParticipantCreate(
        budget=friend.budget,
        consumption_level=friend.consumption_level,
        max_entry_price=friend.max_entry_price,
        max_return_time=time(3, 0),
        name=friend.name,
        origin_zone=origin_zone,
        preferences=_tags_from_outing_type(friend.outing_type),
        restrictions={},
        transport_type=friend.transport_type,
    )


def _tags_from_outing_type(value: str) -> dict[str, list[str]]:
    normalized = value.lower()
    ambience: set[str] = set()
    music: set[str] = set()

    if "bail" in normalized:
        ambience.add("baile")
    if "bar" in normalized:
        ambience.add("bar")
    if "stand" in normalized:
        ambience.add("conversado")
    if "terraza" in normalized:
        ambience.add("terraza")
    if "reggaeton" in normalized:
        music.add("reggaeton")
    if "house" in normalized or "electro" in normalized:
        music.add("house")
    if "pop" in normalized:
        music.add("pop")
    if "indie" in normalized:
        music.add("indie")
    if not ambience:
        ambience.add("casual")
    if not music:
        music.add("pop")

    return {
        "ambience_tags": sorted(ambience),
        "music_tags": sorted(music),
    }
