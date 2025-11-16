"""
Configuration for eval queue
"""
import os
from dotenv import load_dotenv

load_dotenv()

def _get_env_or_raise(key: str, cast_func=None, required=True):
    value = os.getenv(key)
    if value is None or value == "":
        raise RuntimeError(f"Environment variable '{key}' is required but not set!")
    return cast_func(value) if cast_func else value

# Redis configuration
REDIS_HOST = _get_env_or_raise("REDIS_HOST")

REDIS_PORT = _get_env_or_raise("REDIS_PORT", int)
REDIS_DB = _get_env_or_raise("REDIS_DB", int)
REDIS_PASSWORD = _get_env_or_raise("REDIS_PASSWORD")

# Queue name
EVAL_QUEUE_NAME = _get_env_or_raise("EVAL_QUEUE_NAME")

# Eval server
EVAL_SERVER_URL = _get_env_or_raise("EVAL_SERVER_URL")

# Gemini for evaluation
GEMINI_API_KEY = _get_env_or_raise("GEMINI_API_KEY")
GEMINI_EVAL_MODEL = _get_env_or_raise("GEMINI_EVAL_MODEL")

