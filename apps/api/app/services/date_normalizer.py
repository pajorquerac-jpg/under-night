from dataclasses import dataclass
from datetime import date, timedelta
import re
import unicodedata


@dataclass(frozen=True)
class DateNormalizationResult:
    normalized_date: date | None
    needs_confirmation: bool
    clarification: str | None = None


WEEKDAYS = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6,
}

WEEKDAY_LABELS = {
    "lunes": "lunes",
    "martes": "martes",
    "miercoles": "miércoles",
    "jueves": "jueves",
    "viernes": "viernes",
    "sabado": "sábado",
    "domingo": "domingo",
}


def _normalize_text(value: str) -> str:
    value = value.strip().lower()

    normalized = unicodedata.normalize("NFD", value)
    without_accents = "".join(
        char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    return " ".join(without_accents.split())


def _next_weekday(
    reference_date: date,
    weekday: int,
    *,
    include_today: bool,
) -> date:
    days_ahead = (weekday - reference_date.weekday()) % 7

    if days_ahead == 0 and not include_today:
        days_ahead = 7

    return reference_date + timedelta(days=days_ahead)


def normalize_event_date(
    raw_value: str,
    *,
    reference_date: date,
) -> DateNormalizationResult:
    value = _normalize_text(raw_value)

    if value in {"hoy", "esta noche"}:
        return DateNormalizationResult(
            normalized_date=reference_date,
            needs_confirmation=False,
        )

    if value == "manana":
        return DateNormalizationResult(
            normalized_date=reference_date + timedelta(days=1),
            needs_confirmation=False,
        )

    if value == "pasado manana":
        return DateNormalizationResult(
            normalized_date=reference_date + timedelta(days=2),
            needs_confirmation=False,
        )

    iso_match = re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)

    if iso_match:
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            return DateNormalizationResult(
                normalized_date=None,
                needs_confirmation=True,
                clarification="La fecha indicada no es válida.",
            )

        return DateNormalizationResult(
            normalized_date=parsed,
            needs_confirmation=False,
        )

    for weekday_name, weekday_number in WEEKDAYS.items():
        if value in {
            weekday_name,
            f"el {weekday_name}",
            f"este {weekday_name}",
        }:
            candidate_today = _next_weekday(
                reference_date,
                weekday_number,
                include_today=True,
            )

            candidate_next = _next_weekday(
                reference_date,
                weekday_number,
                include_today=False,
            )

            if candidate_today == reference_date:
                weekday_label = WEEKDAY_LABELS.get(weekday_name, weekday_name)
                return DateNormalizationResult(
                    normalized_date=None,
                    needs_confirmation=True,
                    clarification=(
                        f"¿Te refieres a hoy "
                        f"{weekday_label} "
                        f"{candidate_today.strftime('%d-%m-%Y')} "
                        f"o al próximo {weekday_label} "
                        f"{candidate_next.strftime('%d-%m-%Y')}?"
                    ),
                )

            return DateNormalizationResult(
                normalized_date=candidate_today,
                needs_confirmation=False,
            )

        if value in {
            f"proximo {weekday_name}",
            f"el proximo {weekday_name}",
        }:
            return DateNormalizationResult(
                normalized_date=_next_weekday(
                    reference_date,
                    weekday_number,
                    include_today=False,
                ),
                needs_confirmation=False,
            )

    return DateNormalizationResult(
        normalized_date=None,
        needs_confirmation=True,
        clarification=(
            "No pude determinar la fecha exacta. "
            "Indícala, por ejemplo, como 2026-08-08."
        ),
    )