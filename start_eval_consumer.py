#!/usr/bin/env python3
"""
Start the eval consumer process

This listens to the Redis queue and processes eval events.
Run this in a separate terminal alongside your main application.
"""
from agent.eval_queue.consumer import start_eval_consumer

if __name__ == "__main__":
    print("=" * 60)
    print("  EVAL CONSUMER - Event-Driven Evaluation System")
    print("=" * 60)
    print()
    print("This process will:")
    print("  1. Listen to Redis queue for eval events")
    print("  2. Evaluate responses using Gemini")
    print("  3. Store results in eval server")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    start_eval_consumer()

