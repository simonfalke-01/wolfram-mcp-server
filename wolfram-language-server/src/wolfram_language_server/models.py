"""Pydantic models for the Wolfram Language Server API."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class WolframRequest(BaseModel):
    """Request model for Wolfram Language execution."""
    
    code: str = Field(..., description="Wolfram Language code to execute")
    timeout: Optional[int] = Field(30, description="Execution timeout in seconds", ge=1, le=300)
    format: Optional[str] = Field("text", description="Output format: 'text', 'json', 'image'")
    kernel_path: Optional[str] = Field(None, description="Path to Wolfram Kernel (optional)")


class WolframResponse(BaseModel):
    """Response model for Wolfram Language execution."""
    
    success: bool = Field(..., description="Whether execution was successful")
    result: Optional[Any] = Field(None, description="Execution result")
    output: Optional[str] = Field(None, description="Text output from execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    warnings: Optional[List[str]] = Field(None, description="Any warnings from execution")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    wolfram_available: bool = Field(..., description="Whether Wolfram Engine is available")
    kernel_info: Optional[Dict[str, Any]] = Field(None, description="Wolfram Kernel information")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class EvaluateRequest(BaseModel):
    """Request model for simple expression evaluation."""
    
    expression: str = Field(..., description="Wolfram Language expression to evaluate")
    timeout: Optional[int] = Field(10, description="Evaluation timeout in seconds", ge=1, le=60)


class EvaluateResponse(BaseModel):
    """Response model for simple expression evaluation."""
    
    success: bool = Field(..., description="Whether evaluation was successful")
    result: Optional[Union[str, int, float, bool, List, Dict]] = Field(None, description="Evaluation result")
    error: Optional[str] = Field(None, description="Error message if evaluation failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")


class ExecuteWolframRequest(BaseModel):
    """Request model for Wolfram Language execution using wlexpr."""
    
    code: str = Field(..., description="Wolfram Language code to execute (strict syntax)")
    timeout: Optional[int] = Field(30, description="Execution timeout in seconds", ge=1, le=300)


