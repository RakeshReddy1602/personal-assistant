from typing import Any, Dict, Optional

from agent.mcp_servers.expense_tracker_mcp import services as expense_services


def add_expense(
    amount: float,
    description: str,
    email: str,
    expense_date: Optional[str] = None
) -> Dict[str, Any]:
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
        result = expense_services.add_expense(
            amount=amount,
            description=description,
            email=email,
            expense_date=expense_date
        )
        return result
    except Exception as e:
        return {"error": f"Failed to add expense: {str(e)}"}


def update_expense(
    expense_id: int,
    amount: Optional[float] = None,
    description: Optional[str] = None,
    email: Optional[str] = None,
    expense_date: Optional[str] = None
) -> Dict[str, Any]:
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
        result = expense_services.update_expense(
            expense_id=expense_id,
            amount=amount,
            description=description,
            email=email,
            expense_date=expense_date
        )
        return result
    except Exception as e:
        return {"error": f"Failed to update expense: {str(e)}"}


def get_expense_by_id(expense_id: int) -> Dict[str, Any]:
    """
    Get a specific expense by ID.
    
    Args:
        expense_id: The ID of the expense to retrieve
    
    Returns:
        dict: The expense data
    """
    try:
        result = expense_services.get_expense_by_id(expense_id=expense_id)
        return result
    except Exception as e:
        return {"error": f"Failed to get expense: {str(e)}"}


def get_expenses(
    email: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
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
        result = expense_services.get_expenses(
            email=email,
            start_time=start_time,
            end_time=end_time
        )
        return result
    except Exception as e:
        return {"error": f"Failed to get expenses: {str(e)}"}


def get_expenses_by_time_range(
    email: str,
    start_time: str,
    end_time: str
) -> Dict[str, Any]:
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
        result = expense_services.get_expenses_by_time_range(
            email=email,
            start_time=start_time,
            end_time=end_time
        )
        return result
    except Exception as e:
        return {"error": f"Failed to get expenses by time range: {str(e)}"}


def delete_expense(expense_id: int) -> Dict[str, Any]:
    """
    Delete an expense by ID.
    
    Args:
        expense_id: The ID of the expense to delete
    
    Returns:
        dict: Confirmation message
    """
    try:
        result = expense_services.delete_expense(expense_id=expense_id)
        return result
    except Exception as e:
        return {"error": f"Failed to delete expense: {str(e)}"}


def check_api_health() -> Dict[str, Any]:
    """
    Check the health status of the expense tracker API.
    
    Returns:
        dict: API health status
    """
    try:
        result = expense_services.check_api_health()
        return result
    except Exception as e:
        return {"error": f"Failed to check API health: {str(e)}"}


def search_expenses_by_description(
    email: str,
    description: str,
    limit: Optional[int] = None
) -> Dict[str, Any]:
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
        result = expense_services.search_expenses_by_description(
            email=email,
            description=description,
            limit=limit
        )
        return result
    except Exception as e:
        return {"error": f"Failed to search expenses: {str(e)}"}


def get_api_info() -> Dict[str, Any]:
    """
    Get API information and available endpoints.
    
    Returns:
        dict: API information and available endpoints
    """
    try:
        result = expense_services.get_api_info()
        return result
    except Exception as e:
        return {"error": f"Failed to get API info: {str(e)}"}

