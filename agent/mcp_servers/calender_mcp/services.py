import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.clients.google import init_calendar_service

_SERVICE_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {"service": None}


def initialize_calendar_service(force: bool = False) -> Any:
    if _STATE["service"] is not None and not force:
        return _STATE["service"]
    with _SERVICE_LOCK:
        if _STATE["service"] is not None and not force:
            return _STATE["service"]
        _STATE["service"] = init_calendar_service(force=force)
        return _STATE["service"]


def _get_service() -> Any:
    if _STATE["service"] is None:
        return initialize_calendar_service()
    return _STATE["service"]


def _ensure_rfc3339(time_str: str) -> str:
    """
    Ensure time string is in RFC3339 format with timezone.
    Google Calendar API requires format like: 2025-11-09T00:00:00+05:30 or 2025-11-09T00:00:00Z
    """
    if not time_str:
        return time_str
    
    # If already has timezone info (ends with Z or has +/- offset), return as is
    if time_str.endswith('Z') or '+' in time_str or time_str.count('-') > 2:
        return time_str
    
    # Add Z (UTC) suffix if no timezone specified
    return time_str + 'Z'


def list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    single_events: bool = True,
    order_by: str = "startTime",
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List calendar events with optional filters.
    
    Args:
        calendar_id: Calendar ID (default: "primary")
        time_min: Lower bound for event start time (RFC3339)
        time_max: Upper bound for event start time (RFC3339)
        max_results: Maximum number of events to return
        single_events: Whether to expand recurring events
        order_by: Order of events ("startTime" or "updated")
        query: Free text search terms to find events
    """
    service = _get_service()
    params: Dict[str, Any] = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": single_events,
        "orderBy": order_by,
    }
    if time_min:
        params["timeMin"] = _ensure_rfc3339(time_min)
    if time_max:
        params["timeMax"] = _ensure_rfc3339(time_max)
    if query:
        params["q"] = query  # Google Calendar API uses 'q' for text search
    events_result = service.events().list(**params).execute()  # type: ignore[attr-defined]
    return events_result.get("items", [])


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    timezone: str = "UTC",
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
) -> Dict[str, Any]:
    service = _get_service()
    event: Dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": _ensure_rfc3339(start_time), "timeZone": timezone},
        "end": {"dateTime": _ensure_rfc3339(end_time), "timeZone": timezone},
    }
    if description:
        event["description"] = description
    if location:
        event["location"] = location
    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    created = service.events().insert(calendarId=calendar_id, body=event, sendUpdates="all").execute()  # type: ignore[attr-defined]
    return {"id": created.get("id"), "htmlLink": created.get("htmlLink")}


def get_event(event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
    service = _get_service()
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()  # type: ignore[attr-defined]
    return event


def update_event(
    event_id: str,
    calendar_id: str = "primary",
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    timezone: str = "UTC",
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
) -> Dict[str, Any]:
    service = _get_service()
    current = service.events().get(calendarId=calendar_id, eventId=event_id).execute()  # type: ignore[attr-defined]
    if summary is not None:
        current["summary"] = summary
    if description is not None:
        current["description"] = description
    if location is not None:
        current["location"] = location
    if start_time is not None:
        current["start"] = {"dateTime": _ensure_rfc3339(start_time), "timeZone": timezone}
    if end_time is not None:
        current["end"] = {"dateTime": _ensure_rfc3339(end_time), "timeZone": timezone}
    if attendees is not None:
        current["attendees"] = [{"email": e} for e in attendees]
    updated = service.events().update(calendarId=calendar_id, eventId=event_id, body=current, sendUpdates="all").execute()  # type: ignore[attr-defined]
    return updated


def delete_event(event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
    service = _get_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id, sendUpdates="all").execute()  # type: ignore[attr-defined]
    return {"deleted": True, "eventId": event_id}


