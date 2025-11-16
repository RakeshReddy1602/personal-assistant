# Event-Driven Evaluation System

Async evaluation system using **Redis Queue** + **Gemini AI** for zero-latency agent evaluation.

## 🏗️ Architecture

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   Agents    │ ──push──>│ Redis Queue │<─listen─│   Consumer   │
│ (mail, cal, │         │   (async)   │         │   Process    │
│  expense)   │         └─────────────┘         └──────────────┘
└─────────────┘                                         │
      │                                                 │
      │ No latency!                                     ▼
      │                                          ┌──────────────┐
      ▼                                          │    Gemini    │
User gets response                               │  Evaluator   │
immediately                                      └──────────────┘
                                                        │
                                                        ▼
                                                 ┌──────────────┐
                                                 │ Eval Server  │
                                                 │  (Storage)   │
                                                 └──────────────┘
```

## ✨ Features

1. **Zero Latency** - Agents don't wait for evaluation
2. **Gemini Evaluation** - AI-powered quality assessment
3. **3-Part Feedback**:
   - ✅/❌ Pass/Fail status
   - 📝 Justification
   - 💡 Improvement suggestions
4. **Automatic Storage** - Results saved to eval server
5. **Easy Integration** - Simple decorator or manual publishing

## 🚀 Setup

### 1. Install Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### 2. Install Dependencies

```bash
cd /Users/rakeshreddy/learning/AI/personal-assistant
pip install -r agent/requirements.txt
```

### 3. Configure Environment

Add to your `.env`:

```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Eval Server
EVAL_SERVER_URL=http://localhost:8001

# Gemini for Evaluation
GEMINI_API_KEY=your_api_key
GEMINI_EVAL_MODEL=gemini-1.5-flash
```

### 4. Start Services

**Terminal 1 - Eval Server:**
```bash
python -m eval_server.main
```

**Terminal 2 - Eval Consumer:**
```bash
python start_eval_consumer.py
```

**Terminal 3 - Your Main App:**
```bash
python -m agent.main
```

## 📝 Usage

### Method 1: Decorator (Automatic)

```python
from agent.eval_queue.decorator import auto_eval

@auto_eval(agent_name="mail_agent", category="mail")
async def execute_mail_agent(query: str) -> str:
    # Your agent logic
    response = await process_mail_query(query)
    return response
```

### Method 2: Manual Publishing

```python
from agent.eval_queue import publish_eval_event

async def my_agent(query: str) -> str:
    response = await do_work(query)
    
    # Publish eval event (async, non-blocking)
    publish_eval_event(
        agent_name="custom_agent",
        query=query,
        response=response,
        category="custom",
        metadata={"tools_used": ["tool1", "tool2"]}
    )
    
    return response
```

## 🔍 How It Works

### 1. Agent Publishes Event

When an agent completes a task, it pushes an event to Redis queue:

```python
{
    "agent_name": "mail_agent",
    "query": "Show me my unread emails",
    "response": "You have 3 unread emails...",
    "category": "mail",
    "metadata": {"execution_time": 150},
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Consumer Picks Up Event

The consumer process (running separately) picks up the event and sends it to Gemini for evaluation.

### 3. Gemini Evaluates

Gemini analyzes the query and response, providing:

```json
{
    "status": "pass",
    "justification": "Response correctly lists unread emails with clear formatting",
    "improvements": "Could add timestamps and sender names for better context"
}
```

### 4. Results Stored

The evaluation is automatically stored in the eval server database with:
- Pass/fail status
- Score (1.0 for pass, 0.0 for fail)
- Justification
- Improvement suggestions
- Original query/response (truncated)
- Execution time
- Metadata

## 📊 Monitoring

### Check Queue Length

```python
from agent.eval_queue.publisher import get_queue_length

print(f"Pending evaluations: {get_queue_length()}")
```

### View Results

```bash
# Get all eval results
curl http://localhost:8001/evals

# Get stats
curl http://localhost:8001/stats

# Filter by category
curl http://localhost:8001/evals?category=mail&status=pass
```

## 🎯 Example: Integrate into Mail Agent

```python
# agent/agents/mail_agent.py

from agent.eval_queue import publish_eval_event

async def execute_mail_agent(query: str) -> str:
    """Execute mail agent"""
    
    # ... your existing logic ...
    response = await process_mail_request(query)
    
    # Publish eval event (non-blocking, won't slow down response)
    publish_eval_event(
        agent_name="mail_agent",
        query=query,
        response=response,
        category="mail",
        metadata={
            "mcp_server": "mail_mcp",
            "port": 6281
        }
    )
    
    return response
```

## 🧪 Testing

### Test Publishing

```python
from agent.eval_queue import publish_eval_event

publish_eval_event(
    agent_name="test_agent",
    query="What's the weather?",
    response="It's sunny and 72°F",
    category="test",
    metadata={"test": True}
)
```

Check Redis:
```bash
redis-cli
> LLEN agent_evals
> LRANGE agent_evals 0 -1
```

### Monitor Consumer

The consumer prints status messages:
```
📊 Evaluating: mail_agent - mail
✅ Evaluated & Stored: mail_agent - pass
```

## 🔧 Configuration

### Custom Eval Prompt

Edit `gemini_evaluator.py` to customize the evaluation prompt.

### Adjust Redis Queue Name

Change `EVAL_QUEUE_NAME` in `config.py`.

### Change Gemini Model

Set `GEMINI_EVAL_MODEL` in `.env`:
- `gemini-1.5-flash` (fast, cheap)
- `gemini-1.5-pro` (slower, better)

## ⚡ Performance

- **Agent Response Time**: No impact (async publishing)
- **Evaluation Time**: 1-3 seconds per event (Gemini API call)
- **Throughput**: ~100+ evals/minute
- **Storage**: Automatic to PostgreSQL

## 🐛 Troubleshooting

### Queue not processing

1. Check Redis is running: `redis-cli ping`
2. Check consumer is running: Should see "🎧 Eval consumer started"
3. Check queue length: `redis-cli LLEN agent_evals`

### Evaluation errors

1. Check Gemini API key is set
2. Check eval server is running: `curl http://localhost:8001/health`
3. Check consumer logs for errors

### No results in database

1. Check eval server connection: `curl http://localhost:8001/health`
2. Check database connection in eval server
3. Verify results: `curl http://localhost:8001/evals`

## 📚 Files

- `publisher.py` - Publishes events to Redis
- `consumer.py` - Consumes and processes events
- `gemini_evaluator.py` - Gemini-based evaluation logic
- `decorator.py` - Auto-eval decorator
- `config.py` - Configuration

## 🎉 Benefits

✅ **No Latency** - Users get immediate responses
✅ **AI-Powered** - Gemini evaluates quality
✅ **Actionable Feedback** - Specific improvements
✅ **Automatic** - Just add decorator or one line
✅ **Scalable** - Queue handles any volume
✅ **Observable** - Track in eval server dashboard

