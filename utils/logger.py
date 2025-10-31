"""
Logging Configuration
=====================

Structured logging for MCP Agent Memory operations.

Logs are written to: ~/.shared_memory_mcp/mcp_memory.log

Log levels:
- DEBUG: Detailed operation information
- INFO: Important events (tool calls, operations)
- WARNING: Non-critical issues (truncation, retries)
- ERROR: Error conditions requiring attention

Log format includes:
- Timestamp (ISO 8601)
- Log level
- Component/module name
- Message
- Additional context (agent_name, entry_id, etc.)
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import json


# Log file location
LOG_FILE = Path.home() / ".shared_memory_mcp" / "mcp_memory.log"

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "shared_memory_mcp",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure and return a logger for the MCP server.

    Args:
        name (str): Logger name (default: "shared_memory_mcp")
        level (int): Logging level (default: INFO)
        log_file (Path): Path to log file (default: ~/.shared_memory_mcp/mcp_memory.log)
        max_bytes (int): Maximum log file size before rotation (default: 10MB)
        backup_count (int): Number of backup files to keep (default: 5)

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> logger = setup_logger()
        >>> logger.info("Server started")
        >>> logger.error("Failed to read file", extra={"file": "memory.json"})
    """
    # Use default log file if not specified
    if log_file is None:
        log_file = LOG_FILE

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    return logger


class StructuredLogger:
    """
    Wrapper around standard logger that adds structured logging capabilities.

    Provides methods for logging common MCP operations with consistent formatting
    and automatic context injection.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize structured logger.

        Args:
            logger (Optional[logging.Logger]): Logger to wrap. If None, creates default.
        """
        self.logger = logger or setup_logger()

    def _format_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Format message with optional context."""
        if context:
            context_str = " | " + " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message}{context_str}"
        return message

    def debug(self, message: str, **context):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message, context))

    def info(self, message: str, **context):
        """Log info message with context."""
        self.logger.info(self._format_message(message, context))

    def warning(self, message: str, **context):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message, context))

    def error(self, message: str, exc_info: bool = False, **context):
        """Log error message with context and optional exception info."""
        self.logger.error(self._format_message(message, context), exc_info=exc_info)

    # Operation-specific logging methods

    def log_add_memory(
        self,
        agent_name: str,
        word_count: int,
        entry_number: int,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log memory addition operation."""
        context = {
            "operation": "add_memory",
            "agent": agent_name,
            "words": word_count,
            "entry_num": entry_number
        }

        if success:
            self.info(f"Memory entry added", **context)
        else:
            context["error"] = error
            self.error(f"Failed to add memory entry", **context)

    def log_read_memory(
        self,
        format: str,
        entry_count: int,
        agent_filter: Optional[str] = None,
        limit: Optional[int] = None,
        truncated: bool = False
    ):
        """Log memory read operation."""
        context = {
            "operation": "read_memory",
            "format": format,
            "entries": entry_count
        }

        if agent_filter:
            context["filter"] = agent_filter
        if limit:
            context["limit"] = limit
        if truncated:
            context["truncated"] = True

        if truncated:
            self.warning(f"Memory read truncated", **context)
        else:
            self.info(f"Memory read", **context)

    def log_clear_memory(self, entries_cleared: int, success: bool = True):
        """Log memory clear operation."""
        context = {
            "operation": "clear_memory",
            "entries_cleared": entries_cleared
        }

        if success:
            self.info(f"Memory cleared", **context)
        else:
            self.error(f"Failed to clear memory", **context)

    def log_update_memory(
        self,
        entry_id: str,
        agent_name: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log memory update operation."""
        context = {
            "operation": "update_memory",
            "entry_id": entry_id,
            "agent": agent_name
        }

        if success:
            self.info(f"Memory entry updated", **context)
        else:
            context["error"] = error
            self.error(f"Failed to update memory entry", **context)

    def log_delete_memory(
        self,
        entry_id: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log memory delete operation."""
        context = {
            "operation": "delete_memory",
            "entry_id": entry_id
        }

        if success:
            self.info(f"Memory entry deleted", **context)
        else:
            context["error"] = error
            self.error(f"Failed to delete memory entry", **context)

    def log_search_memory(
        self,
        query: str,
        results_count: int,
        search_time_ms: Optional[float] = None
    ):
        """Log memory search operation."""
        context = {
            "operation": "search_memory",
            "query": query[:50],  # Truncate long queries
            "results": results_count
        }

        if search_time_ms:
            context["time_ms"] = round(search_time_ms, 2)

        self.info(f"Memory search completed", **context)

    def log_lock_acquired(self, file_path: str, wait_time_ms: float):
        """Log successful file lock acquisition."""
        context = {
            "operation": "file_lock",
            "file": file_path,
            "wait_ms": round(wait_time_ms, 2)
        }
        self.debug(f"File lock acquired", **context)

    def log_lock_timeout(self, file_path: str, timeout_s: float):
        """Log file lock timeout."""
        context = {
            "operation": "file_lock",
            "file": file_path,
            "timeout_s": timeout_s
        }
        self.error(f"File lock timeout", **context)

    def log_storage_corruption(self, file_path: str, error: str):
        """Log storage corruption detected."""
        context = {
            "operation": "storage",
            "file": file_path,
            "error": error
        }
        self.error(f"Storage corruption detected", **context)

    def log_storage_recovered(self, file_path: str, backup_used: bool = False):
        """Log storage recovery."""
        context = {
            "operation": "storage",
            "file": file_path,
            "backup_used": backup_used
        }
        self.info(f"Storage recovered", **context)


# Singleton logger instance
_default_logger: Optional[StructuredLogger] = None


def get_logger() -> StructuredLogger:
    """
    Get the default structured logger instance (singleton).

    Returns:
        StructuredLogger: Default logger instance

    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger()
        >>> logger.info("Operation completed")
    """
    global _default_logger

    if _default_logger is None:
        _default_logger = StructuredLogger(setup_logger())

    return _default_logger


def set_log_level(level: int):
    """
    Set the logging level for the default logger.

    Args:
        level (int): Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> import logging
        >>> from utils.logger import set_log_level
        >>> set_log_level(logging.DEBUG)
    """
    logger = get_logger()
    logger.logger.setLevel(level)
    for handler in logger.logger.handlers:
        handler.setLevel(level)
