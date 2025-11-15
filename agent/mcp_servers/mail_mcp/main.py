import sys
from pathlib import Path

# Ensure project root on sys.path so `agent` imports resolve when running from this dir
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastmcp import FastMCP  # type: ignore
from agent.mcp_servers.mail_mcp import tools as mail_tools
from agent.mcp_servers.mail_mcp import services as mail_services

# Initialize Gmail service once
mail_services.initialize_mail_service()

# Create server and bind tools annotated in tools.py
mcp = FastMCP("mail-mcp")
mail_tools.mcp.bind(mcp)


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=6281, stateless_http=True)


