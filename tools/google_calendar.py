import base64
import json
import re
import os
import unicodedata
from functools import lru_cache
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from langchain_core.tools import tool

from langchain_google_community.calendar.utils import (
    build_calendar_service,
)

from monitor import metrics

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMEZONE = "Europe/Paris"
PARIS_TZ = ZoneInfo(DEFAULT_TIMEZONE)
DEFAULT_DURATION_MINUTES = 30


def _get_service_account_info() -> dict:
    encoded_credentials = os.getenv("GOOGLE_CREDENTIALS_BASE64", "").strip()
    if not encoded_credentials:
        raise RuntimeError(
            "La variable d'environnement GOOGLE_CREDENTIALS_BASE64 n'est pas définie."
        )

    decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
    return json.loads(decoded_credentials)


def _get_calendar_service():
    creds = _get_service_account_info()
    credentials = service_account.Credentials.from_service_account_info(
        creds,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    return build_calendar_service(credentials=credentials)


def _get_reference_date() -> date:
    """Renvoie la date du jour. 
    Utile pour l'application et indispensable pour la figer (monkeypatch) pendant les tests.
    """
    return date.today()


def _resolve_date(query: str, reference_date: date) -> date | None:
    """Analyse le texte pour trouver une date relative."""

    query = query.lower()

    # Cas simples
    if "aujourd'hui" in query:
        return reference_date

    if "demain" in query:
        return reference_date + timedelta(days=1)

    # Mapping des jours FR -> weekday Python
    weekdays = {
        "lundi": 0,
        "mardi": 1,
        "mercredi": 2,
        "jeudi": 3,
        "vendredi": 4,
        "samedi": 5,
        "dimanche": 6,
    }

    for day_name, target_weekday in weekdays.items():

        # Exemple : "lundi prochain"
        if f"{day_name} prochain" in query:

            current_weekday = reference_date.weekday()

            days_ahead = target_weekday - current_weekday

            # Si le jour est déjà passé ou aujourd'hui
            if days_ahead <= 0:
                days_ahead += 7

            return reference_date + timedelta(days=days_ahead)

        # Exemple : "lundi"
        elif re.search(rf"\b{day_name}\b", query):

            current_weekday = reference_date.weekday()

            days_ahead = target_weekday - current_weekday

            if days_ahead < 0:
                days_ahead += 7

            return reference_date + timedelta(days=days_ahead)

    return None


def _extract_time(query: str) -> tuple[int, int]:
    patterns = [
        r"(?:\bà\b|\ba\b|\bde\b|\bvers\b)\s*(\d{1,2})(?:\s*(?:h|:)\s*(\d{2})|\s*h\b|\s*heures?\b)?",
        r"\b(\d{1,2})\s*h\s*(\d{2})?\b",
        r"\b(\d{1,2}):(\d{2})\b",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, query, flags=re.IGNORECASE):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.lastindex and match.group(2) else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return hour, minute

    raise ValueError("Impossible de trouver l'heure dans la requête.")


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


@lru_cache(maxsize=1)
def _load_duration_rules() -> list[dict[str, object]]:
    durations_file = BASE_DIR / "data" / "duree.txt"
    if not durations_file.exists():
        return []

    entries: list[dict[str, object]] = []
    pattern = re.compile(
        r'"(?P<code>[^"]+)"\s*=\s*\{\s*name\s*=\s*"(?P<name>[^"]+)"\s*,\s*duration\s*=\s*(?P<duration>\d+)\s*\}',
        flags=re.IGNORECASE,
    )

    for line in durations_file.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if not match:
            continue

        entries.append(
            {
                "code": match.group("code").strip(),
                "name": match.group("name").strip(),
                "duration": int(match.group("duration")),
            }
        )

    return entries


def _extract_duration_minutes(query: str) -> int | None:
    duration_match = re.search(
        r"(?:durée|duration)\s*(?:de\s*)?(\d+)\s*(?:minutes?|mins?|mn|min)\b",
        query,
        flags=re.IGNORECASE,
    )
    if duration_match:
        return int(duration_match.group(1))

    duration_match = re.search(
        r"(?:durée|duration)\s*(?:de\s*)?(\d+)\s*(?:heures?|hrs?|h)\b",
        query,
        flags=re.IGNORECASE,
    )
    if duration_match:
        return int(duration_match.group(1)) * 60

    return None


def _infer_act_duration(query: str) -> int:
    normalized_query = _normalize_text(query)
    default_duration = DEFAULT_DURATION_MINUTES

    for entry in _load_duration_rules():
        code = str(entry["code"])
        name = str(entry["name"])
        duration = int(entry["duration"])

        if code.upper() == "DEFAULT":
            default_duration = duration
            continue

        normalized_name = _normalize_text(name)
        if _normalize_text(code) in normalized_query or normalized_name in normalized_query:
            return duration

    return default_duration


def _extract_time_range(query: str) -> tuple[int, int, int | None, int | None]:
    range_patterns = [
        r"(?:\bde\b|\bentre\b)?\s*(\d{1,2})(?:\s*(?:h|:)\s*(\d{2})|\s*h\b|\s*heures?\b)?\s*(?:à|au|-)\s*(\d{1,2})(?:\s*(?:h|:)\s*(\d{2})|\s*h\b|\s*heures?\b)?",
        r"(\d{1,2})\s*h\s*(\d{2})?\s*(?:à|au|-)\s*(\d{1,2})\s*h\s*(\d{2})?",
        r"(\d{1,2}):(\d{2})\s*(?:à|au|-)\s*(\d{1,2}):(\d{2})",
    ]

    for pattern in range_patterns:
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if not match:
            continue

        start_hour = int(match.group(1))
        start_minute = int(match.group(2)) if match.group(2) else 0
        end_hour = int(match.group(3))
        end_minute = int(match.group(4)) if match.lastindex and match.lastindex >= 4 and match.group(4) else 0

        if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
            continue
        if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
            continue

        return start_hour, start_minute, end_hour, end_minute

    hour, minute = _extract_time(query)
    return hour, minute, None, None

def _parse_query(query: str) -> dict:
    # 1. Extraction du titre
    summary_match = re.search(
        r'(?:titre|title)\s*[":-]?\s*["“”]?(.+?)(?:"|["“”]|[.,;]|$)',
        query,
        flags=re.IGNORECASE,
    )

    summary = summary_match.group(1).strip() if summary_match else query.strip()

    # 2. Résolution de la date
    ref_date = _get_reference_date()
    target_date = _resolve_date(query, ref_date)
    date_text = None

    # Recherche de date numérique si aucune date textuelle
    if not target_date:
        date_match = re.search(
            r"(\d{4})[-/](\d{2})[-/](\d{2})|(\d{2})[-/](\d{2})[-/](\d{4})",
            query,
        )

        if date_match:
            date_text = date_match.group(0)
            raw_date = date_match.group(0)

            # Format AAAA-MM-JJ ou AAAA/MM/JJ
            if date_match.group(1):
                raw_date = raw_date.replace("/", "-")
                target_date = date.fromisoformat(raw_date)

            # Format JJ-MM-AAAA ou JJ/MM/AAAA
            else:
                for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
                    try:
                        target_date = datetime.strptime(raw_date, fmt).date()
                        break
                    except ValueError:
                        pass

    if not target_date:
        raise ValueError("Impossible de trouver la date dans la requête.")

    # 3. Extraction de l'heure
    time_source = query.replace(date_text, " ") if date_text else query
    hour, minute, end_hour, end_minute = _extract_time_range(time_source)

    # 4. Construction des datetime
    start_dt = datetime.combine(
        target_date,
        datetime.min.time()
    ).replace(hour=hour, minute=minute, tzinfo=PARIS_TZ)

    if end_hour is not None:
        end_dt = datetime.combine(
            target_date,
            datetime.min.time()
        ).replace(hour=end_hour, minute=end_minute or 0, tzinfo=PARIS_TZ)
    else:
        duration_minutes = _extract_duration_minutes(query)
        if duration_minutes is None:
            duration_minutes = _infer_act_duration(query)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

    start_datetime = start_dt.isoformat()
    end_datetime = end_dt.isoformat()

    return {
        "summary": summary,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    }

@tool
def create_event(query: str) -> str:
    """Create a calendar event from a natural-language query."""
    # if os.environ.get("VERCEL"):
    #     raise RuntimeError(
    #         "Google Calendar tool is not enabled in the Vercel runtime."
    #     )

    details = _parse_query(query)
    api_resource = _get_calendar_service()
    event = api_resource.events().insert(
        calendarId="medjahed.lamia4@gmail.com",
        body={
            "summary": details["summary"],
            "start": {
                "dateTime": details["start_datetime"],
                "timeZone": DEFAULT_TIMEZONE,
            },
            "end": {
                "dateTime": details["end_datetime"],
                "timeZone": DEFAULT_TIMEZONE,
            },
        },
    ).execute()
    metrics["nbr_rdv"] += 1
    return f"Event created: {event.get('htmlLink')}"
