"""
Master Supervisor Agent: Coordinates sub-agents using LangChain's supervisor pattern
"""
import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.states.assistant_state import AssistantState, Message
from agent.prompts.master_agent_prompts.prompt import MASTER_AGENT_SYSTEM_PROMPT
from agent.agents.sub_agent_tools import SUB_AGENT_TOOLS

load_dotenv()


# --- History helpers (cap at 40) ---
def push_history(state: AssistantState, role: str, content: str, name: Optional[str] = None) -> AssistantState:
    history: List[Message] = list(state.get("history", []))  # type: ignore[assignment]
    msg: Message = {"role": role, "content": content, "name": name}  # type: ignore
    history.append(msg)
    # cap to last 40
    if len(history) > 40:
        history = history[-40:]
    state["history"] = history
    return state


def get_recent_history(state: AssistantState, limit: int = 40) -> List[Message]:
    history: List[Message] = list(state.get("history", []))  # type: ignore[assignment]
    if limit and len(history) > limit:
        return history[-limit:]
    return history


def _build_langchain_messages_from_history(
    history: List[Message],
    query: str,
    system_prompt: str
) -> List[Any]:
    """
    Build LangChain message list from history.
    """
    messages = []
    
    # Add system prompt
    messages.append(SystemMessage(content=system_prompt))
    
    # Process history (last 40 messages)
    for msg in (history or [])[-40:]:
        role = msg.get("role")
        content = msg.get("content", "")
        
        # Convert content to string if needed
        if not isinstance(content, str):
            try:
                content = json.dumps(content, ensure_ascii=False)
            except Exception:
                content = str(content)
        
        if role == "user":
            if content:  # Skip empty user messages
                messages.append(HumanMessage(content=content))
        
        elif role in ("assistant", "model"):
            # Check if this is a function call
            function_call = msg.get("function_call")
            if function_call:
                # This is a tool call from the assistant
                tool_calls = [{
                    "name": function_call["name"],
                    "args": function_call.get("args", {}),
                    "id": msg.get("tool_call_id", function_call["name"])
                }]
                ai_msg = AIMessage(content="", tool_calls=tool_calls)
                messages.append(ai_msg)
            elif content:
                # Regular assistant message
                messages.append(AIMessage(content=content))
        
        elif role == "tool":
            # Tool result
            tool_name = msg.get("name") or msg.get("tool_name", "tool")
            tool_call_id = msg.get("tool_call_id", tool_name)
            
            # Get structured response if available
            structured_response = msg.get("structured_response")
            if structured_response is None:
                try:
                    structured_response = json.loads(content)
                except Exception:
                    structured_response = {"content": content}
            
            # Convert to string for ToolMessage
            tool_content = json.dumps(structured_response) if isinstance(structured_response, dict) else str(structured_response)
            
            messages.append(ToolMessage(
                content=tool_content,
                tool_call_id=tool_call_id,
                name=tool_name
            ))
    
    # Add current query
    if query:
        messages.append(HumanMessage(content=query))
    
    return messages


async def handle_master(state: AssistantState) -> AssistantState:
    """
    Master Supervisor Agent using LangChain's multi-agent pattern.
    
    The supervisor coordinates three specialized sub-agents:
    1. Mail Agent - Handles all email operations
    2. Calendar Agent - Manages calendar and scheduling
    3. Expense Agent - Tracks expenses and budgets
    
    The supervisor delegates tasks to appropriate sub-agents based on user queries.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")
    
    if not api_key:
        state["response"] = "Error: GEMINI_API_KEY is not set."
        return state
    
    try:
        # Create LangChain Gemini model with sub-agent tools
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        # Bind sub-agent tools to the supervisor
        llm_with_tools = llm.bind_tools(SUB_AGENT_TOOLS)
        
        # Build initial messages from history and query
        query = state.get("query_to_be_served", "")
        history = state.get("history", [])
        
        # Enhanced system prompt for supervisor
        supervisor_prompt = MASTER_AGENT_SYSTEM_PROMPT
        
        messages = _build_langchain_messages_from_history(
            history,
            query,
            supervisor_prompt
        )
        
        # Tool calling loop
        MAX_ITERATIONS = 20
        iterations = 0
        
        while iterations < MAX_ITERATIONS:
            iterations += 1
            
            # Invoke the supervisor
            response = await llm_with_tools.ainvoke(messages)
            
            # Check if supervisor wants to delegate to sub-agents
            if not response.tool_calls:
                # No delegation needed; return final response
                final_text = response.content
                if final_text:
                    state["response"] = final_text
                    return state
                state["response"] = "I processed your request."
                return state
            
            # Add AI message with tool calls to conversation
            messages.append(response)
            
            # Execute each sub-agent tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", tool_name)
                
                # Store supervisor's delegation in history
                state = push_history(
                    state,
                    "assistant",
                    f"Delegating to {tool_name}",
                    name=None
                )
                if state["history"]:
                    state["history"][-1]["function_call"] = {"name": tool_name, "args": tool_args}  # type: ignore
                    state["history"][-1]["tool_call_id"] = tool_call_id  # type: ignore
                
                # Execute sub-agent tool
                try:
                    # Find and execute the tool
                    tool_func = None
                    for tool in SUB_AGENT_TOOLS:
                        if tool.name == tool_name:
                            tool_func = tool
                            break
                    
                    if tool_func:
                        # Execute the sub-agent
                        result = await tool_func.ainvoke(tool_args)
                        result_content = result if isinstance(result, str) else json.dumps(result)
                    else:
                        result_content = json.dumps({"error": f"Unknown tool: {tool_name}"})
                except Exception as e:
                    result_content = json.dumps({"error": str(e)})
                    print(f"Error calling sub-agent {tool_name}: {e}")
                
                # Create ToolMessage for the supervisor
                tool_message = ToolMessage(
                    content=result_content,
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                messages.append(tool_message)
                
                # Store sub-agent result in history
                state = push_history(
                    state,
                    "tool",
                    result_content,
                    name=tool_name
                )
                if state["history"]:
                    try:
                        state["history"][-1]["structured_response"] = json.loads(result_content)  # type: ignore
                    except Exception:
                        state["history"][-1]["structured_response"] = {"content": result_content}  # type: ignore
                    state["history"][-1]["tool_call_id"] = tool_call_id  # type: ignore
        
        # Max iterations reached
        state["response"] = "I processed your request but reached the iteration limit."
        return state
        
    except Exception as e:
        state["response"] = f"Error: {str(e)}"
        import traceback
        traceback.print_exc()
        return state
