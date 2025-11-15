"""
Calendar MCP Server

A FastMCP server that exposes Google Calendar tools via HTTP.
Run this server separately, and the orchestrator will connect to it.
"""

from fastmcp import FastMCP
from typing import Optional, List
from agent.mcp_servers.calender_mcp import services

# Initialize FastMCP server
mcp = FastMCP('Calendar Server')


@mcp.tool(description="List Google Calendar events in a time range with optional text search.")
def list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    query: Optional[str] = None,
) -> dict:
    """
    List calendar events with optional filters.
    
    Args:
        calendar_id: Calendar ID (default: "primary")
        time_min: Lower bound for event start time (RFC3339 format)
        time_max: Upper bound for event start time (RFC3339 format)
        max_results: Maximum number of events to return
        query: Free text search terms to find events (searches summary, description, location, attendees)
    
    Returns:
        dict: Dictionary containing list of events
    """
    try:
        items = services.list_events(
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
) -> dict:
    """
    Create a Google Calendar event.
    
    Args:
        summary: Event title/summary
        start_time: Event start time (RFC3339 format)
        end_time: Event end time (RFC3339 format)
        calendar_id: Calendar ID (default: "primary")
        timezone: Timezone for the event (default: "UTC")
        description: Event description (optional)
        attendees: List of attendee email addresses (optional)
        location: Event location (optional)
    
    Returns:
        dict: Created event information
    """
    try:
        created = services.create_event(
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
def get_event(event_id: str, calendar_id: str = "primary") -> dict:
    """
    Get a Google Calendar event by ID.
    
    Args:
        event_id: The event ID
        calendar_id: Calendar ID (default: "primary")
    
    Returns:
        dict: Event information
    """
    try:
        event = services.get_event(event_id=event_id, calendar_id=calendar_id)
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
) -> dict:
    """
    Update a Google Calendar event by ID.
    
    Args:
        event_id: The event ID
        calendar_id: Calendar ID (default: "primary")
        summary: New event title/summary (optional)
        start_time: New event start time (RFC3339 format, optional)
        end_time: New event end time (RFC3339 format, optional)
        timezone: Timezone for the event (default: "UTC")
        description: New event description (optional)
        attendees: New list of attendee email addresses (optional)
        location: New event location (optional)
    
    Returns:
        dict: Updated event information
    """
    try:
        updated = services.update_event(
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
def delete_event(event_id: str, calendar_id: str = "primary") -> dict:
    """
    Delete a Google Calendar event by ID.
    
    Args:
        event_id: The event ID
        calendar_id: Calendar ID (default: "primary")
    
    Returns:
        dict: Deletion confirmation
    """
    try:
        result = services.delete_event(event_id=event_id, calendar_id=calendar_id)
        return result
    except Exception as e:
        return {"error": f"Failed to delete event: {str(e)}"}


# Run the server when this file is executed directly
if __name__ == "__main__":
    print("Starting Calendar MCP Server on http://127.0.0.1:6282/mcp")
    mcp.run(transport="http", host="127.0.0.1", port=6282, stateless_http=True)

