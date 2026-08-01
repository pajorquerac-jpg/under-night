from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass

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
    ConversationState,
    ExtractedConversationData,
    SuggestedAction,
)

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
    next_field = state.missing_fields[0] if state.missing_fields else None
    next_question = _collection_question(next_field) if next_field is not None else None
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
            "people_count, budget_per_person, event_date, origin_zones,",
            "meeting_point, outing_type, music_preferences, restrictions.",
            "Si un dato no aparece, usa null para escalares y [] para listas.",
            "No inventes datos.",
        ]
    )


def _reply_prompt(state: ConversationState) -> str:
    next_field = state.missing_fields[0] if state.missing_fields else None
    next_question = _collection_question(next_field) if next_field is not None else None
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
    if not state.missing_fields:
        return reply
    if _looks_like_internal_reasoning(reply):
        return _collection_question(state.missing_fields[0])
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
        if value is None:
            continue
        if isinstance(value, list):
            if value:
                data[key] = _merge_lists(data.get(key, []), value)
            continue
        data[key] = value
    return ConversationState.model_validate(data)


def _finalize_state(state: ConversationState) -> ConversationState:
    data = state.model_dump()
    missing = _missing_fields(state)
    data["missing_fields"] = missing
    data["stage"] = "ready_for_recommendations" if not missing else "collecting"
    return ConversationState.model_validate(data)


def _missing_fields(state: ConversationState) -> list[str]:
    missing: list[str] = []
    if state.people_count is None:
        missing.append("people_count")
    if state.budget_per_person is None:
        missing.append("budget_per_person")
    if state.event_date is None:
        missing.append("event_date")
    if not state.origin_zones and state.meeting_point is None:
        missing.append("origin_zones")
    if state.outing_type is None:
        missing.append("outing_type")
    if not state.music_preferences:
        missing.append("music_preferences")
    if not state.restrictions:
        missing.append("restrictions")

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
        return _collection_question(state.missing_fields[0])

    return (
        "Tengo la información base. El siguiente paso es calcular recomendaciones con el "
        "motor determinístico para cruzar presupuesto, zonas y preferencias del grupo."
    )


def _rule_extract(message: str) -> ExtractedConversationData:
    text = message.lower()
    return ExtractedConversationData(
        budget_per_person=_extract_budget(text),
        event_date=_extract_date(text),
        meeting_point=_extract_meeting_point(message),
        music_preferences=_extract_music(text),
        origin_zones=_extract_origins(message),
        outing_type=_extract_outing_type(text),
        people_count=_extract_people_count(text),
        restrictions=_extract_restrictions(text),
    )


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
    actions = [
        SuggestedAction(
            label="Iniciar salida",
            type="navigate",
            payload={"route": "/plans/create"},
        ),
    ]
    if state.stage == "ready_for_recommendations":
        actions.append(
            SuggestedAction(
                label="Calcular recomendaciones",
                type="submit",
                payload={"conversation_id": conversation_id},
            )
        )
    if payload.plan_id is not None or context.recommendations:
        actions.append(
            SuggestedAction(
                label="Ver recomendaciones",
                type="navigate",
                payload={"route": "/recommendations", "plan_id": payload.plan_id},
            )
        )
    return actions


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
    return None


def _extract_budget(text: str) -> int | None:
    match = re.search(r"\b(\d+)\s*(?:mil|k)\b", text)
    if match is not None:
        return int(match.group(1)) * 1000
    match = re.search(r"\b(\d{1,3}(?:[.,]\d{3})+)\b", text)
    if match is not None:
        return int(match.group(1).replace(".", "").replace(",", ""))
    return None


def _extract_date(text: str) -> str | None:
    explicit = re.search(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}\b", text)
    if explicit is not None:
        return explicit.group(0)
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
    known = [
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
    normalized = message.lower()
    return [zone for zone in known if zone.lower() in normalized]


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
    return [tag for tag in tags if tag in text]


def _extract_restrictions(text: str) -> list[str]:
    if "sin restricciones" in text:
        return ["sin restricciones"]
    restrictions = []
    if "sin fumar" in text:
        restrictions.append("sin fumar")
    if "evitar" in text:
        restrictions.append("lugares a evitar")
    if "edad" in text:
        restrictions.append("restricción de edad")
    return restrictions


def _merge_lists(existing: object, incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for value in [*(existing if isinstance(existing, list) else []), *incoming]:
        if value not in merged:
            merged.append(value)
    return merged


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
