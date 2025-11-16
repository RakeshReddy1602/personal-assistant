# Simple Eval Server

A minimal FastAPI server for storing evaluation results in Supabase using direct PostgreSQL connection.

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r eval_server/requirements.txt
```

### 2. Configure Supabase

Create `eval_server/.env`:

```env
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.kvfllvtachbppikzrnaa.supabase.co:5432/postgres
PORT=8001
```

Get your DATABASE_URL from:
- Supabase Dashboard → Project Settings → Database → Connection String → Direct Connection

### 3. Start Server

```bash
# From project root
python -m eval_server.main

# Or
cd eval_server
python main.py
```

Server runs on: **http://localhost:8001**

API Docs: **http://localhost:8001/docs**

## 📡 API Endpoints

### POST /evals - Insert Result

```bash
curl -X POST http://localhost:8001/evals \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "router_mail_001",
    "category": "router",
    "status": "passed",
    "score": 1.0,
    "execution_time_ms": 125.5,
    "error_message": null,
    "metadata": {"accuracy": 1.0}
  }'
```

### GET /evals - Fetch Results

```bash
# Get all results
curl http://localhost:8001/evals

# Filter by category
curl http://localhost:8001/evals?category=router

# Filter by status
curl http://localhost:8001/evals?status=passed

# Limit results
curl http://localhost:8001/evals?limit=50
```

### GET /stats - Get Statistics

```bash
curl http://localhost:8001/stats
```

### GET /health - Health Check

```bash
curl http://localhost:8001/health
```

## 📊 Database Schema

```sql
CREATE TABLE eval_results (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    score DECIMAL(5, 4) DEFAULT 0.0,
    execution_time_ms DECIMAL(10, 2) DEFAULT 0.0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Table is created automatically on first run.

## 🧪 Testing

### Python

```python
import httpx

# Insert result
response = httpx.post("http://localhost:8001/evals", json={
    "test_name": "test_example",
    "category": "router",
    "status": "passed",
    "score": 0.95,
    "execution_time_ms": 100.0,
    "metadata": {"details": "test passed"}
})
print(response.json())

# Fetch results
response = httpx.get("http://localhost:8001/evals?category=router")
print(response.json())
```

## 🔧 Simple & Clean

- ✅ No ORM - Direct PostgreSQL
- ✅ No migrations - Auto-creates table
- ✅ Minimal dependencies
- ✅ Just 2 main endpoints
- ✅ Works with Supabase out of the box

