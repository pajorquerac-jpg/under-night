from datetime import UTC, date, datetime, time

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessage
from app.schemas.conversation import ConversationState
from app.services.conversation_agent import _missing_fields


def create_plan(client: TestClient) -> int:
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "Viernes de prueba",
            "event_date": date.today().isoformat(),
            "start_time": time(22, 0).isoformat(),
            "decision_deadline": datetime.now(UTC).isoformat(),
            "preferred_zone": "Centro",
            "plan_type": "bar",
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def add_participant(client: TestClient, plan_id: int, budget: str = "20000") -> int:
    response = client.post(
        f"/api/v1/plans/{plan_id}/participants",
        json={
            "name": "Paz",
            "budget": budget,
            "max_entry_price": "8000",
            "origin_zone": "Centro",
            "transport_type": "walking",
            "consumption_level": "medium",
            "preferences": {"music_tags": ["pop"], "ambience_tags": ["baile"]},
            "restrictions": {},
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_plan(client: TestClient) -> None:
    plan_id = create_plan(client)
    response = client.get(f"/api/v1/plans/{plan_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Viernes de prueba"


def test_create_participant(client: TestClient) -> None:
    plan_id = create_plan(client)
    participant_id = add_participant(client, plan_id)
    response = client.get(f"/api/v1/plans/{plan_id}/participants")
    assert response.status_code == 200
    assert response.json()[0]["id"] == participant_id


def test_list_venues(client: TestClient) -> None:
    response = client.get("/api/v1/venues")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_generate_recommendations(client: TestClient) -> None:
    plan_id = create_plan(client)
    add_participant(client, plan_id)
    response = client.post(f"/api/v1/plans/{plan_id}/recommendations")
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) == 2
    assert recommendations[0]["score"] >= recommendations[1]["score"]


def test_recommendations_include_participant_details(client: TestClient) -> None:
    plan_id = create_plan(client)
    participant_id = add_participant(client, plan_id, budget="12000")

    response = client.post(f"/api/v1/plans/{plan_id}/recommendations")

    assert response.status_code == 200
    cost = response.json()[0]["participant_costs"][0]
    assert cost["participant_id"] == participant_id
    assert cost["participant"]["name"] == "Paz"
    assert cost["participant"]["budget"] == "12000.00"


def test_night_out_recommendations_deduplicates_long_plan_type(client: TestClient) -> None:
    friends = [
        {
            "budget": "20000",
            "consumption_level": "medium",
            "max_entry_price": "10000",
            "name": f"Amigo {index + 1}",
            "origin_zone": "Centro",
            "outing_type": "bailar reggaeton, reggaeton",
            "transport_type": "rideshare",
        }
        for index in range(8)
    ]

    response = client.post(
        "/api/v1/night-out/recommendations",
        json={
            "friend_count": len(friends),
            "friends": friends,
            "group_mode": "together",
            "plan_name": "Salida UnderNight",
            "preferred_zone": "Oriente",
        },
    )

    assert response.status_code == 201
    assert len(response.json()) == 2


def test_night_out_recommendations_keep_three_named_participants(client: TestClient) -> None:
    response = client.post(
        "/api/v1/night-out/recommendations",
        json={
            "friend_count": 3,
            "friends": [
                {
                    "budget": "8000",
                    "consumption_level": "medium",
                    "max_entry_price": "10000",
                    "name": "Pablo",
                    "origin_zone": "Ñuñoa",
                    "outing_type": "bar, pop",
                    "transport_type": "rideshare",
                },
                {
                    "budget": "10000",
                    "consumption_level": "medium",
                    "max_entry_price": "10000",
                    "name": "Isabel",
                    "origin_zone": "Las Condes",
                    "outing_type": "bar, pop",
                    "transport_type": "rideshare",
                },
                {
                    "budget": "15000",
                    "consumption_level": "medium",
                    "max_entry_price": "10000",
                    "name": "Jaime",
                    "origin_zone": "Providencia",
                    "outing_type": "bar, pop",
                    "transport_type": "rideshare",
                },
            ],
            "group_mode": "individual",
            "plan_name": "Salida UnderNight",
            "preferred_zone": "Centro",
        },
    )

    assert response.status_code == 201
    names = {
        cost["participant"]["name"]
        for cost in response.json()[0]["participant_costs"]
    }
    assert names == {"Pablo", "Isabel", "Jaime"}


def test_over_budget_venue_is_penalized(client: TestClient) -> None:
    plan_id = create_plan(client)
    add_participant(client, plan_id, budget="12000")
    response = client.post(f"/api/v1/plans/{plan_id}/recommendations")
    assert response.status_code == 200
    premium = next(item for item in response.json() if item["venue"]["name"] == "Premium Oriente")
    economy = next(item for item in response.json() if item["venue"]["name"] == "Economico Centro")
    assert premium["all_within_budget"] is False
    assert premium["score"] < economy["score"]


def test_empty_confirmed_restrictions_are_not_missing() -> None:
    state = ConversationState(
        people_count=4,
        budget_per_person=25000,
        event_date="2026-08-08",
        origin_zones=["Ñuñoa", "Providencia"],
        outing_type="bailar",
        music_preferences=["electrónica", "pop"],
        restrictions=[],
        restrictions_confirmed=True,
    )

    missing = _missing_fields(state)

    assert "restrictions" not in missing

def test_unconfirmed_restrictions_are_missing() -> None:
    state = ConversationState(
        people_count=4,
        budget_per_person=25000,
        event_date="2026-08-08",
        origin_zones=["Ñuñoa"],
        outing_type="bailar",
        music_preferences=["electrónica"],
        restrictions=[],
        restrictions_confirmed=False,
    )

    missing = _missing_fields(state)

    assert "restrictions" in missing


def test_agent_confirms_no_restrictions(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos cuatro, tenemos 25 mil pesos cada uno, queremos bailar, "
                "salimos desde Centro, es el viernes, música pop y sin restricciones"
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["restrictions"] == []
    assert body["state"]["restrictions_confirmed"] is True
    assert response.json()["state"]["restrictions"] == []
    assert response.json()["state"]["restrictions_confirmed"] is True
    assert "restrictions" not in response.json()["state"]["missing_fields"]


def test_agent_confirms_place_restriction(client: TestClient) -> None:
    first = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos tres, tenemos 20 mil pesos cada uno, queremos bailar, "
                "salimos desde Centro, es el viernes y música reggaeton"
            ),
            "use_llm": False,
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["state"]["missing_fields"] == ["restrictions"]

    second = client.post(
        "/api/v1/agent/chat",
        json={
            "conversation_id": first_body["conversation_id"],
            "message": "Queremos solo lugares del sector oriente",
            "use_llm": False,
        },
    )

    assert second.status_code == 200
    body = second.json()
    assert body["state"]["restrictions"] == ["solo lugares en oriente"]
    assert body["state"]["restrictions_confirmed"] is True
    assert "restrictions" not in body["state"]["missing_fields"]
    assert body["state"]["stage"] == "ready_for_recommendations"


def test_agent_extracts_named_group_and_tech_music(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos Pablo, Denisse y Martina. Pablo tiene 20 mil y Denisse y "
                "Martina tienen 25 mil. Queremos salir a bailar Tech. Pablo sale "
                "de Ñuñoa, Denisse de Las Condes y Martina de Providencia. "
                "Queremos salir el próximo viernes."
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["people_count"] == 3
    assert body["state"]["budget_per_person"] == 20000
    assert body["state"]["music_preferences"] == ["techno"]
    assert body["state"]["origin_zones"] == ["Providencia", "Ñuñoa", "Las Condes"]
    assert body["state"]["outing_type"] == "bailar"
    assert body["state"]["missing_fields"] == ["restrictions"]


def test_agent_extracts_generic_good_music_and_lowest_budget(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos 3 amigos, uno tiene 20 mil y el resto tiene 15 mil. "
                "Queremos ir a un bar de buena música. Cada un sale desde Providencia"
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["people_count"] == 3
    assert body["state"]["budget_per_person"] == 15000
    assert body["state"]["music_preferences"] == ["pop"]
    assert body["state"]["origin_zones"] == ["Providencia"]
    assert body["state"]["outing_type"] == "bar"
    assert body["state"]["missing_fields"] == ["event_date", "restrictions"]


def test_agent_normalizes_today_with_weekday(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.conversation_agent._today", lambda: date(2026, 8, 1))

    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos 3 amigos, los presupuestos son 20mil, 15 mil y 30 mil. "
                "Queremos ir a un bar de buena música. Todos salimos desde Providencia. "
                "Para hoy sábado."
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["event_date"] == "2026-08-01"
    assert body["state"]["missing_fields"] == ["restrictions"]


def test_agent_extracts_plain_numeric_named_budgets(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.conversation_agent._today", lambda: date(2026, 8, 1))

    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Hola, somos 3 amigos. Pablo tiene 8000, Isabel tiene 10000 "
                "y Jaime tiene 15000 para salir hoy sábado"
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["people_count"] == 3
    assert body["state"]["budget_per_person"] == 8000
    assert body["state"]["event_date"] == "2026-08-01"
    assert body["state"]["participants"] == [
        {"name": "Pablo", "budget": 8000, "origin_zone": None},
        {"name": "Isabel", "budget": 10000, "origin_zone": None},
        {"name": "Jaime", "budget": 15000, "origin_zone": None},
    ]
    assert "budget_per_person" not in body["state"]["missing_fields"]


def test_agent_extracts_named_participant_budgets_and_origins(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.conversation_agent._today", lambda: date(2026, 8, 1))

    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos Pablo, Isabel y Jaime. Pablo tiene 8000, Isabel 10000 "
                "y Jaime 15000. Pablo sale de Ñuñoa, Isabel de Las Condes "
                "y Jaime de Providencia. Queremos ir a un bar con reggaetón "
                "hoy sábado y sin restricciones."
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["people_count"] == 3
    assert body["state"]["budget_per_person"] == 8000
    assert body["state"]["participants"] == [
        {"name": "Pablo", "budget": 8000, "origin_zone": "Ñuñoa"},
        {"name": "Isabel", "budget": 10000, "origin_zone": "Las Condes"},
        {"name": "Jaime", "budget": 15000, "origin_zone": "Providencia"},
    ]
    assert body["state"]["missing_fields"] == []
    assert body["state"]["stage"] == "ready_for_recommendations"


def test_agent_updates_people_count_when_more_participants_are_named(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.conversation_agent._today", lambda: date(2026, 8, 1))

    first = client.post(
        "/api/v1/agent/chat",
        json={"message": "Somos 2 amigos", "use_llm": False},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/agent/chat",
        json={
            "conversation_id": first.json()["conversation_id"],
            "message": (
                "Pablo tiene 8000, Isabel tiene 10000 y Jaime tiene 15000. "
                "Queremos bar con música variada hoy sábado y sin restricciones."
            ),
            "use_llm": False,
        },
    )

    assert second.status_code == 200
    body = second.json()
    assert body["state"]["people_count"] == 3
    assert [participant["name"] for participant in body["state"]["participants"]] == [
        "Pablo",
        "Isabel",
        "Jaime",
    ]


class FakeOllamaResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class FakeOllamaClient:
    payload: dict[str, object] = {
        "message": {"content": "¿Desde qué comunas sale cada persona?"}
    }
    error: Exception | None = None

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "FakeOllamaClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, object]) -> FakeOllamaResponse:
        if self.error is not None:
            raise self.error
        return FakeOllamaResponse(self.payload)


def use_fake_ollama(
    monkeypatch: pytest.MonkeyPatch,
    *,
    payload: dict[str, object] | None = None,
    error: Exception | None = None,
) -> None:
    FakeOllamaClient.payload = payload or {
        "message": {"content": "¿Desde qué comunas sale cada persona?"}
    }
    FakeOllamaClient.error = error
    monkeypatch.setattr("app.services.conversation_agent.httpx.AsyncClient", FakeOllamaClient)


def test_agent_chat_uses_ollama_success(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_fake_ollama(
        monkeypatch,
        payload={
            "message": {
                "content": (
                    "internal reasoning that must not leak</think>\n\n"
                    "¿Desde qué comunas sale cada persona?"
                )
            }
        },
    )

    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar",
            "conversation": [],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "ollama"
    assert body["model"] == "qwen3:4b"
    assert body["used_fallback"] is False
    assert "comunas" in body["reply"]
    assert "internal reasoning" not in body["reply"]
    assert "</think>" not in body["reply"]
    assert body["state"]["people_count"] == 4
    assert body["state"]["budget_per_person"] == 25000
    assert body["state"]["outing_type"] == "bailar"
    assert body["state"]["missing_fields"][0] == "origin_zones"


def test_agent_chat_ollama_timeout_uses_fallback(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_fake_ollama(monkeypatch, error=httpx.TimeoutException("timeout"))

    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "rules"
    assert body["model"] is None
    assert body["used_fallback"] is True
    assert "comunas" in body["reply"]


def test_agent_chat_ollama_unavailable_uses_fallback(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_fake_ollama(monkeypatch, error=httpx.ConnectError("unavailable"))

    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "rules"
    assert body["used_fallback"] is True
    assert "comunas" in body["reply"]


def test_agent_chat_incomplete_message_collects_data_without_venues(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar",
            "use_llm": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "rules"
    assert body["used_fallback"] is True
    assert "comunas" in body["reply"]
    assert "Economico Centro" not in body["reply"]
    assert "Premium Oriente" not in body["reply"]
    assert body["suggested_actions"] == []


def test_agent_chat_guards_internal_reasoning_from_ollama(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_fake_ollama(
        monkeypatch,
        payload={
            "message": {
                "content": (
                    "Okay, the user gave people, budget and type. "
                    "I need to ask for missing_fields now."
                )
            }
        },
    )

    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar",
            "conversation": [],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "ollama"
    assert body["used_fallback"] is False
    assert body["reply"] == "¿Desde qué comunas sale cada persona, o se juntan todos en un punto?"


def test_agent_chat_continues_conversation_state_and_persists_messages(
    client: TestClient,
    db: Session,
) -> None:
    first = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar",
            "use_llm": False,
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    conversation_id = first_body["conversation_id"]
    assert first_body["state"]["people_count"] == 4
    assert first_body["state"]["budget_per_person"] == 25000
    assert first_body["state"]["missing_fields"][0] == "origin_zones"

    second = client.post(
        "/api/v1/agent/chat",
        json={
            "conversation_id": conversation_id,
            "message": "Salimos desde Providencia y Ñuñoa",
            "use_llm": False,
        },
    )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["conversation_id"] == conversation_id
    assert second_body["state"]["people_count"] == 4
    assert second_body["state"]["budget_per_person"] == 25000
    assert second_body["state"]["origin_zones"] == ["Providencia", "Ñuñoa"]

    messages = db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.id)
    ).all()
    assert [message.role for message in messages] == ["user", "assistant", "user", "assistant"]


def test_agent_chat_invalid_ollama_response_uses_fallback(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_fake_ollama(monkeypatch, payload={"done": True})

    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "Somos cuatro, tenemos 25 mil pesos cada uno y queremos bailar"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "rules"
    assert body["used_fallback"] is True
    assert "comunas" in body["reply"]


def test_agent_fallback_formatting_is_readable(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": (
                "Somos cuatro, tenemos 25 mil pesos cada uno, queremos bailar, "
                "salimos desde Centro, es el viernes, música pop y sin restricciones"
            ),
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "Sinun" not in reply
    assert "1." not in reply
    assert "  " not in reply


def test_agent_chat_uses_plan_recommendation_context(client: TestClient) -> None:
    plan_id = create_plan(client)
    add_participant(client, plan_id)
    client.post(f"/api/v1/plans/{plan_id}/recommendations")

    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "Resume las mejores opciones", "plan_id": plan_id, "use_llm": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert "compatibilidad" in body["reply"]
    assert "Economico Centro" in body["reply"]
    assert any(action["label"] == "Ver recomendaciones" for action in body["suggested_actions"])
