import requests
from datetime import datetime
from typing import Any, Dict, Optional

# Base URL for the expense tracker API
API_BASE_URL = "http://localhost:3000"


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
    # Use current date if not provided
    if not expense_date:
        expense_date = datetime.now().isoformat() + "Z"
    
    payload = {
        "amount": amount,
        "description": description,
        "email": email,
        "expenseDate": expense_date
    }
    
    response = requests.post(f"{API_BASE_URL}/expenses", json=payload)
    response.raise_for_status()
    
    return response.json()


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
    payload = {}
    if amount is not None:
        payload["amount"] = amount
    if description is not None:
        payload["description"] = description
    if email is not None:
        payload["email"] = email
    if expense_date is not None:
        payload["expenseDate"] = expense_date
    
    response = requests.put(f"{API_BASE_URL}/expenses/{expense_id}", json=payload)
    response.raise_for_status()
    
    return response.json()


def get_expense_by_id(expense_id: int) -> Dict[str, Any]:
    """
    Get a specific expense by ID.
    
    Args:
        expense_id: The ID of the expense to retrieve
    
    Returns:
        dict: The expense data
    """
    response = requests.get(f"{API_BASE_URL}/expenses/{expense_id}")
    response.raise_for_status()
    
    return response.json()


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
    params = {"email": email}
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    
    response = requests.get(f"{API_BASE_URL}/expenses", params=params)
    response.raise_for_status()
    
    return response.json()


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
    params = {
        "email": email,
        "startTime": start_time,
        "endTime": end_time
    }
    
    response = requests.get(f"{API_BASE_URL}/expenses/time-range", params=params)
    response.raise_for_status()
    
    return response.json()


def delete_expense(expense_id: int) -> Dict[str, Any]:
    """
    Delete an expense by ID.
    
    Args:
        expense_id: The ID of the expense to delete
    
    Returns:
        dict: Confirmation message
    """
    response = requests.delete(f"{API_BASE_URL}/expenses/{expense_id}")
    response.raise_for_status()
    
    return response.json()


def check_api_health() -> Dict[str, Any]:
    """
    Check the health status of the expense tracker API.
    
    Returns:
        dict: API health status
    """
    response = requests.get(f"{API_BASE_URL}/health")
    response.raise_for_status()
    
    return response.json()


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
    params = {
        "email": email,
        "description": description
    }
    
    if limit is not None:
        params["limit"] = limit
    
    response = requests.get(f"{API_BASE_URL}/expenses/search", params=params)
    response.raise_for_status()
    
    return response.json()


def get_api_info() -> Dict[str, Any]:
    """
    Get API information and available endpoints.
    
    Returns:
        dict: API information and available endpoints
    """
    response = requests.get(f"{API_BASE_URL}/")
    response.raise_for_status()
    
    return response.json()

