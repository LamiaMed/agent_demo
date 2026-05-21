import re
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

from langchain_core.tools import tool

if "langchain_google_community" not in sys.modules:
    package_dir = (
        Path(__file__).resolve().parents[1]
        / ".venv"
        / "Lib"
        / "site-packages"
        / "langchain_google_community"
    )
    package = types.ModuleType("langchain_google_community")
    package.__path__ = [str(package_dir)]  # type: ignore[attr-defined]
    sys.modules["langchain_google_community"] = package

from langchain_google_community.calendar.utils import (
    build_resouce_service as build_resource_service,
    get_google_credentials,
)

BASE_DIR = Path(__file__).resolve().parents[1]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
DEFAULT_TIMEZONE = "UTC"

# Can review scopes here: https://developers.google.com/calendar/api/auth
# For instance, readonly scope is https://www.googleapis.com/auth/calendar.readonly
credentials = get_google_credentials(
    token_file="token.json",
    scopes=["https://www.googleapis.com/auth/calendar"],
    client_secrets_file=str(CREDENTIALS_FILE),
)

api_resource = build_resource_service(credentials=credentials)


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
    details = _parse_query(query)
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
    return f"Event created: {event.get('htmlLink')}"
