"""
Enhanced error handling utilities for Local AI Assistant
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..config import settings

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Enhanced error handler with detailed logging and user-friendly messages"""
    
    @staticmethod
    def log_error(error: Exception, context: str = "", request: Request = None) -> str:
        """Log error with context information"""
        error_id = f"ERR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        log_data = {
            "error_id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request:
            log_data.update({
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            })
        
        # Log stack trace for debugging
        if settings.log_level.upper() == "DEBUG":
            log_data["stack_trace"] = traceback.format_exc()
        
        logger.error(f"Application error: {log_data}")
        return error_id
    
    @staticmethod
    def create_error_response(
        error: Exception,
        status_code: int = 500,
        user_message: str = None,
        context: str = "",
        request: Request = None
    ) -> JSONResponse:
        """Create standardized error response"""
        error_id = ErrorHandler.log_error(error, context, request)
        
        # Determine user-friendly message
        if user_message:
            message = user_message
        else:
            message = ErrorHandler.get_user_friendly_message(error, status_code)
        
        response_data = {
            "error": message,
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code
        }
        
        # Add debug information in development
        if settings.log_level.upper() == "DEBUG":
            response_data["debug"] = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def get_user_friendly_message(error: Exception, status_code: int) -> str:
        """Get user-friendly error message based on error type"""
        error_messages = {
            # Database errors
            "sqlite3.OperationalError": "Database operation failed. Please try again.",
            "sqlalchemy.exc.OperationalError": "Database is temporarily unavailable.",
            "sqlalchemy.exc.IntegrityError": "Data validation error. Please check your input.",
            
            # Network/API errors
            "httpx.ConnectError": "Cannot connect to AI service. Please ensure Ollama is running.",
            "httpx.TimeoutException": "Request timed out. The AI service may be busy.",
            "httpx.HTTPStatusError": "AI service returned an error. Please try again.",
            
            # Validation errors
            "pydantic.ValidationError": "Invalid input data. Please check your request.",
            "ValueError": "Invalid value provided. Please check your input.",
            "TypeError": "Invalid data type. Please check your input.",
            
            # File system errors
            "FileNotFoundError": "Required file not found. Please check the configuration.",
            "PermissionError": "Permission denied. Please check file permissions.",
            "OSError": "System error occurred. Please try again.",
            
            # JSON errors
            "json.JSONDecodeError": "Invalid data format. Please check your input.",
            
            # HTTP errors
            "HTTPException": str(error) if isinstance(error, HTTPException) else "Request failed."
        }
        
        error_type = type(error).__name__
        
        if error_type in error_messages:
            return error_messages[error_type]
        
        # Status code specific messages
        status_messages = {
            400: "Bad request. Please check your input.",
            401: "Authentication required.",
            403: "Access forbidden.",
            404: "Resource not found.",
            422: "Invalid input data.",
            429: "Too many requests. Please try again later.",
            500: "Internal server error. Please try again.",
            502: "Service unavailable. Please try again later.",
            503: "AI service is currently unavailable.",
            504: "Request timeout. Please try again."
        }
        
        return status_messages.get(status_code, "An unexpected error occurred.")


class APIException(Exception):
    """Custom API exception with enhanced error information"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = None,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"API_ERROR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class OllamaConnectionError(APIException):
    """Exception for Ollama connection issues"""
    
    def __init__(self, message: str = "Cannot connect to Ollama service", details: Dict = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="OLLAMA_CONNECTION_ERROR",
            details=details or {}
        )


class ModelNotFoundError(APIException):
    """Exception for missing AI models"""
    
    def __init__(self, model_name: str = "", details: Dict = None):
        message = f"AI model '{model_name}' not found" if model_name else "AI model not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="MODEL_NOT_FOUND",
            details=details or {}
        )


class ConversationNotFoundError(APIException):
    """Exception for missing conversations"""
    
    def __init__(self, conversation_id: str = "", details: Dict = None):
        message = f"Conversation '{conversation_id}' not found" if conversation_id else "Conversation not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="CONVERSATION_NOT_FOUND",
            details=details or {}
        )


class DatabaseError(APIException):
    """Exception for database operations"""
    
    def __init__(self, message: str = "Database operation failed", details: Dict = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details or {}
        )


class ValidationError(APIException):
    """Exception for input validation"""
    
    def __init__(self, message: str = "Input validation failed", details: Dict = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )


# Error handling decorators
def handle_database_errors(func):
    """Decorator to handle database errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            if any(db_error in error_type for db_error in ['sqlite3', 'sqlalchemy', 'database']):
                raise DatabaseError(f"Database operation failed: {str(e)}")
            raise
    return wrapper


def handle_ollama_errors(func):
    """Decorator to handle Ollama service errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            if 'httpx' in error_type.lower() or 'connect' in error_type.lower():
                raise OllamaConnectionError(f"Ollama service error: {str(e)}")
            raise
    return wrapper


def safe_execute(operation_name: str = "Operation"):
    """Decorator for safe execution with error logging"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{operation_name} failed: {str(e)}")
                raise
        return wrapper
    return decorator


# Utility functions
def is_network_error(error: Exception) -> bool:
    """Check if error is network-related"""
    network_errors = ['ConnectError', 'TimeoutException', 'HTTPStatusError', 'ConnectionError']
    error_type = type(error).__name__
    return any(net_error in error_type for net_error in network_errors)


def is_validation_error(error: Exception) -> bool:
    """Check if error is validation-related"""
    validation_errors = ['ValidationError', 'ValueError', 'TypeError', 'JSONDecodeError']
    error_type = type(error).__name__
    return any(val_error in error_type for val_error in validation_errors)


def sanitize_error_message(message: str) -> str:
    """Sanitize error message for safe display"""
    # Remove sensitive information patterns
    sensitive_patterns = [
        r'password=\S+',
        r'token=\S+',
        r'key=\S+',
        r'secret=\S+'
    ]
    
    import re
    sanitized = message
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def get_error_context(request: Request = None) -> Dict[str, Any]:
    """Get contextual information for error logging"""
    context = {
        "timestamp": datetime.utcnow().isoformat(),
        "app_version": settings.app_version
    }
    
    if request:
        context.update({
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown"
        })
    
    return context