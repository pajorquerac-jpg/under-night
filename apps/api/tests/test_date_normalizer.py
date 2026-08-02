from datetime import date

from app.services.date_normalizer import normalize_event_date

REFERENCE_DATE = date(2026, 8, 1)


def test_normalizes_today() -> None:
    result = normalize_event_date(
        "hoy",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date == date(2026, 8, 1)
    assert result.needs_confirmation is False


def test_normalizes_today_with_weekday() -> None:
    result = normalize_event_date(
        "hoy sábado",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date == date(2026, 8, 1)
    assert result.needs_confirmation is False


def test_normalizes_tomorrow() -> None:
    result = normalize_event_date(
        "mañana",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date == date(2026, 8, 2)


def test_same_weekday_is_ambiguous() -> None:
    result = normalize_event_date(
        "este sábado",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date is None
    assert result.needs_confirmation is True
    assert result.clarification is not None
    assert "2026" in result.clarification


def test_normalizes_next_saturday() -> None:
    result = normalize_event_date(
        "próximo sábado",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date == date(2026, 8, 8)
    assert result.needs_confirmation is False


def test_normalizes_iso_date() -> None:
    result = normalize_event_date(
        "2026-08-08",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date == date(2026, 8, 8)


def test_invalid_expression_requires_confirmation() -> None:
    result = normalize_event_date(
        "algún día",
        reference_date=REFERENCE_DATE,
    )

    assert result.normalized_date is None
    assert result.needs_confirmation is True
