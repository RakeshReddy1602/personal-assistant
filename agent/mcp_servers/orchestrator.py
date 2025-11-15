from fastmcp import Client as MCPClient
from contextlib import AsyncExitStack
from typing import Optional, Dict, List, Any
import json


class MCPOrchestrator:
    """
    Lightweight MCP connection pool for sub-agents.
    
    Instead of being a central controller, this acts as a shared connection pool
    that allows multiple sub-agents to reuse established MCP server connections.
    
    Benefits:
    - Single connection per MCP server (shared across all sub-agents)
    - Automatic lifecycle management (connect once, use everywhere)
    - Centralized error handling for connection issues
    - Easy to add new servers without modifying sub-agents
    
    Each sub-agent remains independent and only accesses the servers it needs.
    """

    def __init__(
        self,
        mail_url: Optional[str] = None,
        calendar_url: Optional[str] = None,
        expense_tracker_url: Optional[str] = None
    ) -> None:
        # URLs for external MCP servers
        self.mail_url = mail_url or "http://127.0.0.1:6281/mcp"
        self.calendar_url = calendar_url or "http://127.0.0.1:6282/mcp"
        self.expense_tracker_url = expense_tracker_url or "http://127.0.0.1:6280/mcp"
        
        # MCP clients for external servers
        self._clients: Dict[str, MCPClient] = {}
        self._stack: Optional[AsyncExitStack] = None
        
        print("MCP Orchestrator initialized")

    async def __aenter__(self) -> "MCPOrchestrator":
        """Initialize MCP clients for all external servers. Fails if any server is unavailable."""
        print("Starting MCP Orchestrator initialization...")
        
        # Initialize async context stack for MCP clients
        self._stack = AsyncExitStack()
        
        errors = []
        
        # Connect to Mail MCP server
        try:
            print(f"Connecting to Mail MCP at {self.mail_url}...")
            mail_client = MCPClient(self.mail_url)
            await self._stack.enter_async_context(mail_client)
            self._clients["mail"] = mail_client
            
            # Print tools available in mail
            tools = await mail_client.list_tools()
            print(f"✅ Mail MCP connected - {len(tools)} tools available")
        except Exception as e:
            error_msg = f"❌ Failed to connect to Mail MCP at {self.mail_url}: {e}"
            print(error_msg)
            errors.append(error_msg)
        
        # Connect to Calendar MCP server
        try:
            print(f"Connecting to Calendar MCP at {self.calendar_url}...")
            calendar_client = MCPClient(self.calendar_url)
            await self._stack.enter_async_context(calendar_client)
            self._clients["calendar"] = calendar_client
            
            # Print tools available in calendar
            tools = await calendar_client.list_tools()
            print(f"✅ Calendar MCP connected - {len(tools)} tools available")
        except Exception as e:
            error_msg = f"❌ Failed to connect to Calendar MCP at {self.calendar_url}: {e}"
            print(error_msg)
            errors.append(error_msg)
        
        # Connect to Expense Tracker MCP server
        try:
            print(f"Connecting to Expense Tracker MCP at {self.expense_tracker_url}...")
            expense_tracker_client = MCPClient(self.expense_tracker_url)
            await self._stack.enter_async_context(expense_tracker_client)
            self._clients["expense_tracker"] = expense_tracker_client
            
            # Print tools available in expense tracker
            tools = await expense_tracker_client.list_tools()
            print(f"✅ Expense Tracker MCP connected - {len(tools)} tools available")
        except Exception as e:
            error_msg = f"❌ Failed to connect to Expense Tracker MCP at {self.expense_tracker_url}: {e}"
            print(error_msg)
            errors.append(error_msg)
        
        # Fail fast if any servers failed to connect
        if errors:
            print("\n🚫 MCP Orchestrator initialization failed!")
            print("The following servers could not be connected:")
            for error in errors:
                print(f"  {error}")
            print("\nPlease ensure all MCP servers are running:")
            print(f"  • Mail:            {self.mail_url}")
            print(f"  • Calendar:        {self.calendar_url}")
            print(f"  • Expense Tracker: {self.expense_tracker_url}")
            print("\nRun: ./start_mcp_servers.sh to start all servers")
            raise RuntimeError(f"Failed to connect to {len(errors)} MCP server(s). All servers must be running.")
        
        print("\n✅ MCP Orchestrator initialized successfully!")
        print(f"📊 Connected to {len(self._clients)} servers: {', '.join(self._clients.keys())}")
        
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Cleanup MCP clients and resources."""
        if self._stack:
            await self._stack.aclose()

    async def get_client(self, name: str) -> MCPClient:
        """Get an MCP client by name."""
        return self._clients[name]

    def to_plain_json_schema(self, schema: Any) -> Dict[str, Any]:
        """Convert any schema object to plain JSON-serializable dict."""
        if isinstance(schema, dict):
            return schema
        try:
            return json.loads(json.dumps(schema, default=str))
        except (TypeError, ValueError):
            return {}

    async def get_tools_specs(self, server: str, namespaced: bool = True) -> List[Dict[str, Any]]:
        """
        Get tools from a specific server.
        
        Args:
            server: Server name (mail, calendar, expense_tracker)
            namespaced: Whether to add server prefix to tool names
            
        Returns:
            List of tool specs from the specified server
        """
        if server not in self._clients:
            raise ValueError(f"Server {server} not found. Available servers: {list(self._clients.keys())}")
        
        specs: List[Dict[str, Any]] = []
        client = self._clients[server]
        
        try:
            tools = await client.list_tools()
            print(f"Found {len(tools)} tools in {server} server")
            
            for tool in tools:
                desc = getattr(tool, "description", "") or getattr(tool, "title", "")
                input_schema = self.to_plain_json_schema(getattr(tool, "inputSchema", {}) or {})
                bare_name = tool.name
                full_name = f"{server}__{bare_name}" if namespaced else bare_name
                
                specs.append({
                    "server": server,
                    "name": full_name,
                    "bare_name": bare_name,
                    "description": desc,
                    "inputSchema": input_schema,
                })
        except Exception as e:
            print(f"Error listing tools from {server}: {e}")
        
        return specs

    async def get_all_tools_specs(self, namespaced: bool = True) -> List[Dict[str, Any]]:
        """
        Return a normalized, model-agnostic view of all tools with namespacing.
        
        Discovers and combines tools from all connected MCP servers:
        - mail
        - calendar  
        - expense_tracker
        
        Each item:
        {
          "server": "calendar",
          "name": "calendar__list_events" (if namespaced) or "list_events",
          "bare_name": "list_events",
          "description": "...",
          "inputSchema": {...}  # plain JSON Schema
        }
        """
        specs: List[Dict[str, Any]] = []
        
        # Add tools from all external MCP servers
        for server in self._clients.keys():
            server_specs = await self.get_tools_specs(server, namespaced)
            specs.extend(server_specs)
        
        return specs

    async def call_tool(
        self, server: str, name: str, params: Dict[str, Any]
    ) -> Any:
        """
        Call a tool by server and name.
        
        Routes the call to the appropriate MCP server client and extracts the result.
        """
        if server not in self._clients:
            raise ValueError(f"Server {server} not found. Available servers: {list(self._clients.keys())}")
        
        # Call the tool and get the CallToolResult object
        result = await self._clients[server].call_tool(name, params or {})
        
        # Extract the content from CallToolResult
        # The result object has a 'content' attribute which is a list of content items
        if hasattr(result, 'content') and result.content:
            # Get the first content item
            content_item = result.content[0]
            
            # Check if it's a text content type
            if hasattr(content_item, 'text'):
                # Try to parse as JSON if possible
                try:
                    return json.loads(content_item.text)
                except (json.JSONDecodeError, TypeError):
                    return content_item.text
            
            # If it has other attributes, try to convert to dict
            if hasattr(content_item, 'model_dump'):
                return content_item.model_dump()
            
            return str(content_item)
        
        # Fallback: try to convert the whole result to dict
        if hasattr(result, 'model_dump'):
            return result.model_dump()
        
        return str(result)


