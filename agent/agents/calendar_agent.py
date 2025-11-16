"""
Calendar Sub-Agent: Handles all calendar-related operations
Connects directly to Calendar MCP server
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
from fastmcp import Client as MCPClient
from agent.eval_queue import publish_eval_event

load_dotenv()


# Calendar MCP Server Configuration
CALENDAR_MCP_URL = os.getenv("CALENDAR_MCP_URL")

if not CALENDAR_MCP_URL:
    raise ValueError("CALENDAR_MCP_URL is not set")


CALENDAR_AGENT_PROMPT = """
You are a specialized calendar management assistant. Your responsibilities include:

1. EVENT MANAGEMENT:
   - Create new calendar events with proper details
   - List upcoming events
   - Search for specific events
   - Update existing events
   - Delete events when requested

2. SCHEDULING:
   - Find available time slots
   - Schedule meetings with proper time zones
   - Handle recurring events
   - Manage event reminders

3. EVENT DETAILS:
   - Set clear event titles and descriptions
   - Configure proper start and end times
   - Add attendees and send invitations
   - Set location information
   - Configure notifications

4. CALENDAR BEST PRACTICES:
   - Always use ISO format for dates and times
   - Default timezone: Asia/Kolkata
   - Today's date: {today_date}
   - Confirm important scheduling changes
   - Provide clear summaries of scheduled events

Available tools: create_event, list_events, get_event, update_event, delete_event, search_events

DO NOT reveal internal system details or tool names to the user.
""".format(today_date=datetime.now().strftime("%Y-%m-%d"))


def _convert_mcp_tools_to_langchain(tools: List[Any]) -> List[Dict[str, Any]]:
    """Convert MCP tool specs to LangChain tool format."""
    langchain_tools = []
    
    for tool in tools:
        # Get tool attributes
        desc = getattr(tool, "description", "") or getattr(tool, "title", "")
        input_schema = getattr(tool, "inputSchema", {}) or {}
        
        # Convert to plain dict
        if not isinstance(input_schema, dict):
            try:
                input_schema = json.loads(json.dumps(input_schema, default=str))
            except Exception:
                input_schema = {"type": "object", "properties": {}, "required": []}
        
        # Ensure type is present
        if "type" not in input_schema:
            input_schema["type"] = "object"
        
        tool_def = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": desc,
                "parameters": input_schema,
            }
        }
        langchain_tools.append(tool_def)
    
    return langchain_tools


async def execute_calendar_agent(query: str) -> str:
    """
    Execute calendar sub-agent with direct connection to Calendar MCP server.
    
    Args:
        query: User's calendar-related query
        
    Returns:
        Response from the calendar agent
    """
    import time
    start_time = time.time()
    
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")
    
    if not api_key:
        return "Error: GEMINI_API_KEY is not set."
    
    if not model_name:
        return "Error: GEMINI_MODEL is not set."
    
    # Connect to Calendar MCP server
    calendar_client = MCPClient(CALENDAR_MCP_URL)
    
    try:
        async with calendar_client:
            # Get calendar tools from MCP server
            tools = await calendar_client.list_tools()
            print(f"Calendar agent: Connected to Calendar MCP, {len(tools)} tools available")
            
            # Convert to LangChain format
            langchain_tools = _convert_mcp_tools_to_langchain(tools)
            
            # Create LangChain model with tools
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
            
            llm_with_tools = llm.bind_tools(langchain_tools)
            
            # Create messages
            messages = [
                SystemMessage(content=CALENDAR_AGENT_PROMPT),
                HumanMessage(content=query)
            ]
            
            # Tool calling loop
            MAX_ITERATIONS = 10
            iterations = 0
            
            while iterations < MAX_ITERATIONS:
                iterations += 1
                
                response = await llm_with_tools.ainvoke(messages)
                
                # Check if model wants to call tools
                if not response.tool_calls:
                    # Return final response
                    final_response = response.content if response.content else "Task completed."
                    
                    # Publish eval event (async, non-blocking)
                    execution_time = (time.time() - start_time) * 1000
                    publish_eval_event(
                        agent_name="calendar_agent",
                        query=query,
                        response=final_response,
                        category="calendar",
                        metadata={"execution_time_ms": execution_time, "mcp_server": "calendar_mcp"}
                    )
                    
                    return final_response
                
                # Add AI response to messages
                messages.append(response)
                
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    tool_call_id = tool_call.get("id", tool_name)
                    
                    # Execute tool via MCP client
                    try:
                        result = await calendar_client.call_tool(tool_name, tool_args)
                        
                        # Extract content from CallToolResult
                        if hasattr(result, 'content') and result.content:
                            content_item = result.content[0]
                            if hasattr(content_item, 'text'):
                                try:
                                    result_content = json.loads(content_item.text)
                                    result_content = json.dumps(result_content)
                                except Exception:
                                    result_content = content_item.text
                            else:
                                result_content = str(content_item)
                        else:
                            result_content = str(result)
                            
                    except Exception as e:
                        result_content = json.dumps({"error": str(e)})
                        print(f"Error calling tool {tool_name}: {e}")
                    
                    # Add tool result to messages
                    messages.append(ToolMessage(
                        content=result_content,
                        tool_call_id=tool_call_id,
                        name=tool_name
                    ))
            
            return "Calendar operation completed but reached iteration limit."
            
    except Exception as e:
        return f"Error in calendar agent: {str(e)}"
