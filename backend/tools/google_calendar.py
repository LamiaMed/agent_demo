import base64
import json
import re
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from langchain_core.tools import tool

from langchain_google_community.calendar.utils import (
    build_calendar_service,
)
from langchain_google_community._utils import get_google_credentials

from backend.monitor import metrics
from google.oauth2 import service_account

BASE_DIR = Path(__file__).resolve().parents[2]
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


def _parse_query(query: str) -> dict:
    summary_match = re.search(
        r'(?:titre|title)\s*[":-]?\s*["“”]?(.+?)(?:"|["“”]|[.,;]|$)',
        query,
        flags=re.IGNORECASE,
    )
    summary = summary_match.group(1).strip() if summary_match else query.strip()

    date_match = re.search(
        r"(\d{4})[-/](\d{2})[-/](\d{2})|(\d{2})[-/](\d{2})[-/](\d{4})",
        query,
    )
    if not date_match:
        raise ValueError("Impossible de trouver la date dans la requête.")
    if date_match.group(1):
        year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
    else:
        day, month, year = date_match.group(4), date_match.group(5), date_match.group(6)

    time_match = re.search(r"(\d{1,2})[:h](\d{2})", query, flags=re.IGNORECASE)
    if not time_match:
        time_match = re.search(r"\bà\s*(\d{1,2})\b", query, flags=re.IGNORECASE)
        minute = 0
        if not time_match:
            raise ValueError("Impossible de trouver l'heure dans la requête.")
        hour = int(time_match.group(1))
    else:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

    duration_match = re.search(
        r"(?:durée|duration)\s*(?:de\s*)?(\d+)\s*(?:minutes?|mins?|mn|min)\b",
        query,
        flags=re.IGNORECASE,
    )
    duration_minutes = int(duration_match.group(1)) if duration_match else 30

    start_dt = datetime.strptime(
        f"{year}-{month}-{day} {hour:02d}:{minute:02d}:00",
        "%Y-%m-%d %H:%M:%S",
    )
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    return {
        "summary": summary,
        "start_datetime": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_datetime": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
