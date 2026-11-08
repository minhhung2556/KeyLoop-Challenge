import logging
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def sanitize_error_message(error: Exception, default_message: str = "An error occurred") -> str:
    """Sanitize error messages to prevent information disclosure"""
    error_type = type(error).__name__
    error_str = str(error)
    
    sensitive_patterns = [
        "password",
        "secret",
        "key",
        "token",
        "credential",
        "file path",
        "traceback",
        "stack",
        "firebase",
        "database",
        "sql",
        "connection",
    ]
    
    error_lower = error_str.lower()
    for pattern in sensitive_patterns:
        if pattern in error_lower:
            logger.error(f"Error contains sensitive information: {error_type}")
            return default_message
    
    if error_type in ["ValueError", "TypeError", "AttributeError"]:
        return error_str if len(error_str) < 100 else default_message
    
    return default_message


def create_safe_http_exception(
    status_code: int,
    detail: str,
    original_error: Optional[Exception] = None,
    log_error: bool = True
) -> HTTPException:
    """Create HTTPException with sanitized error message"""
    if original_error and log_error:
        logger.error(
            f"HTTP {status_code}: {detail}",
            exc_info=original_error,
            extra={"error_type": type(original_error).__name__}
        )
    
    return HTTPException(status_code=status_code, detail=detail)

