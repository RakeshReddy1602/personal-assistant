import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastmcp import FastMCP
from agent.mcp_servers.calender_mcp import tools as call_tools
from agent.mcp_servers.calender_mcp import services as cal_services

cal_services.initialize_calendar_service()

mcp = FastMCP("calendar-mcp")
call_tools.mcp.bind(mcp)


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=6282, stateless_http=True)


