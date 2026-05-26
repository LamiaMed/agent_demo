import base64
import re
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from langchain_core.tools import tool

from langchain_google_community.calendar.utils import (
    build_calendar_service,
)
from langchain_google_community._utils import get_google_credentials

from monitor import metrics

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMEZONE = "UTC"


def _get_client_secrets_file() -> str:
    encoded_credentials = os.getenv("GOOGLE_CREDENTIALS_BASE64", "").strip()
    if not encoded_credentials:
        raise RuntimeError(
            "La variable d'environnement GOOGLE_CREDENTIALS_BASE64 n'est pas définie."
        )

    decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_file.write(decoded_credentials)
        return temp_file.name


def _get_calendar_service():
    # Can review scopes here: https://developers.google.com/calendar/api/auth
    # For instance, readonly scope is https://www.googleapis.com/auth/calendar.readonly
    credentials = get_google_credentials(
        token_file="token.json",
        scopes=["https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/gmail.send"],
        client_secrets_file=_get_client_secrets_file(),
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

    # Recherche de date numérique si aucune date textuelle
    if not target_date:
        date_match = re.search(
            r"(\d{4})[-/](\d{2})[-/](\d{2})|(\d{2})[-/](\d{2})[-/](\d{4})",
            query,
        )

        if date_match:
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
    hour, minute = 14, 0  # Valeur par défaut

    time_match = re.search(
        r"(\d{1,2})\s*(?:h|heure|heures)\s*(\d{2})?",
        query,
        flags=re.IGNORECASE,
    )

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0

    # 4. Construction des datetime
    start_dt = datetime.combine(
        target_date,
        datetime.min.time()
    ).replace(hour=hour, minute=minute)

    # Durée par défaut = 1 heure
    end_dt = start_dt + timedelta(hours=1)

    start_datetime = start_dt.isoformat() + "+02:00"
    end_datetime = end_dt.isoformat() + "+02:00"

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
        calendarId="primary",
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
