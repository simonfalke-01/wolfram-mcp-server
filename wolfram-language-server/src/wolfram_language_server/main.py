"""Main FastAPI application for Wolfram Language Server."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .models import (
    WolframRequest, WolframResponse, HealthResponse, ErrorResponse,
    EvaluateRequest, EvaluateResponse
)
from .wolfram_client import WolframExecutor
from . import __version__


# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global Wolfram executor
wolfram_executor: WolframExecutor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global wolfram_executor

    # Startup
    logger.info("Starting Wolfram Language Server")
    kernel_path = os.getenv("WOLFRAM_KERNEL_PATH")
    wolfram_executor = WolframExecutor(kernel_path=kernel_path)

    try:
        # Test Wolfram availability
        available, error = await wolfram_executor.is_available()
        if available:
            logger.info("Wolfram Language is available")
        else:
            logger.warning(f"Wolfram Language not available: {error}")
    except Exception as e:
        logger.error(f"Failed to initialize Wolfram executor: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Wolfram Language Server")
    if wolfram_executor:
        await wolfram_executor.stop_session()


app = FastAPI(
    title="Wolfram Language Server",
    description="Backend API for executing Wolfram Language scripts",
    version=__version__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred"
        ).model_dump()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global wolfram_executor

    wolfram_available = False
    kernel_info = None

    if wolfram_executor:
        try:
            wolfram_available, _ = await wolfram_executor.is_available()
            if wolfram_available:
                kernel_info = await wolfram_executor.get_kernel_info()
        except Exception as e:
            logger.error(f"Health check error: {e}")

    return HealthResponse(
        status="healthy",
        version=__version__,
        wolfram_available=wolfram_available,
        kernel_info=kernel_info
    )


@app.post("/execute", response_model=WolframResponse)
async def execute_wolfram_code(request: WolframRequest):
    """Execute Wolfram Language code."""
    global wolfram_executor

    if not wolfram_executor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wolfram executor not initialized"
        )

    # Check if Wolfram is available
    available, error = await wolfram_executor.is_available()
    if not available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Wolfram Language not available: {error}"
        )

    try:
        # Execute the code
        success, result, error_msg, execution_time = await wolfram_executor.execute_code(
            request.code,
            request.timeout or 30
        )

        # Format the result
        formatted_result = None
        output = None

        if success and result is not None:
            if request.format == "json":
                try:
                    formatted_result = wolfram_executor._format_result(result, "json")
                except Exception:
                    output = str(result)
            else:
                output = str(result)

        return WolframResponse(
            success=success,
            result=formatted_result,
            output=output,
            error=error_msg,
            execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"Code execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_expression(request: EvaluateRequest):
    """Evaluate a simple Wolfram Language expression."""
    global wolfram_executor

    if not wolfram_executor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wolfram executor not initialized"
        )

    # Check if Wolfram is available
    available, error = await wolfram_executor.is_available()
    if not available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Wolfram Language not available: {error}"
        )

    try:
        # Evaluate the expression
        success, result, error_msg, execution_time = await wolfram_executor.evaluate_expression(
            request.expression,
            request.timeout or 10
        )

        # Try to convert result to a JSON-serializable format
        formatted_result = None
        if success and result is not None:
            try:
                if isinstance(result, (int, float, str, bool, list, dict)):
                    formatted_result = result
                else:
                    formatted_result = str(result)
            except Exception:
                formatted_result = str(result)

        return EvaluateResponse(
            success=success,
            result=formatted_result,
            error=error_msg,
            execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"Expression evaluation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Wolfram Language Server",
        "version": __version__,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "execute": "/execute",
            "evaluate": "/evaluate",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wolfram_language_server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
