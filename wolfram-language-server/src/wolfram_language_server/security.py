"""Security utilities and middleware for the Wolfram Language Server."""

import logging
import re
import time
from typing import Dict, List, Set
from collections import defaultdict, deque

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param


logger = logging.getLogger(__name__)


class CodeValidator:
    """Validates Wolfram Language code for security risks."""
    
    # Dangerous functions that should be restricted
    DANGEROUS_FUNCTIONS = {
        "Run", "RunProcess", "Import", "Export", "Get", "Put", "OpenRead", "OpenWrite",
        "CreateFile", "DeleteFile", "CopyFile", "RenameFile", "CreateDirectory", 
        "DeleteDirectory", "SetDirectory", "ResetDirectory", "Install", "Uninstall",
        "URLFetch", "URLRead", "URLSubmit", "SendMail", "SystemOpen", "NotebookWrite",
        "CloudDeploy", "CloudFunction", "CloudObject", "RemoteFile", "RemoteRun"
    }
    
    # File system and network related patterns
    RISKY_PATTERNS = [
        r'!/.*',  # Shell commands
        r'Import\[.*\]',
        r'Export\[.*\]',
        r'Get\[.*\]',
        r'Put\[.*\]',
        r'Run\[.*\]',
        r'URLFetch\[.*\]',
        r'SetDirectory\[.*\]',
        r'CreateFile\[.*\]',
        r'DeleteFile\[.*\]'
    ]
    
    def __init__(self, strict_mode: bool = True):
        """Initialize the code validator.
        
        Args:
            strict_mode: If True, apply strict security rules
        """
        self.strict_mode = strict_mode
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.RISKY_PATTERNS]
    
    def validate_code(self, code: str) -> tuple[bool, List[str]]:
        """Validate Wolfram Language code for security risks.
        
        Args:
            code: The code to validate
            
        Returns:
            Tuple of (is_safe, list_of_warnings)
        """
        warnings = []
        
        # Check for dangerous functions
        for func in self.DANGEROUS_FUNCTIONS:
            if func in code:
                if self.strict_mode:
                    warnings.append(f"Dangerous function detected: {func}")
                else:
                    logger.warning(f"Potentially dangerous function used: {func}")
        
        # Check for risky patterns
        for pattern in self.compiled_patterns:
            if pattern.search(code):
                warnings.append(f"Risky pattern detected: {pattern.pattern}")
        
        # Check code length (prevent extremely long code)
        if len(code) > 50000:  # 50KB limit
            warnings.append("Code too long (>50KB)")
        
        # Check for obvious attempts to break out
        dangerous_keywords = ["System`", "Developer`", "Internal`"]
        for keyword in dangerous_keywords:
            if keyword in code:
                warnings.append(f"Restricted namespace access: {keyword}")
        
        is_safe = len(warnings) == 0 or not self.strict_mode
        return is_safe, warnings


class RateLimiter:
    """Rate limiter to prevent abuse."""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP
            burst_size: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.burst_counts: Dict[str, int] = defaultdict(int)
        self.last_reset: Dict[str, float] = defaultdict(float)
    
    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """Check if request is allowed for the given IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        minute_ago = current_time - 60
        while self.requests[client_ip] and self.requests[client_ip][0] < minute_ago:
            self.requests[client_ip].popleft()
        
        # Reset burst counter every minute
        if current_time - self.last_reset[client_ip] > 60:
            self.burst_counts[client_ip] = 0
            self.last_reset[client_ip] = current_time
        
        # Check burst limit
        if self.burst_counts[client_ip] >= self.burst_size:
            return False, f"Burst limit exceeded ({self.burst_size} requests)"
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False, f"Rate limit exceeded ({self.requests_per_minute} requests/minute)"
        
        # Allow the request
        self.requests[client_ip].append(current_time)
        self.burst_counts[client_ip] += 1
        
        return True, "OK"


class AuthenticationHandler:
    """Handle API authentication."""
    
    def __init__(self, api_key: str = None):
        """Initialize authentication handler.
        
        Args:
            api_key: Optional API key for authentication
        """
        self.api_key = api_key
        self.bearer_scheme = HTTPBearer(auto_error=False)
    
    async def authenticate(self, request: Request) -> tuple[bool, str]:
        """Authenticate a request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Tuple of (is_authenticated, reason)
        """
        if not self.api_key:
            # No authentication required
            return True, "No authentication required"
        
        authorization = request.headers.get("Authorization")
        if not authorization:
            return False, "Missing Authorization header"
        
        scheme, credentials = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return False, "Invalid authentication scheme"
        
        if credentials != self.api_key:
            return False, "Invalid API key"
        
        return True, "Authenticated"


# Global instances
code_validator = CodeValidator(strict_mode=True)
rate_limiter = RateLimiter(requests_per_minute=30, burst_size=5)
auth_handler = AuthenticationHandler()