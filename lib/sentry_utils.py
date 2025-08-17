"""
Sentry utilities for Alpha Design Spot project.
Provides custom context managers, tagging functions, and performance monitoring.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, Union
from contextlib import contextmanager

import sentry_sdk
from sentry_sdk import (
    capture_exception,
    capture_message,
    set_tag,
    set_context,
    add_breadcrumb,
)
from django.conf import settings
from django.http import HttpRequest


class SentryContextManager:
    """
    Context manager for adding custom Sentry context and tags.
    """

    def __init__(self):
        self.original_user = None
        self.original_tags = {}
        self.original_contexts = {}

    def set_user_context(self, user):
        """Set user context for Sentry events."""
        if user and hasattr(user, "id"):
            sentry_sdk.set_user(
                {
                    "id": str(user.id),
                    "email": getattr(user, "email", None),
                    "username": getattr(user, "username", None),
                    "is_staff": getattr(user, "is_staff", False),
                    "is_superuser": getattr(user, "is_superuser", False),
                }
            )

    def set_business_context(self, operation: str, details: Dict[str, Any]):
        """Set business operation context."""
        set_context(
            "business_operation",
            {"operation": operation, "details": details, "timestamp": time.time()},
        )

    def set_api_context(self, request: HttpRequest):
        """Set API request context."""
        set_context(
            "api_request",
            {
                "method": request.method,
                "path": request.path,
                "query_params": dict(request.GET) if request.GET else None,
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "client_ip": self._get_client_ip(request),
            },
        )

    def set_module_context(
        self, module_name: str, action: str, details: Optional[Dict] = None
    ):
        """Set application module context."""
        set_context(
            "app_module",
            {"module": module_name, "action": action, "details": details or {}},
        )

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "Unknown")


def tag_business_operation(operation_type: str):
    """Decorator to tag Sentry events with business operation type."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            set_tag("business_operation", operation_type)
            set_tag("function_name", func.__name__)

            # Add breadcrumb for function entry
            add_breadcrumb(
                message=f"Entering {func.__name__}",
                category="business_operation",
                level="info",
                data={"operation_type": operation_type},
            )

            try:
                result = func(*args, **kwargs)

                # Add success breadcrumb
                add_breadcrumb(
                    message=f"Successfully completed {func.__name__}",
                    category="business_operation",
                    level="info",
                )

                return result

            except Exception as e:
                # Add error breadcrumb
                add_breadcrumb(
                    message=f"Error in {func.__name__}: {str(e)}",
                    category="business_operation",
                    level="error",
                )

                # Add custom tags for error
                set_tag("error_in_operation", operation_type)
                set_tag("error_function", func.__name__)

                raise

        return wrapper

    return decorator


def monitor_performance(operation_name: str, threshold_ms: int = 1000):
    """
    Decorator to monitor function performance and send to Sentry.

    Args:
        operation_name: Name of the operation for tracking
        threshold_ms: Threshold in milliseconds to log slow operations
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Start Sentry transaction
            with sentry_sdk.start_transaction(
                op="function", name=f"{operation_name}.{func.__name__}"
            ) as transaction:
                try:
                    # Add performance context
                    set_context(
                        "performance_monitoring",
                        {
                            "operation": operation_name,
                            "function": func.__name__,
                            "threshold_ms": threshold_ms,
                        },
                    )

                    result = func(*args, **kwargs)

                    # Calculate execution time
                    execution_time = (time.time() - start_time) * 1000  # Convert to ms

                    # Set transaction data
                    transaction.set_data("execution_time_ms", execution_time)
                    transaction.set_tag("operation_name", operation_name)

                    # Log slow operations
                    if execution_time > threshold_ms:
                        capture_message(
                            f"Slow operation detected: {operation_name}.{func.__name__} took {execution_time:.2f}ms",
                            level="warning",
                        )

                        set_tag("slow_operation", True)
                        set_tag("execution_time_ms", int(execution_time))

                    return result

                except Exception as e:
                    # Calculate execution time even for errors
                    execution_time = (time.time() - start_time) * 1000

                    # Set error context
                    transaction.set_data("execution_time_ms", execution_time)
                    transaction.set_data("error", str(e))
                    transaction.set_status("internal_error")

                    set_tag("operation_error", operation_name)
                    set_tag("execution_time_ms", int(execution_time))

                    raise

        return wrapper

    return decorator


@contextmanager
def sentry_transaction_context(operation: str, name: str, **tags):
    """
    Context manager for Sentry transactions with custom tags.

    Args:
        operation: Type of operation (e.g., 'auth', 'api', 'task')
        name: Specific name of the transaction
        **tags: Additional tags to add to the transaction
    """
    with sentry_sdk.start_transaction(op=operation, name=name) as transaction:
        # Add custom tags
        for key, value in tags.items():
            transaction.set_tag(key, value)

        try:
            yield transaction
        except Exception as e:
            transaction.set_status("internal_error")
            transaction.set_data("error", str(e))
            capture_exception(e)
            raise


def log_security_event(
    event_type: str,
    severity: str,
    details: Dict[str, Any],
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
):
    """
    Log security events to Sentry with proper context.

    Args:
        event_type: Type of security event (e.g., 'failed_login', 'permission_denied')
        severity: Severity level ('info', 'warning', 'error')
        details: Additional details about the security event
        user_id: User ID if available
        client_ip: Client IP address if available
    """
    # Set security context
    set_context(
        "security_event",
        {
            "event_type": event_type,
            "details": details,
            "timestamp": time.time(),
            "client_ip": client_ip,
            "user_id": user_id,
        },
    )

    # Set security tags
    set_tag("security_event", event_type)
    set_tag("severity", severity)
    if client_ip:
        set_tag("client_ip", client_ip)
    if user_id:
        set_tag("affected_user", user_id)

    # Send to Sentry
    capture_message(f"Security Event: {event_type} - {details}", level=severity)


def log_authentication_event(
    event_type: str,
    user_email: str,
    client_ip: str,
    success: bool,
    additional_data: Optional[Dict] = None,
):
    """
    Log authentication events to Sentry.

    Args:
        event_type: Type of auth event ('login', 'logout', 'registration', 'password_reset')
        user_email: Email of the user
        client_ip: Client IP address
        success: Whether the event was successful
        additional_data: Additional context data
    """
    context_data = {
        "event_type": event_type,
        "user_email": user_email,
        "client_ip": client_ip,
        "success": success,
        "timestamp": time.time(),
    }

    if additional_data:
        context_data.update(additional_data)

    set_context("authentication", context_data)

    # Set tags
    set_tag("auth_event", event_type)
    set_tag("auth_success", success)
    set_tag("client_ip", client_ip)

    # Log based on success/failure
    if success:
        capture_message(
            f"Authentication Success: {event_type} for {user_email}", level="info"
        )
    else:
        capture_message(
            f"Authentication Failure: {event_type} for {user_email} from {client_ip}",
            level="warning",
        )


def log_business_event(
    event_type: str, module: str, details: Dict[str, Any], user_id: Optional[str] = None
):
    """
    Log business events to Sentry.

    Args:
        event_type: Type of business event (e.g., 'post_created', 'user_registered')
        module: Application module (e.g., 'account', 'post', 'master')
        details: Event details
        user_id: User ID if available
    """
    set_context(
        "business_event",
        {
            "event_type": event_type,
            "module": module,
            "details": details,
            "user_id": user_id,
            "timestamp": time.time(),
        },
    )

    set_tag("business_event", event_type)
    set_tag("app_module", module)
    if user_id:
        set_tag("user_id", user_id)

    capture_message(
        f"Business Event: {event_type} in {module} - {details}", level="info"
    )


def capture_custom_exception(
    exception: Exception,
    context: Optional[Dict] = None,
    tags: Optional[Dict] = None,
    user: Optional[Any] = None,
):
    """
    Capture exception with custom context and tags.

    Args:
        exception: Exception to capture
        context: Additional context data
        tags: Additional tags
        user: User object for context
    """
    # Set user context if provided
    if user:
        sentry_context = SentryContextManager()
        sentry_context.set_user_context(user)

    # Set additional context
    if context:
        set_context("custom_error_context", context)

    # Set additional tags
    if tags:
        for key, value in tags.items():
            set_tag(key, value)

    # Capture the exception
    capture_exception(exception)


def add_custom_breadcrumb(
    message: str, category: str, level: str = "info", data: Optional[Dict] = None
):
    """
    Add custom breadcrumb to Sentry.

    Args:
        message: Breadcrumb message
        category: Category of the breadcrumb
        level: Level ('debug', 'info', 'warning', 'error')
        data: Additional data
    """
    add_breadcrumb(message=message, category=category, level=level, data=data or {})


# Singleton instances for global use
sentry_context = SentryContextManager()
