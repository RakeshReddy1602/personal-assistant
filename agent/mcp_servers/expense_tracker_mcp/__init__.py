"""
Expense Tracker MCP - In-process expense tracking integration

This module provides tools for managing expenses through an external expense tracker API.
All tools are registered with the MCPOrchestrator for in-process execution.
"""

from . import services, tools

__all__ = ["services", "tools"]

