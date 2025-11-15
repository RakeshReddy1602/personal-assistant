import asyncio
from dotenv import load_dotenv

from agent.schema.init_assistant_graph import build_graph
from agent.states.assistant_state import AssistantState
from agent.agents.master import push_history


async def main() -> None:
    load_dotenv()
    
    # Initialize graph and state (single state for entire app)
    graph = build_graph()
    state: AssistantState = {
        "category_to_be_served": "",
        "query_to_be_served": "",
        "history": [],
        "response": "",
    }

    print("=" * 70)
    print("  Assistant ready!")
    print("=" * 70)
    print()
    print("Commands:")
    print("  • Type your query to chat")
    print("  • 'exit' - quit the assistant")
    print("  • 'clear' - reset conversation history")
    print("  • 'history' - view conversation history")
    print()
    print("Available Tools: Mail, Calendar, Expense Tracker")
    print()
    
    while True:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "You: "
            )
            user_input = user_input.strip()
            
            if not user_input:
                continue
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if user_input.lower() == "state":
                print(state)
                continue
            if user_input.lower() == "clear":
                state["history"] = []
                state["query_to_be_served"] = ""
                state["category_to_be_served"] = ""
                state["response"] = ""
                print("Cleared history.")
                continue
            if user_input.lower() == "history":
                print("History:")
                for m in state.get("history", []):
                    print(f"{m.get('role','user')}: {m.get('content','')}")
                continue

            # Push user message into history and set query
            state = push_history(state, "user", user_input)
            state["query_to_be_served"] = user_input

            # Run through the graph asynchronously
            # The graph will route through: query_rewriter -> router -> (master or resume)
            state = await graph.ainvoke(state)  # type: ignore[assignment]
            
            reply = (state.get("response") or "").strip()
            if not reply:
                reply = "I processed your request."
            print(f"Assistant: {reply}")
            
            # Add assistant reply to history (state persists across iterations)
            state = push_history(state, "assistant", reply)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            continue


if __name__ == "__main__":
    asyncio.run(main())


