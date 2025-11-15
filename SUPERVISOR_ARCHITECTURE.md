# Supervisor Multi-Agent Architecture

This document describes the supervisor architecture implementation using LangChain for coordinating specialized sub-agents.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Supervisor Agent                   │
│                  (LangChain ChatGoogleGenerativeAI)          │
│                                                               │
│  • Analyzes user queries                                     │
│  • Delegates to specialized sub-agents                       │
│  • Synthesizes responses from multiple agents                │
│  • Maintains conversation history                            │
└───────────────────┬─────────────────┬─────────────────┬──────┘
                    │                 │                 │
        ┌───────────▼──────┐  ┌──────▼────────┐  ┌────▼──────────┐
        │  Mail Sub-Agent  │  │ Calendar Sub- │  │ Expense Sub-  │
        │                  │  │    Agent      │  │    Agent      │
        │ • Read emails    │  │ • Create      │  │ • Track       │
        │ • Send emails    │  │   events      │  │   expenses    │
        │ • Manage         │  │ • List        │  │ • Generate    │
        │   attachments    │  │   schedule    │  │   reports     │
        │ • Mark read/     │  │ • Update      │  │ • Budget      │
        │   unread         │  │   events      │  │   analysis    │
        └────────┬─────────┘  └───────┬───────┘  └───────┬───────┘
                 │                    │                   │
        ┌────────▼──────────┐  ┌──────▼──────────┐      │
        │  Mail MCP Server  │  │ Calendar MCP    │      │
        │  (Port 6281)      │  │ Server          │      │
        │                   │  │ (Port 6282)     │      │
        │ • Gmail API       │  │ • Google        │      │
        │   integration     │  │   Calendar API  │      │
        └───────────────────┘  └─────────────────┘      │
                                                         │
                                        ┌────────────────▼────┐
                                        │ Future: Database    │
                                        │ & Analytics Backend │
                                        └─────────────────────┘
```

## Components

### 1. Master Supervisor Agent (`agents/master.py`)

The master supervisor is the entry point for all user interactions.

**Responsibilities:**
- Receives user queries from the main application
- Analyzes the query to determine which sub-agent(s) to delegate to
- Can delegate to multiple sub-agents for complex queries
- Maintains conversation history and context
- Synthesizes responses from sub-agents into coherent answers

**Technology:**
- LangChain's `ChatGoogleGenerativeAI` with Gemini
- Tool binding for sub-agent delegation
- Async message processing with tool calling loop

**Key Features:**
- Intelligent delegation based on query analysis
- Support for multi-agent coordination
- Context-aware responses
- Conversation history management (last 40 messages)

### 2. Mail Sub-Agent (`agents/mail_sub_agent.py`)

Specialized agent for all email operations.

**Capabilities:**
- Reading and searching emails
- Sending emails with proper formatting
- Managing email status (read/unread)
- Handling attachments (list, download)
- Email summarization
- Context-aware tone adjustment (professional vs. casual)

**MCP Tools:**
- `read_emails` - Search and retrieve emails
- `send_email` - Send new emails
- `mark_email_read` / `mark_email_unread` - Status management
- `delete_email` - Move to trash
- `list_attachments` - List email attachments
- `download_attachment` - Download files

**Best Practices:**
- Uses user's full name "Rakesh Reddy" for professional emails
- Uses short name "Rakesh" for casual emails
- Default email: rakeshb1602@gmail.com
- Clear subject lines and proper greetings

### 3. Calendar Sub-Agent (`agents/calendar_sub_agent.py`)

Specialized agent for calendar and scheduling operations.

**Capabilities:**
- Creating calendar events
- Listing upcoming events
- Searching for specific events
- Updating event details
- Deleting events
- Managing recurring events
- Timezone-aware scheduling

**MCP Tools:**
- `create_event` - Create new calendar events
- `list_events` - List upcoming events
- `get_event` - Get specific event details
- `update_event` - Update existing events
- `delete_event` - Delete events
- `search_events` - Search for events

**Best Practices:**
- Uses ISO format for dates and times
- Default timezone: Asia/Kolkata
- Clear event titles and descriptions
- Proper notification setup

### 4. Expense Sub-Agent (`agents/expense_sub_agent.py`)

Specialized agent for expense tracking and financial management.

**Current Status:** Placeholder implementation

**Planned Capabilities:**
- Recording new expenses
- Categorizing spending (food, transport, utilities, etc.)
- Generating expense reports
- Analyzing spending patterns
- Budget tracking and alerts
- Monthly/weekly summaries

**Future Implementation:**
- Database backend for expense storage
- MCP server for expense tracking tools
- Analytics and visualization
- Budget management features
- Receipt scanning and processing

**Best Practices:**
- Default currency: INR
- ISO format for dates
- Consistent categorization
- Clear spending summaries

### 5. Sub-Agent Tools Wrapper (`agents/sub_agent_tools.py`)

Wraps sub-agents as LangChain tools for the supervisor to use.

**Exported Tools:**
1. `mail_agent_tool` - Delegates to mail sub-agent
2. `calendar_agent_tool` - Delegates to calendar sub-agent
3. `expense_agent_tool` - Delegates to expense sub-agent

**How It Works:**
```python
@tool
async def mail_agent_tool(query: str) -> str:
    """Delegate email tasks to the mail agent."""
    orchestrator = await get_orchestrator()
    async with orchestrator as orch:
        return await execute_mail_agent(query, orch)
```

### 6. MCP Orchestrator (`mcp_servers/orchestrator.py`)

Manages connections to external MCP servers.

**Server Connections:**
- **Mail MCP**: Port 6281 - Gmail API integration
- **Calendar MCP**: Port 6282 - Google Calendar API integration
- **Expense Tracker MCP**: Port 6280 - (Future)

**Key Methods:**
- `get_tools_specs(server)` - Get tools from a specific server
- `get_all_tools_specs()` - Get all available tools
- `call_tool(server, name, params)` - Execute a tool

**Features:**
- Async context manager for connection lifecycle
- Automatic tool discovery
- Tool namespacing (e.g., `mail__send_email`)
- Fail-fast if servers are unavailable

## Message Flow

### Simple Query (Single Agent)

```
User: "Read my unread emails"
    ↓
Master Supervisor
    ├─ Analyzes query
    ├─ Identifies: Email task
    └─ Delegates to mail_agent_tool
        ↓
Mail Sub-Agent
    ├─ Receives query
    ├─ Uses read_emails tool (MCP)
    ├─ Processes results
    └─ Returns formatted summary
        ↓
Master Supervisor
    └─ Returns response to user
```

### Complex Query (Multiple Agents)

```
User: "Check my calendar for tomorrow and send meeting invites"
    ↓
Master Supervisor
    ├─ Analyzes query
    ├─ Identifies: Calendar + Email task
    ├─ Step 1: Delegates to calendar_agent_tool
    │   ↓
    │   Calendar Sub-Agent
    │   ├─ Lists events for tomorrow
    │   └─ Returns event details
    ├─ Step 2: Delegates to mail_agent_tool with context
    │   ↓
    │   Mail Sub-Agent
    │   ├─ Uses event details from calendar
    │   ├─ Composes meeting invites
    │   └─ Sends emails
    └─ Synthesizes both results into coherent response
```

## Key Features

### 1. Intelligent Delegation
The supervisor analyzes queries and routes them to the appropriate specialized agent:
- Single agent for simple tasks
- Multiple agents for complex workflows
- Context passing between agents

### 2. Tool Calling with LangChain
- Uses LangChain's `bind_tools()` for clean tool integration
- Automatic tool schema generation
- Built-in retry and error handling

### 3. Conversation History
- Maintains last 40 messages
- Stores tool calls and results
- Enables context-aware responses
- Proper message type handling (HumanMessage, AIMessage, ToolMessage)

### 4. Error Handling
- Graceful error recovery
- User-friendly error messages
- Internal error tracking
- Fallback responses

### 5. Modularity
- Easy to add new sub-agents
- Clear separation of concerns
- Pluggable MCP servers
- Independent agent development

## Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp  # Optional, default shown

# Gmail API (for Mail MCP)
# Requires oauth-creds.json and token.pickle

# Google Calendar API (for Calendar MCP)
# Shares same credentials as Gmail
```

### MCP Server URLs (Optional)

Default URLs can be overridden when initializing the orchestrator:

```python
orchestrator = MCPOrchestrator(
    mail_url="http://127.0.0.1:6281/mcp",
    calendar_url="http://127.0.0.1:6282/mcp",
    expense_tracker_url="http://127.0.0.1:6280/mcp"
)
```

## Running the System

### 1. Start MCP Servers

```bash
# Start all MCP servers
./start_mcp_servers.sh
```

This script starts:
- Mail MCP server (port 6281)
- Calendar MCP server (port 6282)

### 2. Run the Main Agent

```bash
cd agent
source venv/bin/activate
python main.py

# Or use the run script to avoid Python version conflicts
./run.sh
```

### 3. Verify Connections

On startup, you should see:
```
Starting MCP Orchestrator initialization...
Connecting to Mail MCP at http://127.0.0.1:6281/mcp...
✅ Mail MCP connected - 7 tools available
Connecting to Calendar MCP at http://127.0.0.1:6282/mcp...
✅ Calendar MCP connected - 6 tools available
✅ MCP Orchestrator initialized successfully!
```

## Adding New Sub-Agents

### Step 1: Create Sub-Agent Module

Create `agents/your_sub_agent.py`:

```python
async def execute_your_agent(query: str, orchestrator: MCPOrchestrator) -> str:
    # Get tools from MCP server
    tools_specs = await orchestrator.get_tools_specs("your_server", namespaced=True)
    
    # Create LangChain model with tools
    llm = ChatGoogleGenerativeAI(...)
    llm_with_tools = llm.bind_tools(langchain_tools)
    
    # Tool calling loop
    # ... (see mail_sub_agent.py for template)
    
    return response
```

### Step 2: Create Tool Wrapper

Add to `agents/sub_agent_tools.py`:

```python
@tool
async def your_agent_tool(query: str) -> str:
    """Description of your agent's capabilities."""
    orchestrator = await get_orchestrator()
    async with orchestrator as orch:
        return await execute_your_agent(query, orch)

# Add to SUB_AGENT_TOOLS list
SUB_AGENT_TOOLS = [
    mail_agent_tool,
    calendar_agent_tool,
    expense_agent_tool,
    your_agent_tool  # Add here
]
```

### Step 3: Create MCP Server

Create `mcp_servers/your_mcp/`:
- `main.py` - FastMCP server setup
- `services.py` - Service implementations
- `tools.py` - Tool definitions

### Step 4: Update Orchestrator

Add to `mcp_servers/orchestrator.py`:

```python
def __init__(self, your_url: Optional[str] = None):
    self.your_url = your_url or "http://127.0.0.1:PORT/mcp"
    
async def __aenter__(self):
    # Add connection code
    your_client = MCPClient(self.your_url)
    await self._stack.enter_async_context(your_client)
    self._clients["your_server"] = your_client
```

## Testing

### Test Individual Sub-Agents

```python
# Test mail agent
from agent.agents.mail_sub_agent import execute_mail_agent
from agent.mcp_servers.orchestrator import MCPOrchestrator

async def test():
    orch = MCPOrchestrator()
    async with orch:
        result = await execute_mail_agent("Read unread emails", orch)
        print(result)
```

### Test Supervisor Delegation

```python
# Run full query through supervisor
state = {
    "query_to_be_served": "Check my calendar and send updates",
    "history": []
}

result = await handle_master(state)
print(result["response"])
```

## Benefits of This Architecture

1. **Separation of Concerns**: Each agent focuses on its domain
2. **Scalability**: Easy to add new agents without modifying existing ones
3. **Maintainability**: Clear code organization and boundaries
4. **Flexibility**: Can handle simple or complex multi-agent workflows
5. **Testability**: Each component can be tested independently
6. **Error Isolation**: Errors in one agent don't affect others
7. **Parallel Processing**: Future support for concurrent agent execution
8. **Context Sharing**: Supervisor can pass context between agents

## Future Enhancements

### 1. Parallel Agent Execution
- Execute independent sub-agents concurrently
- Aggregate results efficiently
- Reduce overall response time

### 2. Agent Collaboration
- Sub-agents can communicate with each other
- Shared context and state management
- Complex multi-step workflows

### 3. Streaming Responses
- Stream partial responses as they become available
- Better user experience for long operations
- Progress updates during execution

### 4. Agent Memory
- Long-term memory for each sub-agent
- Personalization based on user history
- Learning from past interactions

### 5. Advanced Analytics
- Agent performance metrics
- Usage patterns and optimization
- Cost tracking and optimization

### 6. Dynamic Agent Loading
- Load agents on-demand
- Plugin architecture for third-party agents
- Hot-reload capability

## Troubleshooting

### MCP Connection Errors
```
❌ Failed to connect to Mail MCP
```
**Solution**: Ensure MCP servers are running with `./start_mcp_servers.sh`

### Import Errors
```
Unable to import 'langchain_google_genai'
```
**Solution**: Use venv's Python directly or run `./run.sh`

### Tool Execution Errors
Check logs for specific tool failures and verify:
- Gmail API credentials are valid
- OAuth token hasn't expired
- Required scopes are granted

### Agent Timeout
If agent reaches iteration limit:
- Check for tool errors in logs
- Verify tool responses are properly formatted
- Ensure model can parse tool results

## References

- [LangChain Documentation](https://python.langchain.com/)
- [LangChain Multi-Agent Systems](https://python.langchain.com/docs/tutorials/multi_agent/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Gemini API Documentation](https://ai.google.dev/docs)

