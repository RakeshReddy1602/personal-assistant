"""
Expense Tracker MCP Server

A FastMCP server that exposes expense tracking tools via HTTP.
Run this server separately, and the orchestrator will connect to it.
"""

from fastmcp import FastMCP
from typing import Optional
from agent.mcp_servers.expense_tracker_mcp import services

# Initialize FastMCP server
mcp = FastMCP('Expense Tracker Server')


@mcp.tool(description="Add a new expense to the expense tracker.")
def add_expense(
    amount: float,
    description: str,
    email: str,
    expense_date: Optional[str] = None
) -> dict:
    """
    Add a new expense to the expense tracker.
    
    Args:
        amount: The expense amount (must be positive)
        description: Description of the expense
        email: User's email address
        expense_date: Expense date in ISO 8601 format (optional, defaults to current date)
    
    Returns:
        dict: The created expense data
    """
    try:
        return services.add_expense(amount, description, email, expense_date)
    except Exception as e:
        return {"error": f"Failed to add expense: {str(e)}"}


@mcp.tool(description="Update an existing expense by ID.")
def update_expense(
    expense_id: int,
    amount: Optional[float] = None,
    description: Optional[str] = None,
    email: Optional[str] = None,
    expense_date: Optional[str] = None
) -> dict:
    """
    Update an existing expense by ID.
    
    Args:
        expense_id: The ID of the expense to update
        amount: New expense amount (optional)
        description: New description (optional)
        email: New email address (optional)
        expense_date: New expense date in ISO 8601 format (optional)
    
    Returns:
        dict: The updated expense data
    """
    try:
        return services.update_expense(expense_id, amount, description, email, expense_date)
    except Exception as e:
        return {"error": f"Failed to update expense: {str(e)}"}


@mcp.tool(description="Get a specific expense by ID.")
def get_expense_by_id(expense_id: int) -> dict:
    """
    Get a specific expense by ID.
    
    Args:
        expense_id: The ID of the expense to retrieve
    
    Returns:
        dict: The expense data
    """
    try:
        return services.get_expense_by_id(expense_id)
    except Exception as e:
        return {"error": f"Failed to get expense: {str(e)}"}


@mcp.tool(description="Get all expenses for a user with optional filtering.")
def get_expenses(
    email: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> dict:
    """
    Get all expenses for a user with optional filtering.
    
    Args:
        email: User's email address (required)
        start_time: Start date for filtering in ISO 8601 format (optional)
        end_time: End date for filtering in ISO 8601 format (optional)
    
    Returns:
        dict: List of expenses matching the criteria
    """
    try:
        return services.get_expenses(email, start_time, end_time)
    except Exception as e:
        return {"error": f"Failed to get expenses: {str(e)}"}


@mcp.tool(description="Get expenses within a specific time range.")
def get_expenses_by_time_range(
    email: str,
    start_time: str,
    end_time: str
) -> dict:
    """
    Get expenses within a specific time range.
    
    Args:
        email: User's email address
        start_time: Start date in ISO 8601 format
        end_time: End date in ISO 8601 format
    
    Returns:
        dict: List of expenses within the time range
    """
    try:
        return services.get_expenses_by_time_range(email, start_time, end_time)
    except Exception as e:
        return {"error": f"Failed to get expenses by time range: {str(e)}"}


@mcp.tool(description="Delete an expense by ID.")
def delete_expense(expense_id: int) -> dict:
    """
    Delete an expense by ID.
    
    Args:
        expense_id: The ID of the expense to delete
    
    Returns:
        dict: Confirmation message
    """
    try:
        return services.delete_expense(expense_id)
    except Exception as e:
        return {"error": f"Failed to delete expense: {str(e)}"}


@mcp.tool(description="Check the health status of the expense tracker API.")
def check_api_health() -> dict:
    """
    Check the health status of the expense tracker API.
    
    Returns:
        dict: API health status
    """
    try:
        return services.check_api_health()
    except Exception as e:
        return {"error": f"Failed to check API health: {str(e)}"}


@mcp.tool(description="Search for expenses by description.")
def search_expenses_by_description(
    email: str,
    description: str,
    limit: Optional[int] = None
) -> dict:
    """
    Search for expenses by description.
    
    Args:
        email: Email address of the user
        description: Description to search for (partial matches supported)
        limit: Maximum number of results to return (default: 50, max: 100)
    
    Returns:
        dict: List of matching expenses with search metadata
    """
    try:
        return services.search_expenses_by_description(email, description, limit)
    except Exception as e:
        return {"error": f"Failed to search expenses: {str(e)}"}


@mcp.tool(description="Get API information and available endpoints.")
def get_api_info() -> dict:
    """
    Get API information and available endpoints.
    
    Returns:
        dict: API information and available endpoints
    """
    try:
        return services.get_api_info()
    except Exception as e:
        return {"error": f"Failed to get API info: {str(e)}"}


# Run the server when this file is executed directly
if __name__ == "__main__":
    print("Starting Expense Tracker MCP Server on http://127.0.0.1:6280/mcp")
    mcp.run(transport="http", host="127.0.0.1", port=6280, stateless_http=True)

