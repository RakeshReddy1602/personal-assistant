"""
Configuration for eval queue
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Queue name
EVAL_QUEUE_NAME = "agent_evals"

# Eval server
EVAL_SERVER_URL = os.getenv("EVAL_SERVER_URL", "http://localhost:8001")

# Gemini for evaluation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EVAL_MODEL = os.getenv("GEMINI_EVAL_MODEL", "gemini-2.5-flash-lite")

