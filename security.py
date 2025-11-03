"""
Security module for input validation and sanitization.
Implements comprehensive security controls to prevent command injection and other attacks.
"""

import re
import html
import json
import time
import threading
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from flask import request, jsonify
from collections import defaultdict
from datetime import datetime, timedelta


# Configuration constants
MAX_STRING_LENGTH = 10000
MAX_TEXT_LENGTH = 100000
MAX_INTEGER_VALUE = 1000000
MIN_INTEGER_VALUE = -1000000
MAX_FLOAT_VALUE = 1e10
MIN_FLOAT_VALUE = -1e10
MAX_ARRAY_LENGTH = 1000
MAX_OBJECT_DEPTH = 10

# Dangerous patterns that could indicate injection attempts
# Using re.IGNORECASE in checks to prevent case-based bypasses
DANGEROUS_PATTERNS = [
    r'[;&|`$(){}]',  # Shell metacharacters and braces
    r'\.\.[/\\]',    # Path traversal
    r'<script\b',    # XSS attempts - matches <script but not <scripts
    r'javascript:',  # XSS
    r'on\w+\s*=',  # Event handlers
    r'eval\s*\(',  # Code evaluation
    r'exec\s*\(',  # Code execution
    r'import\s+os',  # OS module import
    r'__import__',  # Dynamic imports
    r'subprocess',  # Subprocess execution
]

# Rate limiting storage
# Note: For production use with multiple workers, consider using Redis or memcached
# This in-memory storage is suitable for single-worker development/testing
rate_limit_storage = defaultdict(list)
rate_limit_lock = threading.Lock()


class ValidationError(Exception):
    """
    Custom exception for validation errors.
    
    This exception is safe to expose to users as it only contains
    controlled error messages from validation logic, never stack traces
    or internal system information.
    """
    
    def __str__(self):
        """Return only the error message, never stack trace."""
        # Only return the first argument (the message), never stack trace
        return self.args[0] if self.args else "Validation failed"


class SecurityValidator:
    """Handles input validation and sanitization."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
        """
        Sanitize a string input by removing dangerous characters.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        if len(value) > max_length:
            raise ValidationError(f"String too long: {len(value)} > {max_length}")
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"Potentially dangerous pattern detected: {pattern}")
        
        # HTML escape to prevent XSS
        sanitized = html.escape(value)
        
        return sanitized
    
    @staticmethod
    def validate_integer(value: Any, minimum: int = MIN_INTEGER_VALUE, 
                        maximum: int = MAX_INTEGER_VALUE) -> int:
        """
        Validate and convert to integer with bounds checking.
        
        Args:
            value: Value to validate
            minimum: Minimum allowed value
            maximum: Maximum allowed value
            
        Returns:
            Validated integer
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if isinstance(value, bool):
                raise ValidationError("Boolean cannot be converted to integer")
            
            int_value = int(value)
            
            if int_value < minimum:
                raise ValidationError(f"Integer too small: {int_value} < {minimum}")
            if int_value > maximum:
                raise ValidationError(f"Integer too large: {int_value} > {maximum}")
            
            return int_value
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid integer value: {value}") from e
    
    @staticmethod
    def validate_number(value: Any, minimum: float = MIN_FLOAT_VALUE,
                       maximum: float = MAX_FLOAT_VALUE) -> float:
        """
        Validate and convert to float with bounds checking.
        
        Args:
            value: Value to validate
            minimum: Minimum allowed value
            maximum: Maximum allowed value
            
        Returns:
            Validated float
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if isinstance(value, bool):
                raise ValidationError("Boolean cannot be converted to number")
            
            float_value = float(value)
            
            # Check for NaN and infinity
            if float_value != float_value:  # NaN check
                raise ValidationError("NaN is not allowed")
            if float_value == float('inf') or float_value == float('-inf'):
                raise ValidationError("Infinity is not allowed")
            
            if float_value < minimum:
                raise ValidationError(f"Number too small: {float_value} < {minimum}")
            if float_value > maximum:
                raise ValidationError(f"Number too large: {float_value} > {maximum}")
            
            return float_value
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid number value: {value}") from e
    
    @staticmethod
    def validate_enum(value: str, allowed_values: List[str]) -> str:
        """
        Validate that a string is one of the allowed values.
        
        Args:
            value: Value to validate
            allowed_values: List of allowed values
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string for enum, got {type(value).__name__}")
        
        if value not in allowed_values:
            raise ValidationError(
                f"Invalid value '{value}'. Must be one of: {', '.join(allowed_values)}"
            )
        
        return value
    
    @staticmethod
    def validate_object_depth(obj: Any, max_depth: int = MAX_OBJECT_DEPTH,
                             current_depth: int = 0) -> None:
        """
        Validate that an object doesn't exceed maximum nesting depth.
        
        Args:
            obj: Object to validate
            max_depth: Maximum allowed depth
            current_depth: Current depth level
            
        Raises:
            ValidationError: If validation fails
        """
        if current_depth > max_depth:
            raise ValidationError(f"Object nesting too deep: {current_depth} > {max_depth}")
        
        if isinstance(obj, dict):
            for value in obj.values():
                SecurityValidator.validate_object_depth(value, max_depth, current_depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                SecurityValidator.validate_object_depth(item, max_depth, current_depth + 1)
    
    @staticmethod
    def validate_json_size(json_str: str, max_size: int = 1024 * 1024) -> None:
        """
        Validate JSON payload size.
        
        Args:
            json_str: JSON string to validate
            max_size: Maximum size in bytes
            
        Raises:
            ValidationError: If validation fails
        """
        size = len(json_str.encode('utf-8'))
        if size > max_size:
            raise ValidationError(f"JSON payload too large: {size} > {max_size}")
    
    @staticmethod
    def validate_tool_name(tool_name: str) -> str:
        """
        Validate tool name against whitelist pattern.
        
        Args:
            tool_name: Tool name to validate
            
        Returns:
            Validated tool name
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(tool_name, str):
            raise ValidationError("Tool name must be a string")
        
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', tool_name):
            raise ValidationError(
                "Tool name must start with letter or underscore and contain only "
                "alphanumeric characters and underscores"
            )
        
        if len(tool_name) > 100:
            raise ValidationError("Tool name too long")
        
        return tool_name


class RateLimiter:
    """Simple rate limiter to prevent abuse."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit.
        Thread-safe implementation using locks.
        
        Args:
            identifier: Unique identifier for the client
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Use lock for thread-safe access to shared storage
        with rate_limit_lock:
            # Clean old requests
            rate_limit_storage[identifier] = [
                timestamp for timestamp in rate_limit_storage[identifier]
                if timestamp > cutoff
            ]
            
            # Check if limit exceeded
            if len(rate_limit_storage[identifier]) >= self.max_requests:
                return False
            
            # Add current request
            rate_limit_storage[identifier].append(now)
            return True


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    limiter = RateLimiter(max_requests, window_seconds)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as identifier
            identifier = request.remote_addr or 'unknown'
            
            if not limiter.is_allowed(identifier):
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later."
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_request_json():
    """
    Decorator to validate that request has valid JSON.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "Invalid JSON payload"}), 400
                
                # Validate object depth
                SecurityValidator.validate_object_depth(data)
                
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON format"}), 400
            except ValidationError as e:
                # ValidationError messages are safe - they're our controlled messages
                # The ValidationError class is designed to only contain safe validation
                # messages, never stack traces or internal system information.
                # lgtm[py/stack-trace-exposure] - ValidationError only contains safe validation messages
                error_msg = str(e) if str(e) else "Request validation failed"
                return jsonify({"error": error_msg}), 400
            except Exception:
                # Don't expose internal exception details
                return jsonify({"error": "Request validation failed"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def add_security_headers(response):
    """
    Add security headers to response.
    
    Note: CSP currently allows 'unsafe-inline' for backward compatibility with
    existing inline scripts/styles in the HTML template. For production use,
    consider refactoring inline scripts to external files or using CSP nonces.
    
    Args:
        response: Flask response object
        
    Returns:
        Response with security headers
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Note: 'unsafe-inline' is used here for compatibility with the template
    # For enhanced security, refactor inline scripts/styles and use nonces
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:;"
    )
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
