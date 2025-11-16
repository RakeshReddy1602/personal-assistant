"""
Event publisher - Agents use this to push eval events to Redis queue
"""
import redis
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, EVAL_QUEUE_NAME


# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)


def publish_eval_event(
    agent_name: str,
    query: Union[str, Any],
    response: Union[str, Any],
    category: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish an eval event to Redis queue for async evaluation
    
    Args:
        agent_name: Name of the agent (mail_agent, calendar_agent, etc.)
        query: User query that was processed
        response: Agent's response
        category: Category of the task (mail, calendar, expense, etc.)
        metadata: Additional metadata (tools used, execution time, etc.)
    
    Returns:
        bool: True if successfully published
    """
    try:
        # Ensure response is a string (handle various types)
        if not isinstance(response, str):
            if isinstance(response, (dict, list)):
                response = json.dumps(response)
            else:
                response = str(response)
        
        event = {
            "agent_name": agent_name,
            "query": str(query),  # Ensure query is also string
            "response": response,
            "category": category,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Push to Redis queue
        redis_client.rpush(EVAL_QUEUE_NAME, json.dumps(event))
        
        return True
    
    except Exception as e:
        # Don't fail the main agent flow if eval publishing fails
        print(f"⚠️  Failed to publish eval event: {e}")
        return False


def get_queue_length() -> int:
    """Get current queue length"""
    try:
        return redis_client.llen(EVAL_QUEUE_NAME)
    except Exception:
        return 0


def clear_queue() -> bool:
    """Clear the eval queue (for testing)"""
    try:
        redis_client.delete(EVAL_QUEUE_NAME)
        return True
    except Exception as e:
        print(f"Failed to clear queue: {e}")
        return False

