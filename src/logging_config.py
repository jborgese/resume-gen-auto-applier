# src/logging_config.py
"""
Centralized structlog configuration for the resume generator application.
Provides structured logging with consistent formatting and context.
"""

import structlog
import logging
import sys
import os
from typing import Any, Dict, Optional
from pathlib import Path
# Removed circular import - will import debug functions locally when needed


def configure_structlog(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    debug_mode: bool = False,
    include_timestamps: bool = True,
    include_process_info: bool = False
) -> None:
    """
    Configure structlog with consistent formatting and output options.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        debug_mode: Enable debug mode with additional context
        include_timestamps: Include timestamps in log output
        include_process_info: Include process/thread information
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
    ]
    
    # Add timestamps if requested
    if include_timestamps:
        processors.append(structlog.processors.TimeStamper(fmt="ISO"))
    
    # Add process info if requested
    if include_process_info:
        processors.append(structlog.processors.add_log_level)
        processors.append(structlog.processors.StackInfoRenderer())
    
    # Add debug context if in debug mode
    if debug_mode:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up file logging if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured structlog logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_function_call(func_name: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Create a standardized log context for function calls.
    
    Args:
        func_name: Name of the function being called
        **kwargs: Additional context to include
        
    Returns:
        Dictionary with standardized function call context
    """
    context = {
        "function": func_name,
        "event": "function_call"
    }
    context.update(kwargs)
    return context


def log_error_context(error: Exception, **kwargs: Any) -> Dict[str, Any]:
    """
    Create a standardized log context for errors.
    
    Args:
        error: The exception that occurred
        **kwargs: Additional context to include
        
    Returns:
        Dictionary with standardized error context
    """
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "event": "error"
    }
    context.update(kwargs)
    return context


def log_job_context(job_data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """
    Create a standardized log context for job-related operations.
    
    Args:
        job_data: Job information dictionary
        **kwargs: Additional context to include
        
    Returns:
        Dictionary with standardized job context
    """
    context = {
        "job_title": job_data.get("title", "Unknown"),
        "company": job_data.get("company", "Unknown"),
        "job_url": job_data.get("url", ""),
        "event": "job_operation"
    }
    context.update(kwargs)
    return context


def log_browser_context(page_url: str, action: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Create a standardized log context for browser operations.
    
    Args:
        page_url: Current page URL
        action: Browser action being performed
        **kwargs: Additional context to include
        
    Returns:
        Dictionary with standardized browser context
    """
    context = {
        "page_url": page_url,
        "browser_action": action,
        "event": "browser_operation"
    }
    context.update(kwargs)
    return context


# Initialize logging configuration based on environment
def initialize_logging() -> None:
    """Initialize logging configuration based on environment variables."""
    
    # Get configuration from environment or config
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE')
    
    # Configure structlog
    configure_structlog(
        log_level=log_level,
        log_file=log_file,
        debug_mode=debug_mode,
        include_timestamps=True,
        include_process_info=debug_mode
    )


def debug_pause(message: str, **context: Any) -> None:
    """
    Handle debug pauses for interactive debugging.
    Only pauses if DEBUG mode is enabled.
    
    Args:
        message: Debug message to log
        **context: Additional context to include in log
    """
    # Import locally to avoid circular import
    from src.debug_config import is_debug_mode, should_skip_debug_stops, get_debug_delays
    
    debug_mode = is_debug_mode()
    if debug_mode:
        logger = get_logger("debug_pause")
        logger.debug(message, **context)
        
        # Use debug delays if REDUCE_DEBUG_PAUSES is enabled
        if should_skip_debug_stops():
            debug_delays = get_debug_delays()
            pause_delay = debug_delays.get('human_behavior', 0.5)
            logger.debug(f"Debug pause reduced to {pause_delay}s (REDUCE_DEBUG_PAUSES enabled)")
            import time
            time.sleep(pause_delay)
        else:
            try:
                input("Press Enter to continue...")
            except (EOFError, KeyboardInterrupt):
                logger.debug("Continuing automatically...")


def debug_stop(message: str, **context: Any) -> None:
    """
    Comprehensive debug stop with enhanced context and options.
    Only stops if DEBUG mode is enabled.
    
    Args:
        message: Debug message to log
        **context: Additional context to include in log
    """
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    if debug_mode:
        logger = get_logger("debug_stop")
        logger.debug(f"[DEBUG STOP] {message}", **context)
        
        # Show additional context if available
        if context:
            logger.debug("Context:", **context)
        
        try:
            print("\n" + "="*60)
            print(f"[DEBUG STOP] {message}")
            print("="*60)
            if context:
                print("Context:")
                for key, value in context.items():
                    print(f"  {key}: {value}")
            print("\nOptions:")
            print("  [Enter] - Continue")
            print("  [q] - Quit program")
            print("  [s] - Skip remaining debug stops")
            print("="*60)
            
            choice = input("Choice: ").strip().lower()
            
            if choice == 'q':
                logger.debug("User chose to quit program")
                import sys
                sys.exit(0)
            elif choice == 's':
                logger.debug("User chose to skip remaining debug stops")
                os.environ['SKIP_DEBUG_STOPS'] = 'true'
            else:
                logger.debug("User chose to continue")
                
        except (EOFError, KeyboardInterrupt):
            logger.debug("Continuing automatically...")


def debug_checkpoint(checkpoint_name: str, **context: Any) -> None:
    """
    Debug checkpoint for tracking execution flow.
    Only logs if DEBUG mode is enabled.
    
    Args:
        checkpoint_name: Name of the checkpoint
        **context: Additional context to include in log
    """
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    if debug_mode:
        logger = get_logger("debug_checkpoint")
        logger.debug(f"[CHECKPOINT] {checkpoint_name}", **context)


def debug_skip_stops() -> bool:
    """
    Check if debug stops should be skipped.
    Uses debug configuration for consistent behavior.
    
    Returns:
        True if debug stops should be skipped
    """
    # Import locally to avoid circular import
    from src.debug_config import should_skip_debug_stops
    return should_skip_debug_stops()