"""Structured logging and observability utilities."""

import asyncio
import importlib
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Callable


def _load_json_logger_formatter():
    """Load python-json-logger formatter if available."""
    try:
        module = importlib.import_module("pythonjsonlogger.jsonlogger")
        return getattr(module, "JsonFormatter", None)
    except Exception:
        return None


JsonFormatter = _load_json_logger_formatter()


def setup_structured_logging(
    name: str = "llm_eaas",
    level: int = logging.INFO,
    use_json: bool = True,
) -> logging.Logger:
    """Setup structured logging with JSON output.

    Requires: pip install python-json-logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate log lines when setup is called multiple times.
    if logger.handlers:
        return logger

    logger.propagate = False

    handler = logging.StreamHandler()

    if use_json:
        if JsonFormatter is not None:
            formatter = JsonFormatter(
                "%(timestamp)s %(name)s %(levelname)s %(message)s %(duration)s",
                timestamp=True,
            )
        else:
            # Fallback if python-json-logger not installed
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class StructuredLogger:
    """Wrapper for structured logging with context."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context = {}

    def set_context(self, **kwargs):
        """Set context data for all subsequent logs."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear all context."""
        self.context.clear()

    def info(self, message: str, **kwargs):
        """Log info with context."""
        extra = {**self.context, **kwargs}
        self.logger.info(message, extra=extra)

    def error(self, message: str, **kwargs):
        """Log error with context."""
        extra = {**self.context, **kwargs}
        self.logger.error(message, exc_info=True, extra=extra)

    def warning(self, message: str, **kwargs):
        """Log warning with context."""
        extra = {**self.context, **kwargs}
        self.logger.warning(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug with context."""
        extra = {**self.context, **kwargs}
        self.logger.debug(message, extra=extra)


def log_execution_time(logger: logging.Logger):
    """Decorator to log function execution time."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.info(
                    f"Function {func.__name__} completed",
                    extra={"function": func.__name__, "duration_seconds": duration, "status": "success"},
                )
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                logger.error(
                    f"Function {func.__name__} failed",
                    exc_info=True,
                    extra={"function": func.__name__, "duration_seconds": duration, "status": "failed"},
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.info(
                    f"Function {func.__name__} completed",
                    extra={"function": func.__name__, "duration_seconds": duration, "status": "success"},
                )
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                logger.error(
                    f"Function {func.__name__} failed",
                    exc_info=True,
                    extra={"function": func.__name__, "duration_seconds": duration, "status": "failed"},
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class RequestLogger:
    """Log HTTP requests in structured format."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: str = None,
        api_key_id: str = None,
        **extra_fields,
    ):
        """Log HTTP request."""
        log_data = {
            "event": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_seconds": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if user_id:
            log_data["user_id"] = user_id
        if api_key_id:
            log_data["api_key_id"] = api_key_id

        log_data.update(extra_fields)

        self.logger.info(json.dumps(log_data))


@asynccontextmanager
async def log_context(logger: logging.Logger, context_name: str, **context_data):
    """Context manager for logging a specific operation."""
    start_time = time.perf_counter()
    logger.info(
        f"Starting {context_name}",
        extra={"context": context_name, **context_data},
    )

    try:
        yield
    except Exception:
        duration = time.perf_counter() - start_time
        logger.error(
            f"Failed in {context_name}",
            exc_info=True,
            extra={
                "context": context_name,
                "duration_seconds": duration,
                "status": "failed",
                **context_data,
            },
        )
        raise
    else:
        duration = time.perf_counter() - start_time
        logger.info(
            f"Completed {context_name}",
            extra={
                "context": context_name,
                "duration_seconds": duration,
                "status": "success",
                **context_data,
            },
        )
