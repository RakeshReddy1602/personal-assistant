"""
Decorator for automatic eval event publishing
"""
import functools
import time
from typing import Any, Callable

from .publisher import publish_eval_event


def auto_eval(agent_name: str, category: str):
    """
    Decorator to automatically publish eval events for agent functions
    
    Usage:
        @auto_eval(agent_name="mail_agent", category="mail")
        async def execute_mail_agent(query: str) -> str:
            # ... agent logic
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Get query (assume first arg is query)
            query = args[0] if args else kwargs.get("query", "")
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Publish eval event (non-blocking)
            try:
                publish_eval_event(
                    agent_name=agent_name,
                    query=str(query),
                    response=str(result),
                    category=category,
                    metadata={
                        "execution_time_ms": execution_time,
                        "function_name": func.__name__
                    }
                )
            except Exception as e:
                print(f"⚠️  Failed to publish eval: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            query = args[0] if args else kwargs.get("query", "")
            
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            try:
                publish_eval_event(
                    agent_name=agent_name,
                    query=str(query),
                    response=str(result),
                    category=category,
                    metadata={
                        "execution_time_ms": execution_time,
                        "function_name": func.__name__
                    }
                )
            except Exception as e:
                print(f"⚠️  Failed to publish eval: {e}")
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


import asyncio

