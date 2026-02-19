# AI-Powered Personal Assistant - Technical Architecture

## 🎯 Project Overview

An intelligent, multi-agent personal assistant system built with **LangChain**, **LangGraph**, **Google Gemini**, and **MCP (Model Context Protocol)** that autonomously manages emails, calendar events, and expenses through a sophisticated agent orchestration architecture with real-time AI-powered evaluation.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                   (Textual TUI - Terminal UI)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH WORKFLOW                         │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────────┐    │          
│  │Query Rewriter├──→ │Router Agent ├──→ │ Master Supervisor│    │
│  └──────────────┘    └────────|────┘    └─-───────┬─────────┘   │
│                               |                   │             │
│                          ┌────↓───────────────────┼──────────┐  │
│                          ↓                        ↓          ↓  │
│                   ┌──────────┐       ┌──────────┐  ┌────────┐   │
│                   │Mail Agent│       │Calendar  │  │Expense │   │
│                   │          │       │ Agent    │  │ Agent  │   │
│                   └──────────┘       └──────────┘  └────────┘   │ 
└─────────────────────────────────────────────────────────────────┘
                          │                  │            │
                          ↓                  ↓            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVER LAYER (HTTP)                      │
│  ┌──────────────┐   ┌─────────────────┐   ┌─────────────────┐   │
│  │ Mail MCP     │   │ Calendar MCP    │   │ Expense MCP     │   │
│  │ Server       │   │ Server          │   │  Server         │   │
│  └──────┬───────┘   └────────┬────────┘   └────────┬────────┘   │
└─────────┼────────────────────┼─────────────────────┼────────────┘
          │                    │                     │
          ↓                    ↓                     ↓
┌────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                           │
│  ┌──────────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│  │ Gmail API    │   │ Google Calendar │   │ Expense Tracker │  │
│  │ (OAuth 2.0)  │   │ API (OAuth 2.0) │   │ Server          │  │
│  └──────────────┘   └─────────────────┘   └─────────────────┘  │
└────────────────────────────────────────────────────────────────┘

          ┌─────────────────────────────────────────┐
          │       EVALUATION PIPELINE               │
          │                                         │
          │  ┌────────────┐    ┌───────────────┐    │
          │  │Redis Queue │───→│Gemini         │    │
          │  │(Async)     │    │Evaluator      │    │
          │  └────────────┘    └───────┬───────┘    │
          │                            ↓            │
          │                    ┌───────────────┐    │
          │                    │Eval Server    │    │
          │                    │(PostgreSQL)   │    │
          │                    └───────────────┘    │
          └─────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|----------|
| **Language** | Python | 3.10+ | Core implementation |
| **LLM Framework** | LangChain | 0.1.0+ | Agent orchestration & tool calling |
| **Workflow Engine** | LangGraph | 0.0.20+ | State machine & agent routing |
| **LLM Provider** | Google Gemini | 1.5-Flash/Pro | AI reasoning & decision making |
| **MCP Framework** | FastMCP | Latest | Microservice communication |
| **UI Framework** | Textual | 0.47.1+ | Terminal user interface |
| **Queue System** | Redis | 5.0.0+ | Async evaluation queue |
| **Database** | PostgreSQL | Latest | Evaluation storage |
| **Local Storage** | SQLite | 3.x | Expense tracking |
| **OAuth** | Google OAuth 2.0 | Latest | Secure API access |

### Key Libraries

- **langchain-google-genai** - Gemini integration
- **google-api-python-client** - Gmail & Calendar APIs
- **httpx** - Async HTTP client
- **redis** - Redis queue client
- **python-dotenv** - Environment management
- **rich** - Terminal formatting

## 📊 Core Components

### 1. LangGraph Workflow Engine

**File:** `agent/schema/init_assistant_graph.py`

The workflow orchestrates the entire request lifecycle:

```python
Entry Point → Query Rewriter → Router → {Master, Resume, None}
                                          ↓
                                    Sub-Agents → Response
```

**Key Features:**
- **State Management**: Maintains conversation history and context
- **Conditional Routing**: Dynamic agent selection based on query category
- **Error Handling**: Graceful fallback for unsupported queries
- **Graph Compilation**: Optimized execution path

### 2. Query Rewriter

**File:** `agent/agents/query_rewriter.py`

**Purpose:** Enhances user queries for better agent understanding

**Capabilities:**
- Context-aware query reformulation
- Ambiguity resolution
- Intent clarification
- History integration

**Example:**
```
User: "What about tomorrow?"
Rewritten: "What calendar events do I have scheduled for tomorrow, November 17, 2025?"
```

### 3. Router Agent

**File:** `agent/agents/router_agent.py`

**Purpose:** Intelligent query categorization using local LLM (Ollama)

**Categories:**
- `mail` - Email operations
- `calendar` - Calendar management
- `expense_tracker` - Financial tracking
- `resume_preparation` - Resume building
- `greeting` - Conversational
- `none` - Unsupported

**Model:** Llama3 (local, fast, no API costs)

**Evaluation:** Automatically publishes routing decisions to eval queue

### 4. Master Supervisor Agent

**File:** `agent/agents/master.py`

**Architecture:** LangChain's Supervisor Pattern

**Responsibilities:**
1. **Delegation**: Routes to appropriate sub-agents
2. **Coordination**: Manages multi-agent workflows
3. **Context**: Maintains conversation history (40 messages)
4. **Tool Calling**: Executes sub-agent tools via LangChain

**Key Features:**
- **Tool Binding**: Sub-agents exposed as LangChain tools
- **Iterative Execution**: Max 20 iterations for complex tasks
- **History Management**: Caps at 40 messages for performance
- **Structured Responses**: JSON-formatted tool results

### 5. Sub-Agent Architecture

All sub-agents follow the same pattern:

**Common Features:**
- Direct MCP server connection
- Tool calling loop (max 10 iterations)
- Automatic evaluation publishing
- Error handling & recovery
- Gemini-powered reasoning

#### Mail Agent

**File:** `agent/agents/mail_agent.py`

**Capabilities:**
- Read emails (with filters, labels, search)
- Send emails (with CC, BCC)
- Delete emails (move to trash)
- Mark as read/unread
- List attachments
- Download attachments

**MCP Server:** `http://127.0.0.1:6281/mcp`

**Tools:** 7 tools exposed via FastMCP

#### Calendar Agent

**File:** `agent/agents/calendar_agent.py`

**Capabilities:**
- Create events (with attendees, location, reminders)
- List upcoming events
- Search events
- Update event details
- Delete events
- Handle recurring events

**MCP Server:** `http://127.0.0.1:6282/mcp`

**Timezone:** Asia/Kolkata (configurable)

#### Expense Tracker Agent

**File:** `agent/agents/expense_tracker_agent.py`

**Capabilities:**
- Add expenses with categorization
- Track spending by category
- Generate monthly/yearly reports
- Budget management
- Expense analytics
- Export data

**MCP Server:** `http://127.0.0.1:6280/mcp`

**Storage:** Local SQLite database

## 🔌 MCP (Model Context Protocol) Architecture

### What is MCP?

MCP is a microservice architecture pattern that:
- Decouples business logic from agent layer
- Enables independent service scaling
- Provides language-agnostic interfaces
- Facilitates tool discovery & registration

### MCP Server Structure

Each MCP server follows this pattern:

```python
from fastmcp import FastMCP

mcp = FastMCP('Service Name')

@mcp.tool(description="Tool description")
def tool_name(param: str) -> dict:
    """Tool implementation"""
    return {"result": "data"}

# HTTP server on dedicated port
mcp.run(transport="http", host="127.0.0.1", port=6281)
```

**Benefits:**
1. **Isolation**: Each service runs independently
2. **Discovery**: Tools auto-discovered by agents
3. **HTTP Transport**: REST-like communication
4. **Type Safety**: Pydantic schema validation

### MCP Orchestrator

**File:** `agent/mcp_servers/orchestrator.py`

**Purpose:** Connection pool manager for MCP servers

**Features:**
- Single connection per server (shared across agents)
- Automatic lifecycle management
- Connection health checks
- Tool discovery & listing
- Fail-fast initialization
- Namespaced tool names

**Example:**
```python
async with MCPOrchestrator() as orchestrator:
    # Get tools from specific server
    tools = await orchestrator.get_tools_specs("mail")
    
    # Execute tool
    result = await orchestrator.call_tool(
        server="mail",
        name="read_emails",
        params={"max_results": 10}
    )
```

## 🔄 Evaluation System

### Architecture: Event-Driven, Zero-Latency

**Flow:**
```
Agent Response → Redis Queue (async) → Consumer → Gemini Eval → PostgreSQL
                     ↓
              User gets immediate response
              (no blocking!)
```

### Components

#### 1. Publisher

**File:** `agent/eval_queue/publisher.py`

```python
publish_eval_event(
    agent_name="mail_agent",
    query="User's question",
    response="Agent's answer",
    category="mail",
    metadata={"execution_time_ms": 123.45}
)
```

**Characteristics:**
- Non-blocking (fire-and-forget)
- Redis RPUSH for FIFO ordering
- JSON serialization
- Automatic error handling

#### 2. Consumer

**File:** `agent/eval_queue/consumer.py`

**Process:**
1. BLPOP from Redis queue (blocking read)
2. Extract event data
3. Call Gemini evaluator
4. Store result in eval server
5. Log status

**Running:**
```bash
python start_eval_consumer.py
```

#### 3. Gemini Evaluator

**File:** `agent/eval_queue/gemini_evaluator.py`

**Evaluation Criteria:**
- **Correctness**: Did it answer the query?
- **Completeness**: Is all info provided?
- **Clarity**: Is it understandable?
- **Appropriateness**: Is the response suitable?

**Output:**
```json
{
  "status": "pass",  // or "fail"
  "score": 1.0,      // 1.0 for pass, 0.0 for fail
  "justification": "Response correctly lists...",
  "improvements": "Could add timestamps..."
}
```

#### 4. Eval Server

**File:** `eval_server/main.py`

**Technology:** FastAPI + PostgreSQL

**Endpoints:**
- `POST /evals` - Store evaluation result
- `GET /evals` - Query evaluations (with filters)
- `GET /stats` - Aggregated statistics
- `GET /health` - Health check

**Database Schema:**
```sql
CREATE TABLE eval_results (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR,
    category VARCHAR,
    status VARCHAR,
    score FLOAT,
    execution_time_ms FLOAT,
    user_input TEXT,          -- Full user query
    agent_output TEXT,        -- Full agent response
    justification TEXT,       -- Gemini's reasoning
    improvements TEXT,        -- Suggestions
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Benefits:**
- Complete input/output logging
- Time-series analysis
- Pass/fail tracking
- Performance metrics
- Improvement tracking

## 🎨 User Interface

**File:** `agent/main.py`

**Framework:** Textual (Python TUI)

**Features:**

### Terminal UI Components

1. **Header** - Clock and app title
2. **Status Bar** - Available commands and shortcuts
3. **Chat Container** - Rich formatted conversation
4. **Input Box** - User query input
5. **Footer** - Key bindings

### Commands

| Command | Action |
|---------|--------|
| `/clear` | Clear conversation history |
| `/history` | Show recent 10 messages |
| `/state` | Display current state |
| `/help` | Show help message |
| `Ctrl+C` | Quit application |
| `Ctrl+L` | Clear history |
| `Ctrl+H` | Show history |

### Message Rendering

- **User Messages**: Green panels
- **Assistant Messages**: Blue panels with Markdown
- **Tool Calls**: Yellow text
- **Errors**: Red panels

## 📈 Data Flow

### 1. User Query Flow

```
User Input
    ↓
Query Rewriter (enhance query)
    ↓
Router Agent (categorize)
    ↓
Master Supervisor (delegate)
    ↓
Sub-Agent (e.g., Mail Agent)
    ↓
MCP Server (e.g., Mail MCP)
    ↓
External Service (e.g., Gmail API)
    ↓
Response back to user
    ↓
Eval Event → Redis (async)
```

### 2. Tool Calling Flow

```
Sub-Agent receives query
    ↓
Gemini decides to use tool
    ↓
Tool call generated (function name + args)
    ↓
MCP Client executes tool
    ↓
MCP Server processes request
    ↓
External API called
    ↓
Result returned to MCP Server
    ↓
MCP Client receives result
    ↓
Result passed to Gemini
    ↓
Gemini generates final response
```

### 3. Evaluation Flow

```
Agent completes task
    ↓
publish_eval_event() called
    ↓
Event pushed to Redis queue (non-blocking)
    ↓
Consumer picks up event (BLPOP)
    ↓
Gemini evaluates query + response
    ↓
Evaluation sent to Eval Server (HTTP POST)
    ↓
PostgreSQL stores evaluation
    ↓
Available via API (GET /evals)
```

## 🔐 Authentication & Security

### Google OAuth 2.0

**Files:**
- `agent/oauth-creds.json` - OAuth client credentials
- `agent/token.pickle` - Cached access token

**Scopes:**
- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/calendar`

**Flow:**
1. First run triggers OAuth consent
2. Browser opens for authorization
3. Token cached locally
4. Auto-refresh on expiry

### Environment Variables

```env
# Gemini AI
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_EVAL_MODEL=gemini-1.5-flash

# MCP Servers
MAIL_MCP_URL=http://127.0.0.1:6281/mcp
CALENDAR_MCP_URL=http://127.0.0.1:6282/mcp
EXPENSE_MCP_URL=http://127.0.0.1:6280/mcp

# Redis (Evaluation Queue)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Eval Server
EVAL_SERVER_URL=http://localhost:8001
```

## 🚀 Key Features

### 1. Multi-Agent Orchestration

- **Supervisor Pattern**: Centralized coordination
- **Sub-Agent Specialization**: Domain experts
- **Dynamic Delegation**: Intelligent task routing
- **Parallel Execution**: Where applicable

### 2. Conversational Memory

- **History Tracking**: Last 40 messages
- **Context Preservation**: Across queries
- **State Management**: LangGraph state
- **Role Tracking**: User/Assistant/Tool messages

### 3. Tool Calling

- **LangChain Integration**: Native tool binding
- **Structured Arguments**: Pydantic validation
- **Error Handling**: Graceful failures
- **Result Formatting**: JSON responses

### 4. Real-Time Evaluation

- **Zero Latency**: Non-blocking eval
- **AI-Powered**: Gemini as evaluator
- **Complete Logging**: Full I/O capture
- **Actionable Feedback**: Specific improvements

### 5. Extensibility

- **Easy Agent Addition**: Follow sub-agent pattern
- **New MCP Servers**: Add new microservices
- **Custom Tools**: Extend tool catalog
- **Pluggable LLMs**: Change AI providers

## 📊 Performance Characteristics

### Response Times

| Operation | Typical Time |
|-----------|-------------|
| Query Rewriting | 100-300ms |
| Routing | 50-150ms |
| Mail Agent | 500-2000ms |
| Calendar Agent | 300-1500ms |
| Expense Agent | 100-500ms |
| Evaluation | Async (0ms blocking) |

### Resource Usage

- **Memory**: ~200MB base + ~50MB per agent
- **CPU**: Moderate (Gemini API calls dominate)
- **Network**: Depends on API usage
- **Storage**: Minimal (SQLite for expenses, PostgreSQL for evals)

### Scalability

- **Horizontal**: MCP servers can scale independently
- **Vertical**: Increase Gemini rate limits
- **Queue**: Redis handles high throughput
- **Database**: PostgreSQL supports millions of rows

## 🧪 Testing & Quality

### Automated Evaluation

- Every agent response evaluated
- Pass/fail tracking
- Improvement suggestions
- Performance metrics

### Categories Tracked

1. **Mail**: Email operations
2. **Calendar**: Event management
3. **Expense Tracker**: Financial tracking
4. **Router**: Categorization accuracy

### Metrics Collected

- Execution time
- Success/failure rate
- Average score
- Error patterns
- Improvement trends

## 🔧 Development Workflow

### Setup

```bash
# 1. Clone repository
git clone <repo>

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r agent/requirements.txt
pip install -r eval_server/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Setup OAuth
# Place oauth-creds.json in agent/ directory

# 6. Start services
# Terminal 1: MCP Servers
./start_mcp_servers.sh

# Terminal 2: Eval Server
python -m eval_server.main

# Terminal 3: Eval Consumer
python start_eval_consumer.py

# Terminal 4: Main App
python -m agent.main
```

### Adding a New Agent

1. **Create Agent File**: `agent/agents/new_agent.py`
2. **Create MCP Server**: `agent/mcp_servers/new_mcp/server.py`
3. **Add Category**: Update `agent/constants/__init__.py`
4. **Update Router**: Add category to prompt
5. **Create Tool**: Add to `agent/agents/sub_agent_tools.py`
6. **Test**: Run with sample queries

## 🎯 Use Cases

### Personal Productivity

- "Show me unread emails from today"
- "Schedule a meeting tomorrow at 3 PM"
- "What did I spend on groceries this month?"
- "Delete emails older than 6 months"

### Calendar Management

- "What's on my calendar next week?"
- "Move tomorrow's 2 PM meeting to 4 PM"
- "Find a free slot for a 1-hour meeting"
- "Cancel all meetings on Friday"

### Expense Tracking

- "Add $50 expense for lunch"
- "Show me my spending breakdown"
- "How much did I spend in October?"
- "Set a budget of $1000 for dining"

### Multi-Step Tasks

- "Check emails, schedule a meeting with John, and add travel expense"
- "What meetings do I have today and have I spent more than $100?"

## 🏆 Technical Highlights

### 1. LangGraph State Machine

- **Deterministic Routing**: Predictable flows
- **Conditional Edges**: Dynamic path selection
- **State Persistence**: Context maintenance
- **Error Recovery**: Graceful handling

### 2. MCP Microservices

- **Service Isolation**: Independent deployment
- **Language Agnostic**: Any language can implement
- **HTTP Transport**: Universal protocol
- **Auto-Discovery**: Tools discovered at runtime

### 3. Supervisor Pattern

- **Centralized Control**: Single point of coordination
- **Delegate Authority**: Sub-agents are autonomous
- **History Management**: Shared context
- **Tool Orchestration**: Unified execution

### 4. Event-Driven Evaluation

- **Non-Blocking**: Zero impact on user experience
- **Scalable**: Queue handles any load
- **Reliable**: Redis ensures delivery
- **Insightful**: Complete I/O logging

## 📝 Project Structure

```
personal-assistant/
├── agent/                          # Main agent system
│   ├── agents/                     # Agent implementations
│   │   ├── master.py              # Supervisor agent
│   │   ├── router_agent.py        # Query router
│   │   ├── query_rewriter.py      # Query enhancement
│   │   ├── mail_agent.py          # Mail sub-agent
│   │   ├── calendar_agent.py      # Calendar sub-agent
│   │   ├── expense_tracker_agent.py # Expense sub-agent
│   │   └── sub_agent_tools.py     # Tool definitions
│   ├── mcp_servers/               # MCP server implementations
│   │   ├── orchestrator.py        # Connection pool
│   │   ├── mail_mcp/              # Mail microservice
│   │   ├── calender_mcp/          # Calendar microservice
│   │   └── expense_tracker_mcp/   # Expense microservice
│   ├── schema/                    # LangGraph schemas
│   │   ├── init_assistant_graph.py # Main graph builder
│   │   └── init_resume_agent_graph.py # Resume subgraph
│   ├── states/                    # State definitions
│   │   └── assistant_state.py     # Main state schema
│   ├── prompts/                   # System prompts
│   ├── eval_queue/                # Evaluation system
│   │   ├── publisher.py           # Event publisher
│   │   ├── consumer.py            # Event consumer
│   │   ├── gemini_evaluator.py    # AI evaluator
│   │   └── config.py              # Queue config
│   ├── clients/                   # External clients
│   │   ├── gemini_client.py       # Gemini wrapper
│   │   ├── google.py              # Google APIs
│   │   └── ollama_client.py       # Local LLM
│   ├── constants/                 # Configuration
│   ├── main.py                    # TUI application
│   └── requirements.txt           # Dependencies
├── eval_server/                   # Evaluation storage
│   ├── main.py                    # FastAPI server
│   ├── database.py                # PostgreSQL connection
│   ├── models.py                  # Pydantic models
│   └── requirements.txt           # Dependencies
├── start_eval_consumer.py         # Consumer launcher
└── EVAL_SETUP.md                  # Evaluation docs
```

## 🌟 Innovation Highlights

### 1. Hybrid LLM Strategy

- **Gemini**: Complex reasoning & tool calling
- **Ollama (Llama3)**: Fast, local routing
- **Cost Optimization**: Right model for right task

### 2. Zero-Latency Evaluation

- Traditional: Block on evaluation
- This System: Immediate response + async eval
- User Experience: No waiting

### 3. MCP for Tool Integration

- Traditional: Hardcoded integrations
- This System: Discoverable, versioned tools
- Extensibility: Add services without code changes

### 4. Supervisor + Specialists

- Traditional: Single agent does everything
- This System: Expert agents for each domain
- Quality: Domain-specific optimization

## 🔮 Future Enhancements

### Planned Features

1. **Voice Interface**: Speech-to-text integration
2. **Multi-User**: Authentication & user isolation
3. **Slack/Teams Integration**: Work chat connectivity
4. **Mobile App**: iOS/Android clients
5. **Analytics Dashboard**: Web UI for evaluations
6. **Custom Workflows**: User-defined automations
7. **AI Training**: Fine-tune on evaluation data
8. **Cost Tracking**: Monitor API usage
9. **Offline Mode**: Local-only operation
10. **Plugin System**: Third-party extensions

### Scalability Roadmap

1. **Kubernetes Deployment**: Container orchestration
2. **Load Balancing**: Multiple agent instances
3. **Caching Layer**: Redis for responses
4. **CDN**: Static asset delivery
5. **Monitoring**: Prometheus + Grafana

## 📚 Learning Outcomes

This project demonstrates:

1. **LangChain/LangGraph**: Production-grade agent systems
2. **Multi-Agent Orchestration**: Supervisor pattern
3. **MCP Protocol**: Microservice architecture for AI
4. **Event-Driven Architecture**: Async processing
5. **API Integration**: Google services (Gmail, Calendar)
6. **Database Design**: PostgreSQL + SQLite
7. **TUI Development**: Terminal user interfaces
8. **OAuth 2.0**: Secure authentication
9. **Queue Systems**: Redis for async tasks
10. **Evaluation Systems**: AI-powered quality assurance

## 🤝 Contributing

Contributions welcome! Areas of interest:

- New agent implementations
- Additional MCP servers
- UI improvements
- Performance optimizations
- Documentation
- Testing frameworks

## 📄 License

MIT License - See LICENSE file for details

## 👨‍💻 Author

Rakesh Reddy
- Building production-ready AI agent systems
- Exploring multi-agent architectures
- Implementing evaluation-driven development

---

**Built with ❤️ using LangChain, LangGraph, Gemini, and MCP**

*This project showcases modern AI engineering practices: multi-agent systems, microservice architecture, event-driven evaluation, and production-ready code quality.*

