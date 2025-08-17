"""
Logging utilities for Alpha Design Spot project.
Provides centralized logging functions and decorators with Sentry integration.
"""

import logging
import functools
from typing import Any, Callable, Optional
from django.http import HttpRequest
import sentry_sdk
from sentry_sdk import capture_exception, capture_message, set_tag, set_context
from lib.sentry_utils import (
    sentry_context,
    tag_business_operation,
    log_authentication_event as sentry_log_auth,
    log_business_event,
    monitor_performance,
    add_custom_breadcrumb,
)


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "Unknown")


def log_api_call(
    logger_name: str = "business",
    log_level: int = logging.INFO,
    enable_sentry: bool = True,
    operation_type: str = "api_call",
):
    """
    Enhanced decorator to log API calls with request/response details and Sentry integration.

    Args:
        logger_name: Name of the logger to use
        log_level: Logging level (INFO, WARNING, ERROR)
        enable_sentry: Whether to send data to Sentry
        operation_type: Type of operation for Sentry tagging
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @tag_business_operation(operation_type) if enable_sentry else lambda f: f
        @(
            monitor_performance(f"{operation_type}_{func.__name__}")
            if enable_sentry
            else lambda f: f
        )
        def wrapper(self, request, *args, **kwargs):
            logger = logging.getLogger(logger_name)

            # Extract request details
            method = request.method
            path = request.path
            client_ip = get_client_ip(request)
            user_id = (
                getattr(request.user, "id", "Anonymous")
                if hasattr(request, "user")
                else "Unknown"
            )

            # Set Sentry context if enabled
            if enable_sentry:
                sentry_context.set_api_context(request)
                sentry_context.set_user_context(
                    request.user if hasattr(request, "user") else None
                )
                set_tag("api_function", func.__name__)
                set_tag("operation_type", operation_type)

                # Add breadcrumb for API call start
                add_custom_breadcrumb(
                    message=f"API function called: {func.__name__}",
                    category="api_function",
                    level="info",
                    data={
                        "method": method,
                        "path": path,
                        "user_id": str(user_id),
                        "function": func.__name__,
                    },
                )

            # Log request
            logger.log(
                log_level,
                f"API Call - {method} {path} - User: {user_id}, IP: {client_ip}",
            )

            try:
                # Execute the function
                response = func(self, request, *args, **kwargs)

                # Log successful response
                status_code = getattr(response, "status_code", "Unknown")
                logger.log(
                    log_level,
                    f"API Response - {method} {path} - Status: {status_code}, User: {user_id}",
                )

                # Log to Sentry if enabled
                if enable_sentry:
                    log_business_event(
                        event_type=f"{operation_type}_success",
                        module=self.__class__.__module__.split(".")[-2]
                        if hasattr(self, "__class__")
                        else "api",
                        details={
                            "function": func.__name__,
                            "method": method,
                            "path": path,
                            "status_code": status_code,
                        },
                        user_id=str(user_id) if user_id != "Anonymous" else None,
                    )

                return response

            except Exception as e:
                # Log error to traditional logging
                error_logger = logging.getLogger("api_errors")
                error_logger.error(
                    f"API Error - {method} {path} - User: {user_id}, IP: {client_ip}, Error: {str(e)}",
                    exc_info=True,
                )

                # Send to Sentry if enabled
                if enable_sentry:
                    set_context(
                        "api_error",
                        {
                            "function": func.__name__,
                            "method": method,
                            "path": path,
                            "user_id": str(user_id),
                            "client_ip": client_ip,
                            "operation_type": operation_type,
                        },
                    )
                    capture_exception(e)

                raise

        return wrapper

    return decorator


def log_model_operation(operation: str, model_name: str, logger_name: str = "business"):
    """
    Decorator to log model operations (create, update, delete).

    Args:
        operation: Type of operation (create, update, delete)
        model_name: Name of the model being operated on
        logger_name: Name of the logger to use
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)

            try:
                result = func(*args, **kwargs)

                # Extract model instance details
                instance_id = (
                    getattr(result, "id", "Unknown")
                    if hasattr(result, "id")
                    else "Unknown"
                )
                logger.info(
                    f"Model Operation - {operation.upper()} {model_name} - Instance ID: {instance_id}"
                )

                return result

            except Exception as e:
                error_logger = logging.getLogger("api_errors")
                error_logger.error(
                    f"Model Operation Error - {operation.upper()} {model_name} - Error: {str(e)}",
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def log_authentication_event(
    event_type: str,
    email: str,
    client_ip: str,
    success: bool = True,
    additional_info: Optional[dict] = None,
    enable_sentry: bool = True,
):
    """
    Enhanced authentication event logging with Sentry integration.

    Args:
        event_type: Type of auth event (login, logout, registration, password_reset)
        email: User email
        client_ip: Client IP address
        success: Whether the event was successful
        additional_info: Additional context information
        enable_sentry: Whether to send data to Sentry
    """
    auth_logger = logging.getLogger("auth")
    security_logger = logging.getLogger("security")

    log_level = logging.INFO if success else logging.WARNING
    log_message = f"Auth Event - {event_type.upper()} - Email: {email}, IP: {client_ip}, Success: {success}"

    if additional_info:
        log_message += f", Info: {additional_info}"

    auth_logger.log(log_level, log_message)

    # Enhanced Sentry logging
    if enable_sentry:
        sentry_log_auth(
            event_type=event_type,
            user_email=email,
            client_ip=client_ip,
            success=success,
            additional_data=additional_info,
        )

    # Log security events for failed attempts
    if not success:
        security_logger.warning(
            f"SECURITY_EVENT - {event_type.upper()}_FAILED - Email: {email}, IP: {client_ip}"
        )

        # Send security event to Sentry for failed attempts
        if enable_sentry:
            from lib.sentry_utils import log_security_event

            log_security_event(
                event_type=f"{event_type}_failed",
                severity="warning",
                details={
                    "email": email,
                    "event_type": event_type,
                    "additional_info": additional_info or {},
                },
                client_ip=client_ip,
            )


def log_business_operation(
    operation: str,
    details: dict,
    logger_name: str = "business",
    enable_sentry: bool = True,
    module_name: str = "business",
):
    """
    Enhanced business operation logging with Sentry integration.

    Args:
        operation: Name of the business operation
        details: Dictionary with operation details
        logger_name: Name of the logger to use
        enable_sentry: Whether to send data to Sentry
        module_name: Module name for Sentry context
    """
    logger = logging.getLogger(logger_name)
    logger.info(f"Business Operation - {operation.upper()} - Details: {details}")

    # Enhanced Sentry logging
    if enable_sentry:
        log_business_event(
            event_type=operation,
            module=module_name,
            details=details,
            user_id=details.get("user_id") if isinstance(details, dict) else None,
        )


def log_celery_task(
    task_name: str,
    task_id: str,
    status: str,
    details: Optional[dict] = None,
    enable_sentry: bool = True,
    exception: Optional[Exception] = None,
):
    """
    Enhanced Celery task logging with Sentry integration.

    Args:
        task_name: Name of the Celery task
        task_id: Task ID
        status: Task status (started, success, failure, retry)
        details: Additional task details
        enable_sentry: Whether to send data to Sentry
        exception: Exception object if task failed
    """
    celery_logger = logging.getLogger("celery")

    log_message = f"Celery Task - {task_name} - ID: {task_id}, Status: {status.upper()}"
    if details:
        log_message += f", Details: {details}"

    # Traditional logging
    if status == "failure":
        celery_logger.error(log_message)
    elif status == "retry":
        celery_logger.warning(log_message)
    else:
        celery_logger.info(log_message)

    # Enhanced Sentry logging
    if enable_sentry:
        # Set Celery task context
        set_context(
            "celery_task",
            {
                "task_name": task_name,
                "task_id": task_id,
                "status": status,
                "details": details or {},
            },
        )

        set_tag("celery_task", task_name)
        set_tag("task_status", status)
        set_tag("task_id", task_id)

        # Send appropriate message to Sentry
        if status == "failure":
            if exception:
                capture_exception(exception)
            else:
                capture_message(
                    f"Celery Task Failed: {task_name} (ID: {task_id})", level="error"
                )
        elif status == "retry":
            capture_message(
                f"Celery Task Retry: {task_name} (ID: {task_id})", level="warning"
            )
        elif status == "success":
            # Only log successful tasks if they have important details
            if details and any(
                key in str(details).lower() for key in ["error", "warning", "critical"]
            ):
                capture_message(
                    f"Celery Task Completed with Warnings: {task_name} (ID: {task_id})",
                    level="info",
                )


class SecurityLogger:
    """Security-focused logging utility class."""

    def __init__(self):
        self.logger = logging.getLogger("security")

    def log_suspicious_activity(
        self, activity_type: str, client_ip: str, details: dict
    ):
        """Log suspicious activities."""
        self.logger.warning(
            f"SUSPICIOUS_ACTIVITY - {activity_type.upper()} - IP: {client_ip}, Details: {details}"
        )

    def log_permission_denied(self, user_id: str, resource: str, client_ip: str):
        """Log permission denied events."""
        self.logger.warning(
            f"PERMISSION_DENIED - User: {user_id}, Resource: {resource}, IP: {client_ip}"
        )

    def log_rate_limit_exceeded(self, client_ip: str, endpoint: str):
        """Log rate limit violations."""
        self.logger.warning(
            f"RATE_LIMIT_EXCEEDED - IP: {client_ip}, Endpoint: {endpoint}"
        )

    def log_data_access(
        self, user_id: str, data_type: str, action: str, client_ip: str
    ):
        """Log sensitive data access."""
        self.logger.info(
            f"DATA_ACCESS - User: {user_id}, Data: {data_type}, Action: {action.upper()}, IP: {client_ip}"
        )


# Singleton instance
security_logger = SecurityLogger()
