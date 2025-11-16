"""Simple FastAPI Eval Server"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import os
import json
from dotenv import load_dotenv

from .database import get_db_connection, get_db_cursor, init_db
from .models import EvalResultCreate, EvalResultResponse

load_dotenv()

app = FastAPI(
    title="Eval Server",
    description="Simple server for storing evaluation results",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    print("🚀 Starting Eval Server...")
    init_db()
    print("✅ Server ready!")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Eval Server",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """Health check"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/evals", response_model=EvalResultResponse)
def create_eval_result(result: EvalResultCreate):
    """Insert a new eval result"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            insert_sql = """
            INSERT INTO eval_results 
                (test_name, category, status, score, execution_time_ms, error_message, metadata)
            VALUES 
                (%(test_name)s, %(category)s, %(status)s, %(score)s, %(execution_time_ms)s, %(error_message)s, %(metadata)s::jsonb)
            RETURNING id, test_name, category, status, score, execution_time_ms, error_message, metadata, created_at
            """
            
            cursor.execute(insert_sql, {
                'test_name': result.test_name,
                'category': result.category,
                'status': result.status,
                'score': result.score,
                'execution_time_ms': result.execution_time_ms,
                'error_message': result.error_message,
                'metadata': json.dumps(result.metadata)  # Convert dict to JSON string
            })
            
            row = cursor.fetchone()
            return dict(row)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert eval result: {str(e)}")


@app.get("/evals", response_model=List[EvalResultResponse])
def get_eval_results(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Fetch eval results with optional filters"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Build query
            query = "SELECT * FROM eval_results WHERE 1=1"
            params = {}
            
            if category:
                query += " AND category = %(category)s"
                params['category'] = category
            
            if status:
                query += " AND status = %(status)s"
                params['status'] = status
            
            query += " ORDER BY created_at DESC LIMIT %(limit)s"
            params['limit'] = limit
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch eval results: {str(e)}")


@app.get("/stats")
def get_stats():
    """Get evaluation statistics"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM eval_results")
            total = cursor.fetchone()['total']
            
            # By status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM eval_results 
                GROUP BY status
            """)
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count, AVG(score) as avg_score
                FROM eval_results 
                GROUP BY category
            """)
            by_category = {
                row['category']: {
                    'count': row['count'],
                    'avg_score': float(row['avg_score']) if row['avg_score'] else 0.0
                }
                for row in cursor.fetchall()
            }
            
            # Average score
            cursor.execute("SELECT AVG(score) as avg_score FROM eval_results")
            avg_score = cursor.fetchone()['avg_score']
            
            return {
                "total_results": total,
                "by_status": by_status,
                "by_category": by_category,
                "average_score": float(avg_score) if avg_score else 0.0
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(
        "eval_server.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

