"""Improved Wolfram Language client with better session management and performance."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wlexpr
from wolframclient.language import wl


logger = logging.getLogger(__name__)


class ImprovedWolframLanguageClient:
    """Improved Wolfram Language client with optimized session management."""

    def __init__(self, kernel_path: Optional[str] = None):
        """Initialize the Wolfram Language client.

        Args:
            kernel_path: Path to Wolfram kernel executable (optional)
        """
        self.kernel_path = kernel_path
        self._session: Optional[WolframLanguageSession] = None
        self._session_lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="wolfram")
        self._session_initialized = False
        self._last_activity = time.time()

        # Session keep-alive settings
        self.session_timeout = 300  # 5 minutes of inactivity before closing
        self.max_retries = 3

        logger.info(f"Wolfram client initialized with kernel_path: {kernel_path}")

    async def _run_in_executor(self, func, *args):
        """Run a function in the thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    async def _ensure_session(self) -> bool:
        """Ensure we have a working session, with retry logic."""
        async with self._session_lock:
            # Check if we need to create or recreate the session
            if self._session is None or not self._session_initialized:
                logger.info("Creating new Wolfram session...")

                for attempt in range(self.max_retries):
                    try:
                        start_time = time.time()

                        # Create session
                        if self.kernel_path:
                            self._session = WolframLanguageSession(kernel=self.kernel_path)
                            logger.info(f"Using kernel path: {self.kernel_path}")
                        else:
                            self._session = WolframLanguageSession()
                            logger.info("Using default kernel")

                        # Test the session with a simple evaluation
                        test_result = await self._run_in_executor(
                            lambda: self._session.evaluate(wl.Plus(1, 1))
                        )

                        creation_time = time.time() - start_time
                        logger.info(f"Session created successfully in {creation_time:.3f}s, test result: {test_result}")

                        # Additional initialization to warm up the session
                        await self._run_in_executor(
                            lambda: self._session.evaluate(wlexpr("$Version"))
                        )

                        self._session_initialized = True
                        self._last_activity = time.time()
                        return True

                    except Exception as e:
                        logger.error(f"Session creation attempt {attempt + 1} failed: {e}")
                        if self._session:
                            try:
                                await self._run_in_executor(self._session.terminate)
                            except:
                                pass
                            self._session = None

                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            logger.error("All session creation attempts failed")
                            return False
            else:
                # Session exists, check if it's still alive
                try:
                    await self._run_in_executor(
                        lambda: self._session.evaluate(wl.Plus(1, 1))
                    )
                    self._last_activity = time.time()
                    return True
                except Exception as e:
                    logger.warning(f"Session health check failed: {e}, recreating session")
                    self._session = None
                    self._session_initialized = False
                    return await self._ensure_session()  # Recursive call to recreate

        return False

    async def execute_wolfram_code(self, code: str, timeout: int = 30) -> Tuple[bool, Any, Optional[str], float]:
        """Execute Wolfram Language code using wlexpr (strict syntax).

        Args:
            code: Wolfram Language code to execute (strict syntax)
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (success, result, error_message, execution_time)
        """
        logger.info(f"Executing Wolfram code: {code[:100]}...")
        start_time = time.time()

        try:
            # Ensure we have a working session
            if not await self._ensure_session():
                return False, None, "Failed to establish Wolfram session", 0.0

            # Parse and execute the code
            def execute():
                parsed_code = wlexpr(code)
                return self._session.evaluate(parsed_code)

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self._run_in_executor(execute),
                    timeout=timeout
                )

                execution_time = time.time() - start_time
                logger.info(f"Execution completed in {execution_time:.3f}s")

                return True, result, None, execution_time

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.error(f"Execution timed out after {timeout}s")
                return False, None, f"Execution timed out after {timeout} seconds", execution_time

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Execution failed: {e}")
            return False, None, str(e), execution_time


    async def is_available(self) -> Tuple[bool, Optional[str]]:
        """Check if Wolfram Engine is available.

        Returns:
            Tuple of (available, error_message)
        """
        try:
            if await self._ensure_session():
                return True, None
            else:
                return False, "Failed to create Wolfram session"
        except Exception as e:
            return False, str(e)

    async def stop_session(self) -> None:
        """Stop the Wolfram session (alias for close)."""
        await self.close()

    async def get_kernel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the Wolfram Kernel.

        Returns:
            Dictionary with kernel information or None if unavailable
        """
        try:
            if not await self._ensure_session():
                return None

            version = await self._run_in_executor(
                lambda: self._session.evaluate(wlexpr("$Version"))
            )
            system_id = await self._run_in_executor(
                lambda: self._session.evaluate(wlexpr("$SystemID"))
            )

            return {
                "version": str(version) if version else "Unknown",
                "system_id": str(system_id) if system_id else "Unknown",
                "session_active": True
            }
        except Exception as e:
            logger.error(f"Failed to get kernel info: {e}")
            return None

    async def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        info = {
            "session_active": self._session is not None and self._session_initialized,
            "last_activity": self._last_activity,
            "kernel_path": self.kernel_path,
            "session_age": time.time() - self._last_activity if self._session_initialized else None
        }

        if self._session and self._session_initialized:
            try:
                version = await self._run_in_executor(
                    lambda: self._session.evaluate(wlexpr("$Version"))
                )
                info["version"] = str(version)
            except Exception as e:
                info["version_error"] = str(e)

        return info

    async def close(self) -> None:
        """Close the Wolfram session and cleanup resources."""
        async with self._session_lock:
            if self._session:
                try:
                    await self._run_in_executor(self._session.terminate)
                    logger.info("Wolfram session terminated")
                except Exception as e:
                    logger.warning(f"Error terminating session: {e}")
                finally:
                    self._session = None
                    self._session_initialized = False

        # Shutdown the executor
        self._executor.shutdown(wait=True)
        logger.info("Wolfram client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
