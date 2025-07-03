"""Middleware for security and monitoring."""

import logging
import time
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from .security import rate_limiter, auth_handler, code_validator
from .models import ErrorResponse


logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Security middleware for rate limiting and authentication."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Skip middleware for health and docs endpoints
            if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
                await self.app(scope, receive, send)
                return
            
            # Rate limiting
            allowed, reason = rate_limiter.is_allowed(client_ip)
            if not allowed:
                logger.warning(f"Rate limit exceeded for {client_ip}: {reason}")
                response = JSONResponse(
                    status_code=429,
                    content=ErrorResponse(
                        error="RateLimitExceeded",
                        message=reason
                    ).model_dump()
                )
                await response(scope, receive, send)
                return
            
            # Authentication (for protected endpoints)
            if request.url.path in ["/execute-wolfram"]:
                authenticated, auth_reason = await auth_handler.authenticate(request)
                if not authenticated:
                    logger.warning(f"Authentication failed for {client_ip}: {auth_reason}")
                    response = JSONResponse(
                        status_code=401,
                        content=ErrorResponse(
                            error="Unauthorized",
                            message=auth_reason
                        ).model_dump()
                    )
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (in case of proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class LoggingMiddleware:
    """Middleware for request/response logging."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            request = Request(scope, receive)
            
            # Log request
            client_ip = self._get_client_ip(request)
            logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
            
            # Create a custom send function to capture response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    status_code = message["status"]
                    logger.info(f"Response: {status_code} in {duration:.3f}s")
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


async def validate_code_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to validate Wolfram code for security."""
    if request.url.path in ["/execute-wolfram"] and request.method == "POST":
        try:
            # Read the request body
            body = await request.body()
            if body:
                import json
                data = json.loads(body)
                code = data.get("code", "")
                
                # Validate the code
                is_safe, warnings = code_validator.validate_code(code)
                
                if not is_safe:
                    logger.warning(f"Unsafe code detected: {warnings}")
                    return JSONResponse(
                        status_code=400,
                        content=ErrorResponse(
                            error="UnsafeCode",
                            message="Code contains potentially dangerous operations",
                            details={"warnings": warnings}
                        ).model_dump()
                    )
                
                # Log warnings but allow execution
                if warnings:
                    logger.warning(f"Code warnings: {warnings}")
        
        except Exception as e:
            logger.error(f"Error in code validation middleware: {e}")
    
    response = await call_next(request)
    return response