"""
Sub-Agent Tools: Wraps sub-agents as LangChain tools for the master supervisor

Each sub-agent independently connects to its own MCP server:
- Mail agent → Mail MCP (port 6281)
- Calendar agent → Calendar MCP (port 6282)
- Expense agent → Direct implementation (no MCP yet)
"""
from langchain_core.tools import tool

from agent.agents.mail_agent import execute_mail_agent
from agent.agents.calendar_agent import execute_calendar_agent
from agent.agents.expense_tracker_agent import execute_expense_agent


@tool
async def mail_agent_tool(query: str) -> str:
    """
    Delegate email-related tasks to the specialized mail agent.
    
    The mail agent independently connects to the Mail MCP server and handles
    all email operations with full autonomy.
    
    Use this tool for:
    - Reading, searching, and summarizing emails
    - Sending emails with proper formatting
    - Managing emails (mark read/unread, delete)
    - Handling email attachments
    - Any email-related operations
    
    Args:
        query: The email-related task or question from the user
        
    Returns:
        Response from the mail agent with task results
        
    Examples:
        - "Read my unread emails"
        - "Send an email to john@example.com about the meeting"
        - "Mark the email from Sarah as read"
        - "What are the attachments in the latest email?"
    """
    return await execute_mail_agent(query)


@tool
async def calendar_agent_tool(query: str) -> str:
    """
    Delegate calendar and scheduling tasks to the specialized calendar agent.
    
    The calendar agent independently connects to the Calendar MCP server and
    handles all calendar operations with full autonomy.
    
    Use this tool for:
    - Creating new calendar events
    - Listing upcoming events
    - Searching for specific events
    - Updating or deleting events
    - Managing meeting schedules
    - Any calendar-related operations
    
    Args:
        query: The calendar-related task or question from the user
        
    Returns:
        Response from the calendar agent with task results
        
    Examples:
        - "Schedule a meeting tomorrow at 2 PM"
        - "What are my events for next week?"
        - "Create an event for the project review on Friday"
        - "Delete the dentist appointment"
    """
    return await execute_calendar_agent(query)


@tool
async def expense_agent_tool(query: str) -> str:
    """
    Delegate expense tracking and financial tasks to the specialized expense agent.
    
    The expense agent operates independently. Future implementation will connect
    to a dedicated expense tracking MCP server.
    
    Use this tool for:
    - Recording new expenses
    - Tracking spending by category
    - Generating expense reports
    - Analyzing spending patterns
    - Budget management advice
    - Any expense-related operations
    
    Args:
        query: The expense-related task or question from the user
        
    Returns:
        Response from the expense agent with task results
        
    Examples:
        - "Record a $50 expense for groceries"
        - "What did I spend on transportation this month?"
        - "Show me my food expenses"
        - "Help me track my monthly budget"
    """
    return await execute_expense_agent(query)


# Export tools list for easy binding to supervisor
SUB_AGENT_TOOLS = [
    mail_agent_tool,
    calendar_agent_tool,
    expense_agent_tool
]
