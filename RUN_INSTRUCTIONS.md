# How to Run the Personal Assistant

## Prerequisites

1. **Python 3.10+** installed
2. **Environment variables** set in `.env`:
   ```bash
   GOOGLE_OAUTH_CLIENT_FILE=oauth-creds.json
   GOOGLE_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-exp  # optional
   ```
3. **OAuth credentials** file at `agent/oauth-creds.json`

## Step-by-Step Instructions

### Step 1: Clean Python Cache (if you had import errors)
```bash
cd /Users/rakeshreddy/learning/AI/personal-assistant
find agent -name "*.pyc" -delete
find agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### Step 2: Start MCP Servers

**Option A: Using the startup script (recommended)**
```bash
./start_mcp_servers.sh
```

**Option B: Manual (in separate terminals)**

Terminal 1 - Mail MCP:
```bash
cd /Users/rakeshreddy/learning/AI/personal-assistant
MCP_PORT=6281 GOOGLE_OAUTH_CLIENT_FILE=oauth-creds.json python -m agent.mcp_servers.mail_mcp.main
```

Terminal 2 - Calendar MCP:
```bash
cd /Users/rakeshreddy/learning/AI/personal-assistant
MCP_PORT=6282 GOOGLE_OAUTH_CLIENT_FILE=oauth-creds.json python -m agent.mcp_servers.calender_mcp.main
```

You should see:
```
Starting Mail MCP server on port 6281...
Starting Calendar MCP server on port 6282...
```

### Step 3: Run the Assistant

In a new terminal:
```bash
cd /Users/rakeshreddy/learning/AI/personal-assistant
python -m agent.main
```

You should see:
```
Assistant ready. Type 'exit' to quit, 'clear' to reset, 'history' to view.
Note: Make sure MCP servers are running:
  - Mail MCP: python -m agent.mcp_servers.mail_mcp.main
  - Calendar MCP: python -m agent.mcp_servers.calender_mcp.main

You: 
```

## Testing the Assistant

### Test 1: Simple Query
```
You: Hi, who are you?
Assistant: I'm your personal assistant that can help you manage emails and calendars...
```

### Test 2: Email Query
```
You: Read my latest 5 emails
Assistant: [Connects to Mail MCP and fetches emails]
```

### Test 3: Calendar Query
```
You: What's on my calendar today?
Assistant: [Connects to Calendar MCP and lists events]
```

### Test 4: View History
```
You: history
History:
user: Hi, who are you?
assistant: I'm your personal assistant...
user: Read my latest 5 emails
tool: {"messages": [...]}
assistant: Here are your latest emails...
```

### Test 5: Clear History
```
You: clear
Cleared history.
```

## Troubleshooting

### Error: "cannot import name 'NotRequired' from 'typing'"
**Solution:** Clean Python cache
```bash
find agent -name "*.pyc" -delete
find agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### Error: "Client failed to connect: All connection attempts failed"
**Solution:** Make sure MCP servers are running
1. Check if servers are running: `ps aux | grep "agent.mcp_servers"`
2. If not, start them using `./start_mcp_servers.sh`
3. Wait a few seconds for servers to fully start before running the assistant

### Error: "GEMINI_API_KEY is not set"
**Solution:** Add your Gemini API key to `.env`:
```bash
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### Error: "OAuth client file not found"
**Solution:** Make sure `agent/oauth-creds.json` exists with your Google OAuth credentials

## Stopping the Application

1. **Stop the assistant**: Type `exit` or press `Ctrl+C`
2. **Stop MCP servers**: 
   - If using startup script: Press `Ctrl+C` in that terminal
   - If manual: Press `Ctrl+C` in each server terminal
   - Or find PIDs and kill: `ps aux | grep "agent.mcp_servers" | awk '{print $2}' | xargs kill`

## Architecture

```
User Query
    ↓
[main.py] - Single state instance
    ↓
[Query Rewriter] - Rewrites with history
    ↓
[Router] - Classifies category
    ↓
[Master Agent] - Connects to MCP servers
    ↓
[MCPOrchestrator] - Discovers tools from servers
    ↓
[Gemini] - Decides which tools to call
    ↓
[Tool Execution] - Executes via MCP
    ↓
[Response] - Shown to user
    ↓
[History Update] - State updated
```

## Files Structure

```
agent/
├── main.py                      # Entry point
├── agents/
│   ├── query_rewriter.py       # Rewrites queries
│   ├── router_agent.py         # Routes to agents
│   ├── master.py               # Master agent (mail/calendar)
│   └── resume_agent.py         # Resume agent
├── mcp_servers/
│   ├── orchestrator.py         # MCP orchestrator
│   ├── mail_mcp/
│   │   ├── main.py            # Mail MCP server
│   │   ├── tools.py           # Mail tools
│   │   └── services.py        # Gmail service
│   └── calender_mcp/
│       ├── main.py            # Calendar MCP server
│       ├── tools.py           # Calendar tools
│       └── services.py        # Calendar service
├── states/
│   └── assistant_state.py     # State definition
└── schema/
    └── init_assistant_graph.py # LangGraph setup
```

## Next Steps

Once everything is working:
1. Try complex queries that require multiple tool calls
2. Test multi-turn conversations
3. Check history to see tool calls
4. Extend with more MCP servers (Drive, Expense Tracker, etc.)

