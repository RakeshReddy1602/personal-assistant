"""Pydantic models for API"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class EvalResultCreate(BaseModel):
    """Model for creating an eval result"""
    test_name: str = Field(..., description="Name of the test")
    category: str = Field(..., description="Test category (router, mail, calendar, etc.)")
    status: str = Field(..., description="Status: passed, failed, error, skipped")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Score between 0 and 1")
    execution_time_ms: float = Field(default=0.0, ge=0.0, description="Execution time in milliseconds")
    user_input: Optional[str] = Field(None, description="User input/query")
    agent_output: Optional[str] = Field(None, description="Agent output/response")
    justification: Optional[str] = Field(None, description="Gemini's justification for the evaluation")
    improvements: Optional[str] = Field(None, description="Gemini's suggested improvements")
    error_message: Optional[str] = Field(None, description="Error message if any")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EvalResultResponse(BaseModel):
    """Model for eval result response"""
    id: int
    test_name: str
    category: str
    status: str
    score: float
    execution_time_ms: float
    user_input: Optional[str]
    agent_output: Optional[str]
    justification: Optional[str]
    improvements: Optional[str]
    error_message: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

