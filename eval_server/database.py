"""Simple database connection using psycopg2"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")


@contextmanager
def get_db_connection():
    """Get a database connection"""
    connection = psycopg2.connect(DATABASE_URL)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_db_cursor(connection):
    """Get a cursor that returns results as dictionaries"""
    return connection.cursor(cursor_factory=RealDictCursor)


def init_db():
    """Create tables if they don't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS eval_results (
        id SERIAL PRIMARY KEY,
        test_name VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        status VARCHAR(50) NOT NULL,
        score DECIMAL(5, 4) DEFAULT 0.0,
        execution_time_ms DECIMAL(10, 2) DEFAULT 0.0,
        user_input TEXT,
        agent_output TEXT,
        justification TEXT,
        improvements TEXT,
        error_message TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_eval_results_category ON eval_results(category);
    CREATE INDEX IF NOT EXISTS idx_eval_results_status ON eval_results(status);
    CREATE INDEX IF NOT EXISTS idx_eval_results_created_at ON eval_results(created_at DESC);
    """
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute(create_table_sql)
        print("✅ Database tables created successfully")

