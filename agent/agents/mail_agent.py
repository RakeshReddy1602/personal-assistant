"""
Mail Sub-Agent: Handles all email-related operations
Connects directly to Mail MCP server
"""
import json
import os
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
from fastmcp import Client as MCPClient

from agent.prompts.mail_agent_prompts.prompt import MAIL_AGENT_PROMPT

load_dotenv()


# Mail MCP Server Configuration
MAIL_MCP_URL = os.getenv("MAIL_MCP_URL")

if not MAIL_MCP_URL:
    raise ValueError("MAIL_MCP_URL is not set")


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


async def execute_mail_agent(query: str) -> str:
    """
    Execute mail sub-agent with direct connection to Mail MCP server.
    
    Args:
        query: User's email-related query
        
    Returns:
        Response from the mail agent
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

    if not model_name:
        return "Error: GEMINI_MODEL is not set."

    if not api_key:
        return "Error: GEMINI_API_KEY is not set."
    
    # Connect to Mail MCP server
    mail_client = MCPClient(MAIL_MCP_URL)
    
    try:
        async with mail_client:
            # Get mail tools from MCP server
            tools = await mail_client.list_tools()
            print(f"Mail agent: Connected to Mail MCP, {len(tools)} tools available")
            
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
                SystemMessage(content=MAIL_AGENT_PROMPT),
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
                    return response.content if response.content else "Task completed."
                
                # Add AI response to messages
                messages.append(response)
                
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    tool_call_id = tool_call.get("id", tool_name)
                    
                    # Execute tool via MCP client
                    try:
                        result = await mail_client.call_tool(tool_name, tool_args)
                        
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
            
            return "Mail operation completed but reached iteration limit."
            
    except Exception as e:
        return f"Error in mail agent: {str(e)}"
