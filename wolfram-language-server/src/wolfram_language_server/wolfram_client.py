"""Wolfram Language client using wolframclient library."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple, Union
from pathlib import Path

from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl
from wolframclient.exception import WolframKernelException


logger = logging.getLogger(__name__)


class WolframExecutor:
    """Handles Wolfram Language code execution."""

    def __init__(self, kernel_path: Optional[str] = None):
        """Initialize the Wolfram executor.

        Args:
            kernel_path: Optional path to Wolfram Kernel executable
        """
        self.kernel_path = kernel_path
        self._session: Optional[WolframLanguageSession] = None
        self._session_lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_session()

    async def start_session(self) -> None:
        """Start a Wolfram Language session."""
        async with self._session_lock:
            if self._session is None:
                try:
                    if self.kernel_path:
                        self._session = WolframLanguageSession(kernel=self.kernel_path)
                        logger.info(f"Kernel path provided: {self.kernel_path}")
                    else:
                        self._session = WolframLanguageSession()

                    # Test the session with a simple evaluation
                    await self._run_in_executor(lambda: self._session.evaluate(wl.Plus(1, 1)))
                    logger.info("Wolfram Language session started successfully")
                except Exception as e:
                    logger.error(f"Failed to start Wolfram session: {e}")
                    self._session = None
                    raise

    async def stop_session(self) -> None:
        """Stop the Wolfram Language session."""
        async with self._session_lock:
            if self._session:
                try:
                    await self._run_in_executor(self._session.terminate)
                    logger.info("Wolfram Language session terminated")
                except Exception as e:
                    logger.warning(f"Error terminating Wolfram session: {e}")
                finally:
                    self._session = None

    async def _run_in_executor(self, func, *args):
        """Run a blocking function in an executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def is_available(self) -> Tuple[bool, Optional[str]]:
        """Check if Wolfram Language is available.

        Returns:
            Tuple of (available, error_message)
        """
        try:
            if self._session is None:
                await self.start_session()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_kernel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the Wolfram Kernel.

        Returns:
            Dictionary with kernel information or None if unavailable
        """
        try:
            if self._session is None:
                await self.start_session()

            if self._session:
                # Get basic kernel information
                version = await self._run_in_executor(
                    lambda: self._session.evaluate(wl.SystemInformation("Kernel"))
                )
                return {
                    "version": str(version) if version else "Unknown",
                    "session_active": True
                }
        except Exception as e:
            logger.error(f"Failed to get kernel info: {e}")

        return None

    async def execute_code(self, code: str, timeout: int = 30) -> Tuple[bool, Any, Optional[str], float]:
        """Execute Wolfram Language code.

        Args:
            code: Wolfram Language code to execute
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (success, result, error_message, execution_time)
        """
        if self._session is None:
            await self.start_session()

        if self._session is None:
            return False, None, "Wolfram session not available", 0.0

        start_time = time.time()

        try:
            # Set timeout for the evaluation
            async with asyncio.timeout(timeout):
                result = await self._run_in_executor(
                    lambda: self._session.evaluate(code)
                )

            execution_time = time.time() - start_time

            # Check if result indicates an error
            if hasattr(result, 'head') and str(result.head) == '$Failed':
                return False, None, "Evaluation failed", execution_time

            return True, result, None, execution_time

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return False, None, f"Execution timed out after {timeout} seconds", execution_time
        except WolframKernelException as e:
            execution_time = time.time() - start_time
            return False, None, f"Wolfram kernel error: {str(e)}", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, None, f"Execution error: {str(e)}", execution_time

    async def evaluate_expression(self, expression: str, timeout: int = 10) -> Tuple[bool, Any, Optional[str], float]:
        """Evaluate a simple Wolfram Language expression.

        Args:
            expression: Wolfram Language expression to evaluate
            timeout: Evaluation timeout in seconds

        Returns:
            Tuple of (success, result, error_message, execution_time)
        """
        return await self.execute_code(expression, timeout)

    def _format_result(self, result: Any, format_type: str = "text") -> Any:
        """Format the result based on the requested format.

        Args:
            result: The raw result from Wolfram
            format_type: Format type ('text', 'json', 'image')

        Returns:
            Formatted result
        """
        if result is None:
            return None

        if format_type == "text":
            return str(result)
        elif format_type == "json":
            # Try to convert to a JSON-serializable format
            try:
                if hasattr(result, 'to_dict'):
                    return result.to_dict()
                elif isinstance(result, (int, float, str, bool, list, dict)):
                    return result
                else:
                    return str(result)
            except Exception:
                return str(result)
        elif format_type == "image":
            # Handle image results - this would need additional logic
            # for now, just return as string
            return str(result)
        else:
            return str(result)
