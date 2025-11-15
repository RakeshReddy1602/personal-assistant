# Personal Assistant Application Flow

## Architecture Overview

This personal assistant uses a multi-agent architecture with MCP (Micro-Agent Communication Protocol) servers for tool execution.

## Application Flow

```
User Query
    ↓
[main.py] - Single state management
    ↓
[Query Rewriter] - Rewrites query using history
    ↓
[Router Agent] - Classifies query into categories
    ↓
    ├─→ [Master Agent] - Handles mail, calendar, drive, expense_tracker
    │       ↓
    │   [MCP Orchestrator] - Connects to MCP servers
    │       ↓
    │   [Gemini] - Decides which tools to call
    │       ↓
    │   [Tool Execution] - Executes via MCP servers
    │       ↓
    │   [Response Generation] - Gemini generates final response
    │
    └─→ [Resume Agent] - Handles resume preparation tasks
            ↓
        [Gemini] - Generates resume content
    ↓
[Response] - Shown to user
    ↓
[History Update] - State updated with user query, tool calls, and response
```

## State Management

### Single State Instance
- One `AssistantState` instance is created in `main.py` at startup
- This state persists across all user interactions
- State is passed through the LangGraph pipeline and updated by each node

### State Structure
```python
class AssistantState(TypedDict):
    category_to_be_served: str      # Category from router
    query_to_be_served: str         # Current user query (rewritten)
    history: List[Message]          # Conversation history (capped at 40)
    response: str                   # Agent's response
```

### Message Structure
```python
class Message(TypedDict):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: NotRequired[str]  # Tool name (for tool messages)
```

## History Management

### What Gets Stored in History
1. **User messages**: Every user query
2. **Assistant responses**: Every agent response
3. **Tool calls**: Tool execution results with tool names
4. **System messages**: (optional) System-level information

### History Updates
- **Before processing**: User query is added to history
- **During processing**: Tool calls are added to history by `handle_master`
- **After processing**: Assistant response is added to history
- **Limit**: History is capped at last 40 messages

### History Flow in Master Agent
```python
# 1. User query added in main.py
state = push_history(state, "user", user_input)

# 2. Tool calls added in handle_master
for tool_call in tool_calls_made:
    state = push_history(state, "tool", tool_call["result"])
    state["history"][-1]["name"] = tool_call["name"]

# 3. Assistant response added in main.py
state = push_history(state, "assistant", reply)
```

## MCP Server Architecture

### MCP Servers
- **Mail MCP**: Handles Gmail operations (read, send)
- **Calendar MCP**: Handles Google Calendar operations (list, create, update, delete)

### MCP Orchestrator
- Connects to all MCP servers using `fastmcp.Client`
- Discovers tools dynamically from servers
- Routes tool calls to appropriate servers
- Converts MCP tool specs to Gemini function declarations

### Tool Discovery Flow
```
MCP Servers (running separately)
    ↓
MCPOrchestrator connects via Client
    ↓
get_all_tools_specs() - Fetches tool schemas
    ↓
Convert to Gemini format
    ↓
Pass to Gemini model
    ↓
Gemini decides which tools to call
    ↓
call_tool() - Executes on appropriate server
```

## Running the Application

### 1. Start MCP Servers
```bash
# Terminal 1: Mail MCP
GOOGLE_OAUTH_CLIENT_FILE=oauth-creds.json python -m agent.mcp_servers.mail_mcp.main

# Terminal 2: Calendar MCP
GOOGLE_OAUTH_CLIENT_FILE=oauth-creds.json python -m agent.mcp_servers.calender_mcp.main

# Or use the startup script:
./start_mcp_servers.sh
```

### 2. Run the Assistant
```bash
# Terminal 3: Main agent
python -m agent.main
```

## Key Components

### 1. Query Rewriter (`agent/agents/query_rewriter.py`)
- Rewrites user query using conversation history
- Makes queries more explicit and contextual
- Updates `state["query_to_be_served"]`

### 2. Router Agent (`agent/agents/router_agent.py`)
- Classifies query into categories: mail, calendar, resume, etc.
- Uses Ollama for classification
- Updates `state["category_to_be_served"]`

### 3. Master Agent (`agent/agents/master.py`)
- Handles mail, calendar, drive, expense_tracker queries
- Uses MCP Orchestrator to connect to MCP servers
- Uses Gemini for tool calling decisions
- Updates history with tool calls
- Updates `state["response"]`

### 4. Resume Agent (`agent/agents/resume_agent.py`)
- Handles resume preparation tasks
- Uses Gemini for content generation
- Updates `state["response"]`

### 5. MCP Orchestrator (`agent/mcp_servers/orchestrator.py`)
- Manages connections to MCP servers
- Provides unified tool discovery
- Routes tool execution to appropriate servers

## Environment Variables

Required in `.env`:
```bash
GOOGLE_OAUTH_CLIENT_FILE=oauth-creds.json
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp  # optional, defaults to this
```

## Tool Definitions

### Mail Tools (`agent/mcp_servers/mail_mcp/tools.py`)
- `read_emails`: Read Gmail messages with optional query/labels
- `send_email`: Send email via Gmail

### Calendar Tools (`agent/mcp_servers/calender_mcp/tools.py`)
- `list_events`: List calendar events in time range
- `create_event`: Create new calendar event
- `get_event`: Get specific event by ID
- `update_event`: Update existing event
- `delete_event`: Delete event by ID

## State Persistence

- State persists in memory for the duration of the session
- History is maintained across all interactions
- Clearing history: Type `clear` in the assistant prompt
- Viewing history: Type `history` in the assistant prompt

## Error Handling

- All errors are caught and displayed to user
- State remains consistent even on errors
- Tool execution errors are captured and passed back to Gemini
- Orchestrator handles connection failures gracefully

