"""
Event consumer - Listens to Redis queue and evaluates agent responses
"""
import redis
import json
import asyncio
import httpx
import time
from typing import Dict, Any

from .config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    EVAL_QUEUE_NAME, EVAL_SERVER_URL
)
from .gemini_evaluator import GeminiEvaluator


# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# Create evaluator
evaluator = GeminiEvaluator()


async def process_eval_event(event: Dict[str, Any]) -> None:
    """
    Process a single eval event:
    1. Get evaluation from Gemini
    2. Store result in eval server
    """
    try:
        # Extract event data
        agent_name = event.get("agent_name")
        query = event.get("query")
        response = event.get("response")
        category = event.get("category")
        metadata = event.get("metadata", {})
        
        print(f"📊 Evaluating: {agent_name} - {category}")
        
        # Get evaluation from Gemini
        start_time = time.time()
        evaluation = await evaluator.evaluate(
            query=query,
            response=response,
            agent_name=agent_name,
            category=category,
            metadata=metadata
        )
        execution_time = (time.time() - start_time) * 1000
        
        # Ensure query and response are strings
        query_str = str(query) if not isinstance(query, str) else query
        response_str = str(response) if not isinstance(response, str) else response
        
        # Prepare data for eval server
        eval_result = {
            "test_name": f"{agent_name}_{category}_{int(time.time())}",
            "category": category,
            "status": evaluation["status"],
            "score": evaluation["score"],
            "execution_time_ms": execution_time,
            "user_input": query_str,  # Full user query as string
            "agent_output": response_str,  # Full agent response as string
            "justification": evaluation["justification"],  # Gemini's reasoning
            "improvements": evaluation["improvements"],  # Gemini's suggestions
            "error_message": None if evaluation["status"] != "error" else evaluation["justification"],
            "metadata": {
                "agent_name": agent_name,
                **metadata
            }
        }
        
        # Send to eval server
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                server_response = await client.post(
                    f"{EVAL_SERVER_URL}/evals",
                    json=eval_result
                )
                
                if server_response.status_code == 200:
                    status_emoji = "✅" if evaluation["status"] == "pass" else "❌"
                    print(f"{status_emoji} Evaluated & Stored: {agent_name} - {evaluation['status']}")
                else:
                    print(f"⚠️  Failed to store eval result: {server_response.status_code}")
                    print(f"   Response: {server_response.text}")
            except httpx.TimeoutException:
                print(f"⚠️  Timeout storing eval result for {agent_name}")
            except httpx.HTTPError as e:
                print(f"⚠️  HTTP error storing eval result: {e}")
    
    except Exception as e:
        print(f"❌ Error processing eval event: {e}")
        import traceback
        traceback.print_exc()


async def consume_eval_queue():
    """
    Continuously consume events from Redis queue
    """
    print(f"🎧 Eval consumer started - listening to '{EVAL_QUEUE_NAME}'")
    print(f"📡 Eval server: {EVAL_SERVER_URL}")
    
    while True:
        try:
            # Block and wait for event (with 1 second timeout)
            result = redis_client.blpop(EVAL_QUEUE_NAME, timeout=1)
            
            if result:
                _, event_data = result
                event = json.loads(event_data)
                
                # Process event asynchronously
                await process_eval_event(event)
            
            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n👋 Stopping eval consumer...")
            break
        
        except Exception as e:
            print(f"❌ Consumer error: {e}")
            await asyncio.sleep(1)  # Wait before retrying


def start_eval_consumer():
    """
    Start the eval consumer (blocking)
    Run this in a separate process or terminal
    """
    try:
        asyncio.run(consume_eval_queue())
    except KeyboardInterrupt:
        print("\n✅ Eval consumer stopped")


if __name__ == "__main__":
    # Can run directly: python -m agent.eval_queue.consumer
    start_eval_consumer()

