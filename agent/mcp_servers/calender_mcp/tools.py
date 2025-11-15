from typing import Any, Dict, List, Optional

from agent.mcp_servers.calender_mcp import services as cal_services


class _CalendarMcpBinder:
    def __init__(self) -> None:
        self._mcp: Any = None
        self._pending: List[tuple] = []

    def bind(self, mcp: Any) -> None:
        self._mcp = mcp
        for func, kwargs in self._pending:
            mcp.tool(**kwargs)(func)
        self._pending.clear()

    def tool(self, description: Optional[str] = None) -> Any:
        def decorator(func: Any) -> Any:
            if self._mcp is not None:
                return self._mcp.tool(description=description)(func)
            self._pending.append((func, {"description": description}))
            return func

        return decorator


mcp = _CalendarMcpBinder()


@mcp.tool(description="List Google Calendar events in a time range with optional text search.")
def list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List calendar events with optional filters.
    
    Args:
        calendar_id: Calendar ID (default: "primary")
        time_min: Lower bound for event start time (RFC3339 format)
        time_max: Upper bound for event start time (RFC3339 format)
        max_results: Maximum number of events to return
        query: Free text search terms to find events (searches summary, description, location, attendees)
    """
    try:
        items = cal_services.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            query=query,
        )
        return {"events": items}
    except Exception as e:
        return {"error": f"Failed to list events: {str(e)}"}


@mcp.tool(description="Create a Google Calendar event.")
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
    try:
        created = cal_services.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            calendar_id=calendar_id,
            timezone=timezone,
            description=description,
            attendees=attendees,
            location=location,
        )
        return {"event": created}
    except Exception as e:
        return {"error": f"Failed to create event: {str(e)}"}


@mcp.tool(description="Get a Google Calendar event by ID.")
def get_event(event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
    try:
        event = cal_services.get_event(event_id=event_id, calendar_id=calendar_id)
        return {"event": event}
    except Exception as e:
        return {"error": f"Failed to get event: {str(e)}"}


@mcp.tool(description="Update a Google Calendar event by ID.")
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
    try:
        updated = cal_services.update_event(
            event_id=event_id,
            calendar_id=calendar_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            description=description,
            attendees=attendees,
            location=location,
        )
        return {"event": updated}
    except Exception as e:
        return {"error": f"Failed to update event: {str(e)}"}


@mcp.tool(description="Delete a Google Calendar event by ID.")
def delete_event(event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
    try:
        result = cal_services.delete_event(event_id=event_id, calendar_id=calendar_id)
        return result
    except Exception as e:
        return {"error": f"Failed to delete event: {str(e)}"}


