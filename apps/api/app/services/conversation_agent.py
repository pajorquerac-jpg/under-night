from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import ConversationMessage
from app.models.recommendation import Recommendation
from app.repositories.conversations import (
    add_message,
    get_or_create_conversation,
    list_messages,
    update_conversation_state,
)
from app.repositories.recommendations import list_for_plan
from app.schemas.conversation import (
    AgentChatRequest,
    AgentChatResponse,
    ChatMessage,
    ConversationParticipant,
    ConversationState,
    ExtractedConversationData,
    SuggestedAction,
)
from app.services.date_normalizer import normalize_event_date

logger = logging.getLogger(__name__)


class OllamaInvalidResponseError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentContext:
    recommendations: list[Recommendation]


@dataclass(frozen=True)
class LlmResult:
    provider: str
    model: str | None
    reply: str
    used_fallback: bool


async def answer_chat(db: Session, payload: AgentChatRequest) -> AgentChatResponse:
    conversation = get_or_create_conversation(db, payload.conversation_id)
    add_message(db, conversation.id, "user", payload.message)
    persisted_messages = list_messages(db, conversation.id)
    previous_messages = persisted_messages[:-1]
    request_history = [*payload.history, *_messages_to_chat_history(previous_messages)]
    reply_history = [*request_history, ChatMessage(role="user", content=payload.message)]
    current_state = ConversationState.model_validate(conversation.state or {})
    context = AgentContext(
        recommendations=list_for_plan(db, payload.plan_id) if payload.plan_id is not None else [],
    )

    extracted = await _extract_data(payload, request_history)
    extracted = _override_restrictions_from_message(extracted, payload.message)
    merged_state = _merge_state(current_state, extracted)
    updated_state = _finalize_state(merged_state)
    update_conversation_state(
        db,
        conversation,
        updated_state.model_dump(mode="json"),
        updated_state.stage,
    )

    actions = _suggested_actions(conversation.id, payload, context, updated_state)
    llm_result = await _assistant_reply(payload, reply_history, updated_state, context)
    add_message(
        db,
        conversation.id,
        "assistant",
        llm_result.reply,
        provider=llm_result.provider,
        model=llm_result.model,
    )

    return AgentChatResponse(
        conversation_id=conversation.id,
        model=llm_result.model,
        provider=llm_result.provider,
        reply=llm_result.reply,
        state=updated_state,
        suggested_actions=actions,
        used_fallback=llm_result.used_fallback,
    )


async def _extract_data(
    payload: AgentChatRequest,
    history: list[ChatMessage],
) -> ExtractedConversationData:
    if payload.use_llm and settings.llm_provider == "ollama":
        started_at = time.perf_counter()
        logger.info(
            "agent.extract_attempt provider=ollama model=%s message_chars=%s",
            settings.ollama_model,
            len(payload.message),
        )
        try:
            extracted = await _ask_ollama_for_extraction(payload, history)
            extracted = _override_date_extraction_from_message(extracted, payload.message)
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            logger.info(
                "agent.extract_success provider=ollama model=%s duration_ms=%s",
                settings.ollama_model,
                duration_ms,
            )
            return extracted
        except httpx.TimeoutException as exc:
            _log_llm_error("extract_timeout", exc, started_at)
        except httpx.HTTPStatusError as exc:
            _log_llm_error("extract_http_status", exc, started_at)
        except httpx.RequestError as exc:
            _log_llm_error("extract_request_error", exc, started_at)
        except OllamaInvalidResponseError as exc:
            _log_llm_error("extract_invalid_response", exc, started_at)

    return _rule_extract(payload.message)


async def _assistant_reply(
    payload: AgentChatRequest,
    history: list[ChatMessage],
    state: ConversationState,
    context: AgentContext,
) -> LlmResult:
    if payload.use_llm and settings.llm_provider == "ollama":
        started_at = time.perf_counter()
        logger.info(
            "agent.reply_attempt provider=ollama model=%s message_chars=%s",
            settings.ollama_model,
            len(payload.message),
        )
        try:
            reply = await _ask_ollama_for_reply(history, state)
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            logger.info(
                "agent.reply_success provider=ollama model=%s duration_ms=%s fallback=false",
                settings.ollama_model,
                duration_ms,
            )
            return LlmResult(
                model=settings.ollama_model,
                provider="ollama",
                reply=reply,
                used_fallback=False,
            )
        except httpx.TimeoutException as exc:
            _log_llm_error("reply_timeout", exc, started_at)
        except httpx.HTTPStatusError as exc:
            _log_llm_error("reply_http_status", exc, started_at)
        except httpx.RequestError as exc:
            _log_llm_error("reply_request_error", exc, started_at)
        except OllamaInvalidResponseError as exc:
            _log_llm_error("reply_invalid_response", exc, started_at)
    else:
        logger.info(
            "agent.llm_skipped provider=%s use_llm=%s fallback=true",
            settings.llm_provider,
            payload.use_llm,
        )

    return LlmResult(
        model=None,
        provider="rules",
        reply=_fallback_reply(payload, context, state),
        used_fallback=True,
    )


async def _ask_ollama_for_extraction(
    payload: AgentChatRequest,
    history: list[ChatMessage],
) -> ExtractedConversationData:
    messages = [
        {"role": "system", "content": _extraction_prompt()},
        *[_message_to_ollama(message) for message in history[-10:]],
        {"role": "user", "content": payload.message},
    ]
    response = await _post_ollama(
        messages,
        options={"num_predict": 160, "temperature": 0},
        response_format="json",
    )
    content = _extract_ollama_reply(response)
    return _parse_extracted_data(content)


async def _ask_ollama_for_reply(
    history: list[ChatMessage],
    state: ConversationState,
) -> str:
    next_question = _next_question(state)
    messages = [
        {"role": "system", "content": _reply_prompt(state)},
        *[_message_to_ollama(message) for message in history[-10:]],
        {
            "role": "user",
            "content": "\n".join(
                [
                    "/no_think",
                    "Escribe solamente la respuesta final para el usuario.",
                    "No expliques tu razonamiento.",
                    f"Respuesta esperada: {next_question}",
                ]
            ),
        },
    ]
    response = await _post_ollama(
        messages,
        options={"num_predict": 90, "temperature": 0.2},
    )
    return _guard_conversational_reply(_extract_ollama_reply(response), state)


async def _post_ollama(
    messages: list[dict[str, str]],
    options: dict[str, int | float] | None = None,
    response_format: str | None = None,
) -> httpx.Response:
    request_body = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "think": False,
    }
    if options is not None:
        request_body["options"] = options
    if response_format is not None:
        request_body["format"] = response_format

    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json=request_body,
        )
        response.raise_for_status()
        return response


def _extract_ollama_reply(response: httpx.Response) -> str:
    try:
        body = response.json()
        content = body["message"]["content"]
    except (KeyError, TypeError, ValueError) as exc:
        raise OllamaInvalidResponseError(
            "Ollama response does not contain message content"
        ) from exc

    if not isinstance(content, str):
        raise OllamaInvalidResponseError("Ollama message content is not text")

    cleaned = _strip_thinking(content).strip()
    if not cleaned:
        raise OllamaInvalidResponseError("Ollama returned an empty message")
    return cleaned


def _parse_extracted_data(content: str) -> ExtractedConversationData:
    try:
        raw = _json_object_from_text(content)
        return ExtractedConversationData.model_validate(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise OllamaInvalidResponseError("Ollama extraction is not valid JSON") from exc


def _json_object_from_text(content: str) -> dict[str, object]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match is None:
        raise ValueError("No JSON object found")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("JSON payload is not an object")
    return parsed


def _message_to_ollama(message: ChatMessage) -> dict[str, str]:
    return {"role": message.role, "content": message.content}


def _messages_to_chat_history(messages: list[ConversationMessage]) -> list[ChatMessage]:
    return [
        ChatMessage(role=message.role, content=message.content)
        for message in messages
        if message.role in ("user", "assistant")
    ]


def _extraction_prompt() -> str:
    return "\n".join(
        [
            "Extrae datos estructurados para UnderNight.",
            "Responde sólo JSON válido, sin markdown y sin explicación.",
            "Usa estas claves exactas:",
            "people_count, budget_per_person, participants, event_date, event_date_text,",
            "event_date_needs_confirmation, origin_zones, meeting_point,",
            "outing_type, music_preferences, restrictions, restrictions_confirmed.",
            "participants debe ser una lista de objetos con name, budget y origin_zone.",
            "Para fechas:",
            "- Copia la expresión temporal del usuario en event_date_text.",
            "- No conviertas expresiones relativas a fecha ISO.",
            "- No inventes anio, mes ni dia.",
            "- El backend resolvera la fecha.",
            "Ejemplos:",
            "Usuario: Queremos salir este sabado -> event_date_text: este sabado",
            "Usuario: El 8 de agosto -> event_date_text: 8 de agosto",
            "Usuario: Todavia no sabemos -> event_date_text: null",
            "Si un dato no aparece, usa null para escalares y [] para listas.",
            "No inventes datos.",
        ]
    )


def _reply_prompt(state: ConversationState) -> str:
    next_question = _next_question(state)
    return "\n".join(
        [
            "/no_think",
            "Eres el agente conversacional de UnderNight.",
            "Tu tarea es recopilar datos para preparar una salida nocturna grupal.",
            "Responde sólo con el texto final para el usuario.",
            "No escribas razonamiento, análisis, pasos ni explicación interna.",
            "Responde siempre en español.",
            "Usa máximo dos frases cortas.",
            "Haz una sola pregunta principal.",
            "No recomiendes lugares, venues, precios ni rankings.",
            f"Pregunta principal que debes hacer: {next_question}",
            "Si la pregunta principal es None, confirma que ya tienes la información base.",
        ]
    )


def _guard_conversational_reply(reply: str, state: ConversationState) -> str:
    if _looks_like_internal_reasoning(reply):
        if not state.missing_fields:
            return (
                "Perfecto, ya tengo la información base. "
                "Cuando quieras, calculamos recomendaciones."
            )
        return _next_question(state) or _collection_question(state.missing_fields[0])

    if not state.missing_fields:
        return reply
    return reply


def _looks_like_internal_reasoning(reply: str) -> bool:
    normalized = reply.lower()
    internal_markers = (
        "the user",
        "the system",
        "i need to",
        "missing_fields",
        "respuesta esperada",
        "razonamiento",
    )
    return any(marker in normalized for marker in internal_markers)


def _merge_state(
    current: ConversationState,
    extracted: ExtractedConversationData,
) -> ConversationState:
    data = current.model_dump()
    for key, value in extracted.model_dump().items():
        if key == "restrictions_confirmed" and value is None:
            value = current.restrictions_confirmed
        if key == "restrictions" and isinstance(value, dict):
            value = value.get("restrictions", [])
            if "restrictions_confirmed" in value:
                value = value.get("restrictions_confirmed", False)
        if key == "event_date_text" and isinstance(value, str):
            result = normalize_event_date(
                value, reference_date=_today()
            )
            data["event_date"] = result.normalized_date
            data["event_date_needs_confirmation"] = result.needs_confirmation
        if value is None:
            continue
        if key == "participants" and isinstance(value, list):
            if value:
                data[key] = _merge_participants(data.get(key, []), value)
            continue
        if isinstance(value, list):
            if value:
                data[key] = _merge_lists(data.get(key, []), value)
            continue
        data[key] = value

    if data.get("event_date") is not None:
        data["event_date_needs_confirmation"] = False

    return ConversationState.model_validate(data)


def _finalize_state(state: ConversationState) -> ConversationState:
    data = state.model_dump()
    if state.participants and (
        state.people_count is None or len(state.participants) > state.people_count
    ):
        data["people_count"] = len(state.participants)
        state = ConversationState.model_validate(data)

    missing = _missing_fields(state)
    data["missing_fields"] = missing
    data["stage"] = "ready_for_recommendations" if not missing else "collecting"
    return ConversationState.model_validate(data)


def _missing_fields(state: ConversationState) -> list[str]:
    missing: list[str] = []
    if state.people_count is None:
        missing.append("people_count")
    if state.budget_per_person is None and not _has_participant_budgets(state):
        missing.append("budget_per_person")
    if state.event_date is None:
        missing.append("event_date")
    if (
        not state.origin_zones
        and state.meeting_point is None
        and not _has_participant_origins(state)
    ):
        missing.append("origin_zones")
    if state.outing_type is None:
        missing.append("outing_type")
    if not state.music_preferences:
        missing.append("music_preferences")
    if not state.restrictions_confirmed:
        missing.append("restrictions")

    if state.event_date_needs_confirmation and "event_date" in missing:
        return ["event_date", *[field for field in missing if field != "event_date"]]

    if (
        "origin_zones" in missing
        and "people_count" not in missing
        and "budget_per_person" not in missing
        and "outing_type" not in missing
    ):
        return ["origin_zones", *[field for field in missing if field != "origin_zones"]]
    return missing


def _fallback_reply(
    payload: AgentChatRequest,
    context: AgentContext,
    state: ConversationState,
) -> str:
    if context.recommendations and _asks_for_recommendations(payload.message):
        return _recommendations_reply(context.recommendations)

    if state.missing_fields:
        return _next_question(state) or _collection_question(state.missing_fields[0])

    

    return (
        "Tengo la información base. El siguiente paso es calcular recomendaciones con el "
        "motor determinístico para cruzar presupuesto, zonas y preferencias del grupo."
    )


def _rule_extract(message: str) -> ExtractedConversationData:
    text = message.lower()
    restrictions, restrictions_confirmed = _extract_restrictions(text)
    event_date = _extract_date(text)
    event_date_text = _extract_date_text(text)
    participants = _extract_participants(message)
    participant_budgets = [
        participant.budget for participant in participants if participant.budget is not None
    ]

    event_date_needs_confirmation = False
    if event_date_text is not None:
        normalized = normalize_event_date(event_date_text, reference_date=_today())
        event_date = event_date or normalized.normalized_date
        event_date_needs_confirmation = normalized.needs_confirmation

    budget_per_person = (
        min(participant_budgets) if participant_budgets else _extract_budget(text)
    )

    return ExtractedConversationData(
        budget_per_person=budget_per_person,
        event_date=event_date,
        event_date_text=event_date_text,
        event_date_needs_confirmation=event_date_needs_confirmation,
        meeting_point=_extract_meeting_point(message),
        music_preferences=_extract_music(text),
        origin_zones=_extract_origins(message),
        outing_type=_extract_outing_type(text),
        participants=participants,
        people_count=_extract_people_count(text) or (len(participants) if participants else None),
        restrictions=restrictions,
        restrictions_confirmed=restrictions_confirmed,
    )


def _override_date_extraction_from_message(
    extracted: ExtractedConversationData,
    message: str,
) -> ExtractedConversationData:
    text = message.lower()
    event_date_text = _extract_date_text(text)
    event_date = _extract_date(text)

    if event_date_text is None and event_date is None:
        return extracted

    updates: dict[str, object] = {}
    if event_date_text is not None:
        normalized = normalize_event_date(event_date_text, reference_date=_today())
        updates["event_date_text"] = event_date_text
        updates["event_date_needs_confirmation"] = normalized.needs_confirmation
        if normalized.normalized_date is not None:
            updates["event_date"] = normalized.normalized_date
    if event_date is not None:
        updates["event_date"] = event_date
        updates["event_date_needs_confirmation"] = False

    return extracted.model_copy(update=updates)


def _override_restrictions_from_message(
    extracted: ExtractedConversationData,
    message: str,
) -> ExtractedConversationData:
    restrictions, restrictions_confirmed = extract_restrictions_confirmation(message)
    updates: dict[str, object] = {}

    if restrictions is not None:
        updates["restrictions"] = restrictions
    if restrictions_confirmed is not None:
        updates["restrictions_confirmed"] = restrictions_confirmed

    if not updates:
        return extracted
    return extracted.model_copy(update=updates)


def _collection_question(field: str) -> str:
    questions = {
        "people_count": "¿Cuántas personas son en total para la salida?",
        "budget_per_person": "¿Qué presupuesto aproximado tiene cada persona?",
        "event_date": "¿Para qué día o fecha están pensando salir?",
        "origin_zones": "¿Desde qué comunas sale cada persona, o se juntan todos en un punto?",
        "outing_type": "¿Qué tipo de panorama quieren: bar, bailar, stand up, terraza u otro?",
        "music_preferences": "¿Qué música prefieren para la noche?",
        "restrictions": (
            "¿Hay alguna restricción importante, como edad, horarios o lugares a evitar?"
        ),
    }
    return questions[field]


def _next_question(state: ConversationState) -> str | None:
    if not state.missing_fields:
        return None

    next_field = state.missing_fields[0]
    if next_field == "event_date" and state.event_date_needs_confirmation and state.event_date_text:
        result = normalize_event_date(state.event_date_text, reference_date=_today())
        if result.clarification:
            return result.clarification

    return _collection_question(next_field)


def extract_restrictions_confirmation(message: str) -> tuple[list[str] | None, bool | None]:
    normalized = message.strip().lower()

    no_restrictions_phrases = {
        "no",
        "ninguna",
        "ninguno",
        "no tenemos restricciones",
        "no hay restricciones",
        "ninguna restricción",
        "nada especial",
        "sin restricciones",
    }

    if normalized in no_restrictions_phrases:
        return [], True

    if any(phrase in normalized for phrase in no_restrictions_phrases if " " in phrase):
        return [], True

    place_restriction = _extract_place_restriction(normalized)
    if place_restriction is not None:
        return [place_restriction], True

    return None, None


def _extract_place_restriction(text: str) -> str | None:
    if not re.search(r"\b(?:solo|s[oó]lo|unicamente|únicamente|solamente)\b", text):
        return None

    zone_match = re.search(
        r"\b(?:sector|zona|lugares?\s+(?:del|de la)\s+(?:sector|zona)?)\s+"
        r"(oriente|centro|norte|sur|providencia|santiago|ñuñoa|nunoa|las condes|recoleta)\b",
        text,
    )
    if zone_match is None:
        zone_match = re.search(
            r"\b(oriente|centro|norte|sur|providencia|santiago|ñuñoa|nunoa|las condes|recoleta)\b",
            text,
        )
    if zone_match is None:
        return None

    zone = zone_match.group(1).replace("nunoa", "ñuñoa")
    return f"solo lugares en {zone}"

def _recommendations_reply(recommendations: list[Recommendation]) -> str:
    top = recommendations[:3]
    if not top:
        return "Todavía no hay recomendaciones calculadas para este plan."
    lines = ["Estas son las mejores opciones calculadas para la noche:"]
    for index, recommendation in enumerate(top, start=1):
        venue = recommendation.venue
        lines.append(
            f"{index}. {venue.name}: {recommendation.score:.0f}% de compatibilidad, "
            f"zona {venue.zone}, costo promedio {_money(recommendation.estimated_average_cost)}."
        )
    return "\n".join(lines)


def _suggested_actions(
    conversation_id: str,
    payload: AgentChatRequest,
    context: AgentContext,
    state: ConversationState,
) -> list[SuggestedAction]:
    suggested_actions: list[SuggestedAction] = []
    if state.stage == "ready_for_recommendations":
        suggested_actions.append(
            SuggestedAction(
                label="Ver recomendaciones",
                type="submit",
                payload={"conversation_id": conversation_id},
            )
        )
    if payload.plan_id is not None or context.recommendations:
        suggested_actions.append(
            SuggestedAction(
                label="Ver recomendaciones",
                type="navigate",
                payload={"route": "/recommendations", "plan_id": payload.plan_id},
            )
        )
    return suggested_actions


def _log_llm_error(error_type: str, exc: Exception, started_at: float) -> None:
    duration_ms = round((time.perf_counter() - started_at) * 1000)
    logger.warning(
        "agent.llm_error provider=ollama model=%s duration_ms=%s error_type=%s "
        "exception_class=%s fallback_may_be_used=true",
        settings.ollama_model,
        duration_ms,
        error_type,
        exc.__class__.__name__,
    )


def _asks_for_recommendations(message: str) -> bool:
    normalized = message.lower()
    return any(word in normalized for word in ("recom", "lugar", "opción", "opcion", "ranking"))


def _today() -> date:
    try:
        return datetime.now(ZoneInfo(settings.app_timezone)).date()
    except ZoneInfoNotFoundError:
        return date.today()


def _has_participant_budgets(state: ConversationState) -> bool:
    if state.people_count is None:
        return False
    budget_count = sum(1 for participant in state.participants if participant.budget is not None)
    return budget_count >= state.people_count


def _has_participant_origins(state: ConversationState) -> bool:
    if state.people_count is None:
        return False
    origin_count = sum(
        1 for participant in state.participants if participant.origin_zone is not None
    )
    return origin_count >= state.people_count


def _extract_people_count(text: str) -> int | None:
    words = {
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
    }
    for word, value in words.items():
        if word in text:
            return value
    match = re.search(
        r"\b(?:somos|son|vamos|personas?)\s+(\d{1,2})\b",
        text,
    )
    if match is not None:
        return int(match.group(1))
    match = re.search(r"\b(\d{1,2})\s+personas?\b", text)
    if match is not None:
        return int(match.group(1))

    names_match = re.search(
        r"\bsomos\s+(.+?)(?:\.|,?\s+(?:tenemos|queremos|salimos|vamos|el|la)\b|$)",
        text,
    )
    if names_match is not None:
        names_text = names_match.group(1)
        names = [
            name.strip()
            for name in re.split(r"\s+y\s+|,", names_text)
            if name.strip()
        ]
        if len(names) >= 2:
            return len(names)
    return None


def _extract_participants(message: str) -> list[ConversationParticipant]:
    text = message.lower()
    names = _extract_group_names(message)
    by_name: dict[str, ConversationParticipant] = {
        _participant_key(name): ConversationParticipant(name=name) for name in names
    }

    for name, budget in _extract_named_budgets(message):
        key = _participant_key(name)
        current = by_name.get(key, ConversationParticipant(name=name))
        by_name[key] = current.model_copy(update={"budget": budget})

    for name, origin_zone in _extract_named_origins(message):
        key = _participant_key(name)
        current = by_name.get(key, ConversationParticipant(name=name))
        by_name[key] = current.model_copy(update={"origin_zone": origin_zone})

    if by_name:
        return list(by_name.values())

    people_count = _extract_people_count(text)
    budget_values = _extract_budget_values(text)
    if people_count is None or len(budget_values) < people_count:
        return []

    return [
        ConversationParticipant(name=f"Amigo {index + 1}", budget=budget)
        for index, budget in enumerate(budget_values[:people_count])
    ]


def _extract_group_names(message: str) -> list[str]:
    match = re.search(
        r"\bsomos\s+(.+?)(?:\.|,?\s+(?:tenemos|queremos|salimos|vamos|el|la)\b|$)",
        message,
        flags=re.I,
    )
    if match is None:
        return []

    names_text = match.group(1)
    if re.search(r"\b\d+\s+(?:amigos|personas)\b", names_text, flags=re.I):
        return []

    return [
        name.strip()
        for name in re.split(r"\s+y\s+|,", names_text)
        if name.strip()
    ]


def _extract_named_budgets(message: str) -> list[tuple[str, int]]:
    explicit_budgets = [
        (match.group("name").strip(), _money_text_to_int(match.group("amount")))
        for match in re.finditer(
            r"\b(?P<name>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚáéíóúÑñ]+)\s+"
            r"(?:tiene|tienen|cuenta\s+con|lleva)\s+"
            r"(?P<amount>\d{1,3}(?:[.,]\d{3})+|\d{4,6}|\d+\s*(?:mil|k))\b",
            message,
        )
    ]
    shorthand_budgets = [
        (match.group("name").strip(), _money_text_to_int(match.group("amount")))
        for match in re.finditer(
            r"(?:,|\by\b)\s*(?P<name>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚáéíóúÑñ]+)\s+"
            r"(?P<amount>\d{1,3}(?:[.,]\d{3})+|\d{4,6}|\d+\s*(?:mil|k))\b",
            message,
        )
    ]
    return [*explicit_budgets, *shorthand_budgets]


def _extract_named_origins(message: str) -> list[tuple[str, str]]:
    known = _known_zones()
    zone_pattern = "|".join(re.escape(zone) for zone in known)
    explicit_origins = [
        (match.group("name").strip(), _canonical_zone(match.group("zone")))
        for match in re.finditer(
            rf"\b(?P<name>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚáéíóúÑñ]+)\s+"
            rf"(?:sale|salen|viene|vienen)\s+de\s+(?P<zone>{zone_pattern})\b",
            message,
            flags=re.I,
        )
    ]
    shorthand_origins = [
        (match.group("name").strip(), _canonical_zone(match.group("zone")))
        for match in re.finditer(
            rf"(?:,|\by\b)\s*(?P<name>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚáéíóúÑñ]+)\s+"
            rf"de\s+(?P<zone>{zone_pattern})\b",
            message,
            flags=re.I,
        )
    ]
    return [*explicit_origins, *shorthand_origins]


def _participant_key(name: str | None) -> str:
    if not name:
        return ""
    return name.strip().lower()


def _extract_budget(text: str) -> int | None:
    values = _extract_budget_values(text)
    if values:
        return min(values)
    return None


def _extract_budget_values(text: str) -> list[int]:
    values = [int(match) * 1000 for match in re.findall(r"\b(\d+)\s*(?:mil|k)\b", text)]
    values.extend(
        int(match.replace(".", "").replace(",", ""))
        for match in re.findall(r"\b(\d{1,3}(?:[.,]\d{3})+)\b", text)
    )
    values.extend(
        int(match)
        for match in re.findall(
            r"\b(?:presupuestos?\s+(?:son|es)|tiene|tienen|con|para)\s+(\d{4,6})\b",
            text,
        )
    )
    return values


def _money_text_to_int(value: str) -> int:
    normalized = value.lower().strip()
    match = re.fullmatch(r"(\d+)\s*(?:mil|k)", normalized)
    if match is not None:
        return int(match.group(1)) * 1000
    return int(normalized.replace(".", "").replace(",", ""))


def _extract_date(text: str) -> date | None:
    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso_match is None:
        return None
    try:
        return date.fromisoformat(iso_match.group(0))
    except ValueError:
        return None


def _extract_date_text(text: str) -> str | None:
    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso_match is not None:
        return iso_match.group(0)

    weekday_phrase_match = re.search(
        r"\b(?:hoy|este|proximo|próximo|el\s+proximo|el\s+próximo|el\s+este)\s+"
        r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[áa]bado|domingo)\b",
        text,
    )
    if weekday_phrase_match is not None:
        return weekday_phrase_match.group(0)

    day_month_match = re.search(r"\b\d{1,2}\s+de\s+[a-záéíóúñ]+\b", text)
    if day_month_match is not None:
        return day_month_match.group(0)

    day_slash_month_match = re.search(r"\b\d{1,2}/\d{1,2}\b", text)
    if day_slash_month_match is not None:
        return day_slash_month_match.group(0)

    for word in (
        "hoy",
        "mañana",
        "viernes",
        "sábado",
        "sabado",
        "domingo",
        "lunes",
        "martes",
        "miércoles",
        "miercoles",
        "jueves",
    ):
        if word in text:
            return word
    return None


def _extract_origins(message: str) -> list[str]:
    normalized = message.lower()
    return [zone for zone in _known_zones() if zone.lower() in normalized]


def _known_zones() -> list[str]:
    return [
        "Centro",
        "Oriente",
        "Norte",
        "Sur",
        "Providencia",
        "Santiago",
        "Ñuñoa",
        "Las Condes",
        "Recoleta",
    ]


def _canonical_zone(value: str) -> str:
    normalized = value.lower()
    for zone in _known_zones():
        if zone.lower() == normalized:
            return zone
    return value.strip()


def _extract_meeting_point(message: str) -> str | None:
    match = re.search(r"(?:juntamos|reunimos|encuentro) en ([\w\sñÑ]+)", message, re.I)
    if match is None:
        return None
    return match.group(1).strip()


def _extract_outing_type(text: str) -> str | None:
    for word in ("bar", "bailar", "stand up", "terraza", "club", "discoteca", "karaoke"):
        if word in text:
            return word
    if "bail" in text:
        return "bailar"
    return None


def _extract_music(text: str) -> list[str]:
    tags = ["reggaeton", "pop", "house", "techno", "rock", "indie", "latin"]
    music = [tag for tag in tags if tag in text]
    if "reggaetón" in text and "reggaeton" not in music:
        music.append("reggaeton")
    if re.search(r"\btech\b", text) and "techno" not in music:
        music.append("techno")
    if not music and re.search(r"\b(?:buena\s+m[uú]sica|m[uú]sica\s+variada)\b", text):
        music.append("pop")
    return music


def _extract_restrictions(text: str) -> tuple[list[str], bool | None]:
    if "sin restricciones" in text or "no hay restricciones" in text:
        return [], True

    restrictions: list[str] = []
    if "sin fumar" in text:
        restrictions.append("sin fumar")
    if "evitar" in text:
        restrictions.append("lugares a evitar")
    if "edad" in text:
        restrictions.append("restricción de edad")

    if restrictions:
        return restrictions, True
    return [], None


def _merge_lists(existing: object, incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for value in [*(existing if isinstance(existing, list) else []), *incoming]:
        if value not in merged:
            merged.append(value)
    return merged


def _merge_participants(existing: object, incoming: list[object]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    anonymous_index = 0

    for participant in [
        *(existing if isinstance(existing, list) else []),
        *incoming,
    ]:
        parsed = ConversationParticipant.model_validate(participant)
        payload = parsed.model_dump(exclude_none=True)
        key = _participant_key(parsed.name)
        if not key:
            key = f"__anonymous_{anonymous_index}"
            anonymous_index += 1
        merged[key] = {**merged.get(key, {}), **payload}

    return list(merged.values())


def _money(value: object) -> str:
    return f"${int(value):,}".replace(",", ".")


def _strip_thinking(content: str) -> str:
    without_blocks = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if "</think>" in without_blocks.lower():
        return re.split(r"</think>", without_blocks, flags=re.IGNORECASE)[-1]
    return without_blocks
