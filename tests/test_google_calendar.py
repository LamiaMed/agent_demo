from datetime import date, datetime
from tools.google_calendar import _parse_query, _resolve_date



def test_resolve_date_handles_french_relative_weekday():
    reference_date = date(2026, 5, 26)

    resolved = _resolve_date("donne moi un rendez vous vendredi prochain", reference_date)

    assert resolved == date(2026, 5, 29)


def test_resolve_date_handles_tomorrow():
    reference_date = date(2026, 5, 26)

    resolved = _resolve_date("donne moi un rendez vous demain", reference_date)

    assert resolved == date(2026, 5, 27)


def test_parse_query_uses_europe_paris_timezone_for_relative_dates(monkeypatch):
    # On patche la fonction locale de résolution de date pour figer le comportement pendant le test
    monkeypatch.setattr("tests.test_google_calendar._resolve_date", lambda q, ref: date(2026, 5, 29))

    details = _parse_query("Titre: Consultation, vendredi prochain à 14h00")

    start_dt = datetime.fromisoformat(details["start_datetime"])

    assert start_dt.date() == date(2026, 5, 29)
    assert start_dt.hour == 14
    assert start_dt.minute == 0
    # En mai, la France est en heure d'été (UTC+2), soit 2 * 3600 secondes
    assert start_dt.utcoffset().total_seconds() == 2 * 3600


def test_parse_query_keeps_explicit_dates():
    details = _parse_query("Titre: Consultation, Date: 2026-05-28, Heure: 14h00")

    start_dt = datetime.fromisoformat(details["start_datetime"])

    assert start_dt.date() == date(2026, 5, 28)
    assert start_dt.hour == 14
    assert start_dt.minute == 0